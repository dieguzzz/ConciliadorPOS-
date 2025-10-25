from fastapi import APIRouter, UploadFile, File, Form 
from fastapi.responses import StreamingResponse
from datetime import datetime 
from io import BytesIO

import pandas as pd
import numpy as np
import io, traceback, re
import tempfile

router = APIRouter()

# ========= FUNCIONES AUXILIARES =========

def _cell_to_rc(cell: str):
    """Convierte 'E8' -> (row_idx, col_idx) 0-based."""
    cell = cell.strip().upper()
    m = re.fullmatch(r"([A-Z]+)(\d+)", cell)
    if not m:
        raise ValueError(f"Celda inválida: {cell}")
    col_letters, row_num = m.group(1), int(m.group(2))
    col_idx = 0
    for ch in col_letters:
        col_idx = col_idx * 26 + (ord(ch) - ord('A') + 1)
    col_idx -= 1
    return row_num - 1, col_idx


def _get(df_raw: pd.DataFrame, cell: str):
    r, c = _cell_to_rc(cell)
    if r < 0 or c < 0 or r >= df_raw.shape[0] or c >= df_raw.shape[1]:
        return None
    v = df_raw.iat[r, c]
    return None if (isinstance(v, float) and pd.isna(v)) else v


def _right_of(df_raw: pd.DataFrame, cell: str, max_steps=6):
    """Devuelve el primer valor no vacío a la derecha de 'cell'."""
    r, c = _cell_to_rc(cell)
    for k in range(1, max_steps + 1):
        if c + k < df_raw.shape[1]:
            v = df_raw.iat[r, c + k]
            if not (isinstance(v, float) and pd.isna(v)) and str(v).strip() != "":
                return v
    return None


def _below(df_raw: pd.DataFrame, cell: str, max_steps=6):
    """Devuelve el primer valor no vacío debajo de 'cell'."""
    r, c = _cell_to_rc(cell)
    for k in range(1, max_steps + 1):
        if r + k < df_raw.shape[0]:
            v = df_raw.iat[r + k, c]
            if not (isinstance(v, float) and pd.isna(v)) and str(v).strip() != "":
                return v
    return None


def _to_float(v):
    if v is None:
        return np.nan
    s = str(v).strip().lower()
    s = s.replace("b/.", "").replace("b/ ", "").replace("$", "").replace(",", "")
    try:
        return float(s)
    except:
        m = re.search(r"[-+]?\d*\.?\d+", s)
        return float(m.group(0)) if m else np.nan


# ========= PARSER CIERRE =========

def parse_cierre_blackdog_posicional(df_raw: pd.DataFrame):
    """Lee el cierre por coordenadas (según layout Black Dog)."""
    df_str = df_raw.astype(str).fillna("")
    banner = " ".join(df_str.iloc[:12, :].values.flatten()).upper()
    if "CIERRE DE PUNTO DE VENTA" not in banner:
        return None

    cajero = _below(df_raw, "E8") or _below(df_raw, "F8") or _below(df_raw, "G8")
    fecha_v = _below(df_raw, "I8") or _below(df_raw, "J8") or _below(df_raw, "K8") or _below(df_raw, "L8")
    suc_v = _below(df_raw, "N8") or _below(df_raw, "O8") or _below(df_raw, "P8") or _below(df_raw, "Q8")

    fecha = None
    fecha_str_original = None
    
    if fecha_v is not None:
        print(f"📅 Valor crudo de fecha: '{fecha_v}' (tipo: {type(fecha_v)})")
        
        # 🔥 Si es Timestamp, necesitamos RE-INTERPRETAR como DD/MM/YYYY
        if isinstance(fecha_v, pd.Timestamp):
            # Excel guardó 11/09/2025 pero pandas lo interpretó como 2025-11-09
            # Necesitamos extraer día y mes correctamente
            # Convertir a string ISO y luego intercambiar día/mes
            fecha_iso = fecha_v.strftime("%Y-%m-%d")  # "2025-11-09"
            year, month, day = fecha_iso.split("-")
            
            # 🔥 INTERCAMBIAR: lo que pandas pensó que era mes, es realmente el día
            fecha_str_original = f"{month}/{day}/{year}"  # "11/09/2025"
            
            try:
                dt = datetime.strptime(fecha_str_original, "%d/%m/%Y")
                fecha = dt.date()
                print(f"✅ Fecha cierre (Timestamp corregido): '{fecha_v}' → '{fecha_str_original}' → {fecha}")
            except Exception as e:
                print(f"❌ Error corrigiendo timestamp: {e}")
                # Fallback: usar el timestamp tal cual
                fecha = fecha_v.date()
                fecha_str_original = fecha_v.strftime("%d/%m/%Y")
                
        elif isinstance(fecha_v, datetime):
            # Mismo tratamiento que Timestamp
            fecha_iso = fecha_v.strftime("%Y-%m-%d")
            year, month, day = fecha_iso.split("-")
            fecha_str_original = f"{month}/{day}/{year}"
            
            try:
                dt = datetime.strptime(fecha_str_original, "%d/%m/%Y")
                fecha = dt.date()
                print(f"✅ Fecha cierre (datetime corregido): '{fecha_v}' → '{fecha_str_original}' → {fecha}")
            except Exception as e:
                print(f"❌ Error corrigiendo datetime: {e}")
                fecha = fecha_v.date()
                fecha_str_original = fecha_v.strftime("%d/%m/%Y")
                
        else:
            # Si viene como string, parsear directamente
            s = str(fecha_v).strip()
            match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s)
            if match:
                day, month, year = match.groups()
                try:
                    dt = datetime(int(year), int(month), int(day))
                    fecha = dt.date()
                    fecha_str_original = s
                    print(f"✅ Fecha cierre parseada: '{s}' (DD/MM/YYYY) → {fecha}")
                except Exception as e:
                    print(f"❌ Error parseando fecha: {e}")

    sucursal = (str(suc_v).strip().upper() if suc_v else "DESCONOCIDA")

    def _leer_bloque(col_titulo, col_monto, fila_ini, fila_fin, col_total):
        items = []
        for f in range(fila_ini, fila_fin):
            nombre = _get(df_raw, f"{col_titulo}{f}")
            monto = _get(df_raw, f"{col_monto}{f}")
            if str(nombre).strip().upper() == "TOTAL":
                break
            if nombre and str(nombre).strip() != "" and monto not in (None, "", np.nan):
                val = _to_float(monto)
                if not np.isnan(val):
                    items.append({"nombre": str(nombre).strip(), "monto": f"B/. {val:.2f}"})
        total_val = _get(df_raw, f"{col_total}{fila_fin}")
        total_val_f = _to_float(total_val)
        total_fmt = f"B/. {total_val_f:.2f}" if pd.notna(total_val_f) else None
        return items, total_fmt

    detalle_yappy, total_yappy = _leer_bloque("I", "J", 15, 37, "K")
    detalle_ach, total_ach = _leer_bloque("N", "O", 15, 26, "O")
    detalle_pedidosya, total_pedya = _leer_bloque("Q", "R", 15, 37, "R")

    lecturas = [
        ("EFECTIVO", "A13", "Derecha"), ("FONDO DE CAJA", "A14", "Derecha"),
        ("DEBITO (CLAVE)", "A16", "Derecha"), ("CREDITO (VISA/MASTER)", "A17", "Derecha"),
        ("TOTAL CON PEYA", "A20", "Derecha"), ("TOTAL SIN PEYA", "A21", "Derecha"),
        ("TOTAL DE INGRESO", "A24", "Derecha"), ("CIERRE DEL SISTEMA", "A25", "Derecha"),
        ("DIFERENCIA", "A26", "Derecha"), ("A DEPOSITAR EN EFECTIVO", "A28", "Derecha"),
    ]

    totales = {}
    for nombre, celda, modo in lecturas:
        val = _right_of(df_raw, celda, max_steps=6) if modo == "Derecha" else _below(df_raw, celda, max_steps=6)
        totales[nombre] = round(float(_to_float(val)), 2) if pd.notna(_to_float(val)) else np.nan

    if total_yappy: totales["YAPPY"] = _to_float(total_yappy)
    if total_ach: totales["ACH"] = _to_float(total_ach)
    if total_pedya: totales["PEDIDOS YA"] = _to_float(total_pedya)

    orígenes = ["EFECTIVO", "YAPPY", "DEBITO (CLAVE)", "CREDITO (VISA/MASTER)",
                "ACH", "PEDIDOS YA", "TOTAL DE INGRESO", "CIERRE DEL SISTEMA", "DIFERENCIA"]

    data_rows = []
    for o in orígenes:
        monto = totales.get(o, np.nan)
        if pd.notna(monto):
            data_rows.append({
                "fecha": fecha_str_original if fecha_str_original else str(fecha) if fecha else None,
                "sucursal": sucursal, "origen": o, "monto": monto
            })

    df_tabla = pd.DataFrame(data_rows)
    
    meta = {
        "fecha": fecha_str_original if fecha_str_original else str(fecha) if fecha else None,
        "sucursal": sucursal,
        "cajero": (str(cajero).strip() if cajero else None)
    }

    return {
        "meta": meta, "totales": totales, "tabla": df_tabla,
        "detalle_yappy": detalle_yappy, "detalle_ach": detalle_ach,
        "detalle_pedidosya": detalle_pedidosya
    }


# ========= PARSER YAPPY =========

def parse_yappy_blackdog(df_raw: pd.DataFrame, fecha_cierre_str: str = None):
    """Parser específico para Yappy de Black Dog."""
    cols = {"fecha": 1, "referencia": 6, "cliente": 9, "celular": 12, "estado": 14, "total": 22}

    start_row = None
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x).strip().upper() for x in row if pd.notna(x))
        if "FECHA" in row_str and "REFERENCIA" in row_str:
            start_row = i + 1
            break

    if start_row is None:
        raise ValueError("❌ No se encontró la fila de encabezados en Yappy")

    df_data = df_raw.iloc[start_row:].reset_index(drop=True)
    df_yappy = pd.DataFrame({
        "fecha": df_data.iloc[:, cols["fecha"]],
        "referencia": df_data.iloc[:, cols["referencia"]],
        "cliente": df_data.iloc[:, cols["cliente"]],
        "celular": df_data.iloc[:, cols["celular"]],
        "estado": df_data.iloc[:, cols["estado"]],
        "total": df_data.iloc[:, cols["total"]],
    })

    def clean_fecha(v):
        if pd.isna(v): return None
        s = str(v).strip()
        s = re.sub(r'^(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)\.?\s+', '', s, flags=re.IGNORECASE).strip()
        try:
            dt = datetime.strptime(s, '%d/%m/%Y')
            return dt.strftime("%Y-%m-%d")
        except:
            return None

    df_yappy["fecha"] = df_yappy["fecha"].apply(clean_fecha)

    def clean_monto(v):
        if pd.isna(v): return 0.0
        s = str(v).strip().replace("B/.", "").replace("$", "").replace(",", "")
        try: return float(s)
        except: return 0.0

    df_yappy["total"] = df_yappy["total"].apply(clean_monto)
    df_yappy = df_yappy[(df_yappy["fecha"].notna()) & (df_yappy["total"] > 0)]

    if fecha_cierre_str:
        try:
            dt = datetime.strptime(fecha_cierre_str, '%d/%m/%Y')
            fecha_norm = dt.strftime("%Y-%m-%d")
            df_yappy = df_yappy[df_yappy["fecha"] == fecha_norm]
            print(f"✅ Filtradas {len(df_yappy)} transacciones para '{fecha_norm}'")
        except:
            print(f"⚠️ No se pudo parsear fecha_cierre: {fecha_cierre_str}")

    return {"data": df_yappy.to_dict(orient="records")}


# ========= ENDPOINTS =========


@router.post("/cierre_preview")
async def cierre_preview(cierre: UploadFile = File(...), hoja_cierre: str = Form(None)):
    try:
        contents = await cierre.read()
        cierre.file.seek(0)
        xls = pd.ExcelFile(io.BytesIO(contents))

        # === Selección de hoja ===
        if hoja_cierre:
            # Si es un número, convertir a índice
            if str(hoja_cierre).isdigit():
                idx = int(hoja_cierre) - 1  # Convertir de 1-based a 0-based
                idx = max(0, min(idx, len(xls.sheet_names) - 1))
                target = xls.sheet_names[idx]
                print(f"📄 Seleccionando hoja por índice: {hoja_cierre} → '{target}' (índice {idx})")
            else:
                target = hoja_cierre
                print(f"📄 Seleccionando hoja por nombre: '{target}'")
        else:
            # Buscar la primera hoja no vacía
            target = next(
                (n for n in xls.sheet_names if xls.parse(n).dropna(how="all").shape[0] > 0),
                xls.sheet_names[0]
            )
            print(f"📄 Auto-seleccionando primera hoja no vacía: '{target}'")

        # === Leer hoja seleccionada SIN dtype=str para detectar fechas ===
        df_raw = pd.read_excel(io.BytesIO(contents), sheet_name=target, header=None)
        
        print(f"📊 Forma del DataFrame: {df_raw.shape}")
        print(f"📋 Hojas disponibles: {xls.sheet_names}")
        
        parsed = parse_cierre_blackdog_posicional(df_raw)
        
        if not parsed:
            return {
                "error": "No se detectó el layout de Cierre Black Dog.",
                "sheet": str(target),
                "shape": df_raw.shape,
                "available_sheets": xls.sheet_names,
                "preview": df_raw.head(30).fillna("").astype(str).to_dict(orient="split")
            }

        # 🔥 GUARDAR LA FECHA ORIGINAL ANTES DE LIMPIAR
        fecha_original = parsed.get("meta", {}).get("fecha")
        print(f"📅 Fecha original del parser: '{fecha_original}' (tipo: {type(fecha_original)})")

        def limpiar(obj):
            if isinstance(obj, dict): 
                return {k: limpiar(v) for k, v in obj.items()}
            elif isinstance(obj, list): 
                return [limpiar(x) for x in obj]
            elif isinstance(obj, (float, np.floating)):
                return None if np.isnan(obj) or np.isinf(obj) else float(obj)
            return obj

        df_tabla = parsed.get("tabla", pd.DataFrame())
        if isinstance(df_tabla, pd.DataFrame) and "fecha" in df_tabla.columns:
            df_tabla["fecha"] = df_tabla["fecha"].astype(str)

        salida = {
            "sheet": str(target),
            "available_sheets": xls.sheet_names,
            "meta": {
                "fecha": fecha_original,  # 🔥 NO LIMPIAR LA FECHA
                "sucursal": parsed.get("meta", {}).get("sucursal"),
                "cajero": parsed.get("meta", {}).get("cajero")
            },
            "totales": limpiar(parsed.get("totales", {})),
            "tabla": limpiar(df_tabla.to_dict(orient="records")),
            "detalle_yappy": limpiar(parsed.get("detalle_yappy", [])),
            "detalle_ach": limpiar(parsed.get("detalle_ach", [])),
            "detalle_pedidosya": limpiar(parsed.get("detalle_pedidosya", []))
        }

        print(f"📤 Fecha final enviada al frontend: '{salida['meta'].get('fecha')}'")
        print(f"📊 Totales: {list(salida['totales'].keys())}")
        
        return salida

    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Error en cierre_preview: {e}")
        print(tb)
        return {"error": str(e), "trace": tb}


@router.post("/yappy_preview")
async def yappy_preview(yappy: UploadFile = File(...), fecha_cierre: str = Form(None)):
    try:
        print(f"📥 Recibido archivo Yappy: {yappy.filename}")
        print(f"📅 Fecha del cierre recibida: {fecha_cierre}")
        
        content = await yappy.read()
        df_raw = pd.read_excel(BytesIO(content), sheet_name=0, header=None)
        
        print(f"📊 Shape del Excel Yappy: {df_raw.shape}")
        
        result = parse_yappy_blackdog(df_raw, fecha_cierre_str=fecha_cierre)
        
        preview_data = result.get("data", [])
        print(f"✅ Total transacciones Yappy procesadas: {len(preview_data)}")
        
        return {
            "status": "success", 
            "preview": preview_data, 
            "total_rows": len(preview_data)
        }
    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ Error en yappy_preview: {e}")
        print(tb)
        return {"error": str(e), "trace": tb}
