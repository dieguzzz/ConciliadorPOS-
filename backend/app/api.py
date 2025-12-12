from fastapi import APIRouter, UploadFile, File, Form 
from fastapi.responses import StreamingResponse
from datetime import datetime 
from io import BytesIO

import pandas as pd
import numpy as np
import io, traceback, re
import tempfile
from app.utils.file_reader import read_file, get_excel_sheets, detect_file_type
from app.utils.filename_parser import extraer_fecha_del_nombre, validar_y_corregir_fecha_con_nombre

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

def parse_cierre_blackdog_posicional(df_raw: pd.DataFrame, info_nombre: dict = None):
    """Lee el cierre por coordenadas (según layout Black Dog).
    
    Args:
        df_raw: DataFrame con los datos del Excel
        info_nombre: Información extraída del nombre del archivo (mes, año, etc.)
    """
    df_str = df_raw.astype(str).fillna("")
    
    # Buscar banner en más filas (hasta 20 filas) para ser más flexible
    banner = " ".join(df_str.iloc[:20, :].values.flatten()).upper()
    tiene_banner = "CIERRE DE PUNTO DE VENTA" in banner or "CIERRE" in banner
    
    if not tiene_banner:
        print(f"⚠️ No se encontró banner 'CIERRE DE PUNTO DE VENTA' en las primeras 20 filas")
        print(f"   Dimensiones del DataFrame: {df_raw.shape}")
        print(f"   Primeras 5 filas, primeras 10 columnas:")
        for i in range(min(5, len(df_raw))):
            row_preview = [str(df_raw.iloc[i, j])[:30] if j < len(df_raw.columns) else "" for j in range(min(10, len(df_raw.columns)))]
            print(f"   Fila {i+1}: {row_preview}")
        return None

    # Buscar cajero, fecha y sucursal de manera más flexible
    # Intentar múltiples filas alrededor de la fila 8
    cajero = None
    fecha_v = None
    suc_v = None
    
    for fila_offset in range(-2, 3):  # Buscar desde fila 6 hasta 10
        fila_base = 8 + fila_offset
        if fila_base < 1 or fila_base >= len(df_raw):
            continue
            
        # Buscar cajero
        if not cajero:
            for col in ["E", "F", "G", "D", "H"]:
                cajero = _below(df_raw, f"{col}{fila_base}") or _get(df_raw, f"{col}{fila_base}")
                if cajero and str(cajero).strip():
                    break
        
        # Buscar fecha
        if not fecha_v:
            for col in ["I", "J", "K", "L", "H", "M"]:
                fecha_v = _below(df_raw, f"{col}{fila_base}") or _get(df_raw, f"{col}{fila_base}")
                if fecha_v and str(fecha_v).strip() and str(fecha_v).strip().upper() not in ["NAN", "NONE", ""]:
                    break
        
        # Buscar sucursal
        if not suc_v:
            for col in ["N", "O", "P", "Q", "M", "R"]:
                suc_v = _below(df_raw, f"{col}{fila_base}") or _get(df_raw, f"{col}{fila_base}")
                if suc_v and str(suc_v).strip() and str(suc_v).strip().upper() not in ["NAN", "NONE", ""]:
                    break
        
        if cajero and fecha_v and suc_v:
            break
    
    print(f"📋 Datos encontrados:")
    print(f"   Cajero: {cajero}")
    print(f"   Fecha: {fecha_v} (tipo: {type(fecha_v).__name__})")
    print(f"   Sucursal: {suc_v}")

    fecha = None
    fecha_str_original = None
    
    if fecha_v is not None:
        print(f"📅 Valor crudo de fecha: '{fecha_v}' (tipo: {type(fecha_v)})")
        
        # Convertir fecha_v a string para procesamiento
        if isinstance(fecha_v, pd.Timestamp):
            fecha_iso = fecha_v.strftime("%Y-%m-%d")
            year, month, day = fecha_iso.split("-")
            # Intentar interpretar como DD/MM/YYYY (intercambiar mes y día)
            fecha_str_original = f"{day}/{month}/{year}"
        elif isinstance(fecha_v, datetime):
            fecha_iso = fecha_v.strftime("%Y-%m-%d")
            year, month, day = fecha_iso.split("-")
            fecha_str_original = f"{day}/{month}/{year}"
        else:
            fecha_str_original = str(fecha_v).strip()
        
        # Si tenemos información del nombre del archivo, usarla para validar/corregir
        if info_nombre and info_nombre.get('mes'):
            fecha_corregida, fue_corregida = validar_y_corregir_fecha_con_nombre(
                fecha_str_original,
                info_nombre,
                fecha_str_original
            )
            if fue_corregida:
                fecha_str_original = fecha_corregida
                print(f"✅ Fecha corregida usando nombre del archivo en parser: '{fecha_v}' → '{fecha_str_original}'")
        
        # Parsear la fecha final
        try:
            dt = datetime.strptime(fecha_str_original, "%d/%m/%Y")
            fecha = dt.date()
            print(f"✅ Fecha cierre final: '{fecha_str_original}' → {fecha}")
        except ValueError:
            # Si falla, intentar otros formatos
            try:
                dt = pd.to_datetime(fecha_str_original, dayfirst=True)
                fecha = dt.date()
                fecha_str_original = fecha.strftime("%d/%m/%Y")
                print(f"✅ Fecha cierre (fallback): '{fecha_v}' → '{fecha_str_original}' → {fecha}")
            except Exception as e:
                print(f"❌ Error parseando fecha: {e}")
                if isinstance(fecha_v, (datetime, pd.Timestamp)):
                    fecha = fecha_v.date() if isinstance(fecha_v, datetime) else fecha_v.date()
                    fecha_str_original = fecha.strftime("%d/%m/%Y")

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
    """Parser específico para Yappy de Black Dog. Soporta Excel y CSV."""
    # Detectar si es CSV (primera fila tiene encabezados) o Excel (buscar fila de encabezados)
    first_row_str = " ".join(str(x).strip().upper() for x in df_raw.iloc[0] if pd.notna(x))
    is_csv_format = "FECHA" in first_row_str and "REFERENCIA" in first_row_str
    
    if is_csv_format:
        # CSV: primera fila son los encabezados
        print("📄 Detectado formato CSV - usando encabezados de la primera fila")
        df_data = df_raw.iloc[1:].reset_index(drop=True)  # Saltar primera fila (encabezados)
        
        # Mapear columnas por nombre (normalizado)
        header_row = df_raw.iloc[0].astype(str).str.strip().str.upper()
        col_map = {}
        
        # Buscar columnas por nombre (flexible)
        for idx, header in enumerate(header_row):
            header_upper = str(header).upper()
            if "FECHA" in header_upper and "fecha" not in col_map:
                col_map["fecha"] = idx
            elif "REFERENCIA" in header_upper and "referencia" not in col_map:
                col_map["referencia"] = idx
            elif ("NOMBRE" in header_upper and "CLIENTE" in header_upper) or ("CLIENTE" in header_upper and "cliente" not in col_map):
                col_map["cliente"] = idx
            elif "CELULAR" in header_upper and "celular" not in col_map:
                col_map["celular"] = idx
            elif "ESTADO" in header_upper and "estado" not in col_map:
                col_map["estado"] = idx
            elif "TOTAL" in header_upper and "total" not in col_map and "SUB-TOTAL" not in header_upper:
                col_map["total"] = idx
        
        # Validar que encontramos todas las columnas necesarias
        required_cols = ["fecha", "referencia", "cliente", "celular", "estado", "total"]
        missing = [c for c in required_cols if c not in col_map]
        if missing:
            raise ValueError(f"❌ No se encontraron las columnas requeridas: {missing}. Columnas encontradas: {list(col_map.keys())}")
        
        print(f"✅ Columnas mapeadas: {col_map}")
        df_yappy = pd.DataFrame({
            "fecha": df_data.iloc[:, col_map["fecha"]],
            "referencia": df_data.iloc[:, col_map["referencia"]],
            "cliente": df_data.iloc[:, col_map["cliente"]],
            "celular": df_data.iloc[:, col_map["celular"]],
            "estado": df_data.iloc[:, col_map["estado"]],
            "total": df_data.iloc[:, col_map["total"]],
        })
    else:
        # Excel: buscar fila de encabezados
        print("📄 Detectado formato Excel - buscando fila de encabezados")
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
            from datetime import timedelta
            dt = datetime.strptime(fecha_cierre_str, '%d/%m/%Y')
            fecha_norm = dt.strftime("%Y-%m-%d")
            
            # Intentar primero con la fecha exacta
            df_filtrado = df_yappy[df_yappy["fecha"] == fecha_norm]
            
            # 🔥 Si no encuentra transacciones, buscar en rango de hasta 4 días
            if len(df_filtrado) == 0:
                print(f"⚠️ No se encontraron transacciones para {fecha_norm}")
                print(f"   Buscando en rango de hasta 4 días...")
                
                fecha_inicio = dt
                fecha_fin = dt + timedelta(days=4)
                fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
                fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
                
                df_filtrado = df_yappy[
                    (df_yappy["fecha"] >= fecha_inicio_str) & 
                    (df_yappy["fecha"] <= fecha_fin_str)
                ]
                
                if len(df_filtrado) > 0:
                    fechas_encontradas = sorted(df_filtrado["fecha"].unique())
                    print(f"✅ Encontradas {len(df_filtrado)} transacciones en rango {fecha_inicio_str} a {fecha_fin_str}")
                    print(f"   Fechas con transacciones: {fechas_encontradas}")
                else:
                    print(f"❌ No se encontraron transacciones ni en el rango de 4 días")
            else:
                print(f"✅ Filtradas {len(df_filtrado)} transacciones para '{fecha_norm}'")
            
            df_yappy = df_filtrado
        except:
            print(f"⚠️ No se pudo parsear fecha_cierre: {fecha_cierre_str}")

    return {"data": df_yappy.to_dict(orient="records")}


# ========= ENDPOINTS =========


@router.post("/cierre_preview")
async def cierre_preview(cierre: UploadFile = File(...), hoja_cierre: str = Form(None)):
    try:
        contents = await cierre.read()
        cierre.file.seek(0)
        filename = cierre.filename or "archivo.xlsx"
        file_type = detect_file_type(filename)
        
        # 🔥 EXTRAER INFORMACIÓN DEL NOMBRE DEL ARCHIVO PRIMERO
        info_nombre = extraer_fecha_del_nombre(filename)
        if info_nombre:
            print(f"📋 Información extraída del nombre '{filename}':")
            print(f"   - Mes: {info_nombre.get('mes_nombre', info_nombre.get('mes'))}")
            print(f"   - Año: {info_nombre.get('año')}")
            if info_nombre.get('dia_inicio') and info_nombre.get('dia_fin'):
                print(f"   - Rango de días: {info_nombre['dia_inicio']}-{info_nombre['dia_fin']}")
        
        # === Selección de hoja (solo para Excel/ODS, no CSV) ===
        target = None
        available_sheets = []
        
        if file_type.startswith('excel') or file_type == 'ods':
            available_sheets = get_excel_sheets(contents, filename)
            
            if hoja_cierre:
                # Si es un número, convertir a índice
                if str(hoja_cierre).isdigit():
                    idx = int(hoja_cierre) - 1  # Convertir de 1-based a 0-based
                    idx = max(0, min(idx, len(available_sheets) - 1))
                    target = available_sheets[idx]
                    print(f"📄 Seleccionando hoja por índice: {hoja_cierre} → '{target}' (índice {idx})")
                else:
                    target = hoja_cierre
                    print(f"📄 Seleccionando hoja por nombre: '{target}'")
            else:
                # Por defecto, usar la primera hoja (índice 0)
                if available_sheets:
                    target = available_sheets[0]
                    print(f"📄 Usando hoja 1 por defecto: '{target}'")
                else:
                    print(f"⚠️ No se encontraron hojas en el archivo")
        else:
            # Para CSV, no hay hojas
            print(f"📄 Archivo CSV, no se requiere selección de hoja")

        # === Leer archivo ===
        df_raw = read_file(contents, filename, sheet_name=target, header=None)
        
        print(f"📊 Forma del DataFrame: {df_raw.shape}")
        print(f"📋 Hojas disponibles: {available_sheets}")
        
        # Pasar información del nombre al parser para validar fechas
        parsed = parse_cierre_blackdog_posicional(df_raw, info_nombre=info_nombre)
        
        if not parsed:
            return {
                "error": "No se detectó el layout de Cierre Black Dog.",
                "sheet": str(target) if target else "N/A",
                "shape": df_raw.shape,
                "available_sheets": available_sheets,
                "preview": df_raw.head(30).fillna("").astype(str).to_dict(orient="split")
            }

        # 🔥 GUARDAR LA FECHA ORIGINAL ANTES DE LIMPIAR
        fecha_original = parsed.get("meta", {}).get("fecha")
        print(f"📅 Fecha original del parser: '{fecha_original}' (tipo: {type(fecha_original)})")
        
        # 🔥 EXTRAER INFORMACIÓN DEL NOMBRE DEL ARCHIVO Y VALIDAR FECHA
        info_nombre = extraer_fecha_del_nombre(filename)
        fecha_final = fecha_original
        
        if info_nombre:
            print(f"📋 Información extraída del nombre '{filename}':")
            print(f"   - Mes: {info_nombre.get('mes_nombre', info_nombre.get('mes'))}")
            print(f"   - Año: {info_nombre.get('año')}")
            if info_nombre.get('dia_inicio') and info_nombre.get('dia_fin'):
                print(f"   - Rango de días: {info_nombre['dia_inicio']}-{info_nombre['dia_fin']}")
            
            # Validar y corregir fecha usando información del nombre
            if fecha_original:
                # Convertir fecha_original a string si es necesario
                if isinstance(fecha_original, (datetime, pd.Timestamp)):
                    fecha_str = fecha_original.strftime("%d/%m/%Y") if isinstance(fecha_original, datetime) else fecha_original.strftime("%d/%m/%Y")
                else:
                    fecha_str = str(fecha_original)
                
                fecha_corregida, fue_corregida = validar_y_corregir_fecha_con_nombre(
                    fecha_str,
                    info_nombre,
                    fecha_original
                )
                
                if fue_corregida:
                    fecha_final = fecha_corregida
                    print(f"✅ Fecha corregida usando nombre del archivo: '{fecha_original}' -> '{fecha_final}'")
                else:
                    print(f"✅ Fecha validada correctamente: '{fecha_final}' coincide con el mes del nombre")
        else:
            print(f"⚠️ No se pudo extraer información de fecha del nombre del archivo")

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
            "sheet": str(target) if target else "N/A",
            "available_sheets": available_sheets,
            "meta": {
                "fecha": fecha_final,  # 🔥 USAR FECHA CORREGIDA/VALIDADA
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

    except ValueError as e:
        # Errores de formato de archivo
        error_msg = f"Error en el formato del archivo: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg, "type": "format_error"}
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"Error procesando archivo de cierre: {str(e)}"
        print(f"❌ {error_msg}")
        print(tb)
        return {
            "error": error_msg,
            "type": "processing_error",
            "trace": tb if "trace" in str(e).lower() else None
        }


@router.post("/yappy_preview")
async def yappy_preview(yappy: UploadFile = File(...), fecha_cierre: str = Form(None)):
    try:
        print(f"📥 Recibido archivo Yappy: {yappy.filename}")
        print(f"📅 Fecha del cierre recibida: {fecha_cierre}")
        
        content = await yappy.read()
        filename = yappy.filename or "archivo.xlsx"
        # Para Yappy, leer la primera hoja (índice 0) o sin hoja si es CSV
        sheet_name = 0 if detect_file_type(filename) == 'excel' else None
        df_raw = read_file(content, filename, sheet_name=sheet_name, header=None)
        
        print(f"📊 Shape del Excel Yappy: {df_raw.shape}")
        
        result = parse_yappy_blackdog(df_raw, fecha_cierre_str=fecha_cierre)
        
        preview_data = result.get("data", [])
        print(f"✅ Total transacciones Yappy procesadas: {len(preview_data)}")
        
        return {
            "status": "success", 
            "preview": preview_data, 
            "total_rows": len(preview_data)
        }
    except ValueError as e:
        error_msg = f"Error en el formato del archivo Yappy: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg, "type": "format_error"}
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"Error procesando archivo Yappy: {str(e)}"
        print(f"❌ {error_msg}")
        print(tb)
        return {
            "error": error_msg,
            "type": "processing_error",
            "trace": tb if "trace" in str(e).lower() else None
        }
