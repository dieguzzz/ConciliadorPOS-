from fastapi import APIRouter, UploadFile, File, Form 
from app.services.banco_parser import parse_banco
from datetime import datetime 
from fastapi.responses import StreamingResponse
from io import BytesIO

import pandas as pd
import numpy as np
import io, traceback, re
import re
import tempfile
import unicodedata

router = APIRouter()

# ========= PARSER POSICIONAL DE CIERRE (BLACK DOG) =========

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


def parse_cierre_blackdog_posicional(df_raw: pd.DataFrame):
    """
    Lee el cierre por coordenadas (según layout Black Dog).
    Devuelve:
      meta: fecha, sucursal, cajero
      totales: dict de montos clave
      tabla: DataFrame normalizado (fecha, sucursal, origen, monto)
      detalle_yappy / detalle_ach / detalle_pedidosya: listas con detalle por método
    """
    df_str = df_raw.astype(str).fillna("")
    banner = " ".join(df_str.iloc[:12, :].values.flatten()).upper()
    if "CIERRE DE PUNTO DE VENTA" not in banner:
        return None

    # === 1) ENCABEZADOS ===
    cajero = _below(df_raw, "E8") or _below(df_raw, "F8") or _below(df_raw, "G8")
    fecha_v = _below(df_raw, "I8") or _below(df_raw, "J8") or _below(df_raw, "K8") or _below(df_raw, "L8")
    suc_v = _below(df_raw, "N8") or _below(df_raw, "O8") or _below(df_raw, "P8") or _below(df_raw, "Q8")

    fecha = (
        pd.to_datetime(fecha_v, errors="coerce", dayfirst=True).date()
        if fecha_v
        else pd.NaT
    )
    sucursal = (str(suc_v).strip().upper() if suc_v else "DESCONOCIDA")

    # === 2) BLOQUES DE YAPPY / ACH / PEDIDOS YA ===
    def _leer_bloque(col_titulo, col_monto, fila_ini, fila_fin, col_total):
        """Lee un bloque de método de pago hasta encontrar 'Total'."""
        items = []
        for f in range(fila_ini, fila_fin):
            nombre = _get(df_raw, f"{col_titulo}{f}")
            monto = _get(df_raw, f"{col_monto}{f}")
            if str(nombre).strip().upper() == "TOTAL":
                break
            if nombre and str(nombre).strip() != "" and monto not in (None, "", np.nan):
                val = _to_float(monto)
                if not np.isnan(val):
                    items.append({
                        "nombre": str(nombre).strip(),
                        "monto": f"B/. {val:.2f}"
                    })
        total_val = _get(df_raw, f"{col_total}{fila_fin}")
        total_val_f = _to_float(total_val)
        total_fmt = f"B/. {total_val_f:.2f}" if pd.notna(total_val_f) else None
        return items, total_fmt

    detalle_yappy, total_yappy = _leer_bloque("I", "J", 15, 37, "K")
    detalle_ach, total_ach = _leer_bloque("N", "O", 15, 26, "O")
    detalle_pedidosya, total_pedya = _leer_bloque("Q", "R", 15, 37, "R")

    # === 3) TOTALES (lado izquierdo) ===
    lecturas = [
        ("EFECTIVO", "A13", "Derecha"),
        ("FONDO DE CAJA", "A14", "Derecha"),
        ("DEBITO (CLAVE)", "A16", "Derecha"),
        ("CREDITO (VISA/MASTER)", "A17", "Derecha"),
        ("TOTAL CON PEYA", "A20", "Derecha"),
        ("TOTAL SIN PEYA", "A21", "Derecha"),
        ("TOTAL DE INGRESO", "A24", "Derecha"),
        ("CIERRE DEL SISTEMA", "A25", "Derecha"),
        ("DIFERENCIA", "A26", "Derecha"),
        ("A DEPOSITAR EN EFECTIVO", "A28", "Derecha"),
    ]

    totales = {}
    for nombre, celda, modo in lecturas:
        if modo == "Derecha":
            val = _right_of(df_raw, celda, max_steps=6)
        else:
            val = _below(df_raw, celda, max_steps=6)
        totales[nombre] = round(float(_to_float(val)), 2) if pd.notna(_to_float(val)) else np.nan

    # Añadimos los totales detectados por posición fija
    if total_yappy:
        totales["YAPPY"] = _to_float(total_yappy)
    if total_ach:
        totales["ACH"] = _to_float(total_ach)
    if total_pedya:
        totales["PEDIDOS YA"] = _to_float(total_pedya)

    # === 4) TABLA FINAL ===
    orígenes = [
        "EFECTIVO", "YAPPY", "DEBITO (CLAVE)", "CREDITO (VISA/MASTER)",
        "ACH", "PEDIDOS YA", "TOTAL DE INGRESO", "CIERRE DEL SISTEMA", "DIFERENCIA"
    ]

    data_rows = []
    for o in orígenes:
        monto = totales.get(o, np.nan)
        if pd.notna(monto):
            data_rows.append({
                "fecha": fecha,
                "sucursal": sucursal,
                "origen": o,
                "monto": monto
            })

    df_tabla = pd.DataFrame(data_rows)
    meta = {
        "fecha": str(fecha) if pd.notna(pd.to_datetime(fecha, errors="coerce")) else None,
        "sucursal": sucursal,
        "cajero": (str(cajero).strip() if cajero else None)
    }

    return {
        "meta": meta,
        "totales": totales,
        "tabla": df_tabla,
        "detalle_yappy": detalle_yappy,
        "detalle_ach": detalle_ach,
        "detalle_pedidosya": detalle_pedidosya
    }


def parse_yappy_blackdog(df_raw: pd.DataFrame):
    """
    Parser robusto para archivos Yappy Black Dog.
    - Detecta dinámicamente las columnas correctas según el encabezado.
    - Limpia montos en formato "$59.95", "B/. 59.95" o similares.
    - Retorna un DataFrame limpio con: fecha, hora, referencia, cliente, celular, estado, total.
    """

    # Buscar fila de encabezados (donde aparece "FECHA" y "REFERENCIA")
    start_row = None
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x).strip().upper() for x in row if pd.notna(x))
        if "FECHA" in row_str and "REFERENCIA" in row_str:
            start_row = i
            break

    if start_row is None:
        raise ValueError("❌ No se encontró la fila de encabezados en el archivo Yappy")

    # Leer los encabezados reales desde esa fila
    df = pd.read_excel(
        io.BytesIO(df_raw.to_excel(index=False, header=False)),
        sheet_name="ExcelTransactionsYappy",
        header=start_row,
        engine="openpyxl"
    )

    # Normalizar nombres de columnas
    df.columns = [
        unicodedata.normalize("NFKD", str(c)).strip().lower().replace(" ", "_")
        for c in df.columns
    ]

    # 🔍 Detectar columnas esperadas
    col_fecha = next((c for c in df.columns if "fecha" in c), None)
    col_hora = next((c for c in df.columns if "hora" in c), None)
    col_ref = next((c for c in df.columns if "referencia" in c), None)
    col_cliente = next((c for c in df.columns if "nombre" in c), None)
    col_celular = next((c for c in df.columns if "celular" in c), None)
    col_estado = next((c for c in df.columns if "estado" in c), None)
    col_total = next((c for c in df.columns if "total" in c and "sub" not in c), None)

    if not col_total:
        raise ValueError("❌ No se encontró columna de Total en el archivo.")

    # Limpiar montos
    def clean_monto(v):
        if pd.isna(v):
            return 0.0

        # Si ya es número (float o int), úsalo directamente
        if isinstance(v, (float, int)):
            return float(v)

        # Si viene como texto, limpiamos
        s = str(v)
        s = (
            s.replace("B/.", "")
            .replace("B/ ", "")
            .replace("$", "")
            .replace(",", "")
            .replace(" ", "")
            .replace("=", "")
            .strip()
        )
        try:
            return float(s)
        except Exception:
            print(f"⚠️ No se pudo convertir monto: {repr(v)} -> '{s}'")
            return 0.0

    df["total"] = df[col_total].astype(str).apply(clean_monto)

    # Normalizar fecha
    df["fecha"] = pd.to_datetime(df[col_fecha], errors="coerce").dt.strftime("%Y-%m-%d")

    # Limpiar strings
    for c in [col_ref, col_cliente, col_celular, col_estado]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # Filtrar filas válidas
    df = df[df["total"] > 0]

    # Determinar rango de fechas
    fechas_validas = pd.to_datetime(df["fecha"], errors="coerce").dropna()
    fecha_inicio = fechas_validas.min().date() if not fechas_validas.empty else None
    fecha_fin = fechas_validas.max().date() if not fechas_validas.empty else None

    # Armar DataFrame final
    df_final = pd.DataFrame({
        "fecha": df["fecha"],
        "hora": df[col_hora] if col_hora else "",
        "referencia": df[col_ref],
        "cliente": df[col_cliente],
        "celular": df[col_celular],
        "estado": df[col_estado],
        "total": df["total"],
    })
    print("\n🟣 Columnas detectadas:", df_data.columns.tolist())
    print("🟣 Muestra de columnas W, X, Y:")
    for col_idx in range(20, 25):
        try:
            print(f"Columna {col_idx}: {df_data.iloc[:5, col_idx].tolist()}")
        except Exception:
            pass

    return {
        "fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
        "fecha_fin": str(fecha_fin) if fecha_fin else None,
        "data": df_final.to_dict(orient="records"),
    }

@router.post("/cierre_preview")
async def cierre_preview(cierre: UploadFile = File(...), hoja_cierre: str = Form(None)):
    """Lee SOLO el archivo de Cierre (Black Dog) de forma posicional."""
    try:
        contents = await cierre.read()
        cierre.file.seek(0)
        xls = pd.ExcelFile(io.BytesIO(contents))

        # === Selección de hoja ===
        if hoja_cierre:
            if str(hoja_cierre).isdigit():
                idx = int(hoja_cierre) - 1
                idx = max(0, min(idx, len(xls.sheet_names) - 1))
                target = xls.sheet_names[idx]
            else:
                target = hoja_cierre
        else:
            target = next(
                (n for n in xls.sheet_names if xls.parse(n).dropna(how="all").shape[0] > 0),
                xls.sheet_names[0]
            )

        # === Leer hoja seleccionada ===
        df_raw = pd.read_excel(io.BytesIO(contents), sheet_name=target, header=None)
        parsed = parse_cierre_blackdog_posicional(df_raw)
        if parsed is None:
            return {
                "error": "No se detectó el layout de Cierre Black Dog.",
                "sheet": str(target),
                "shape": df_raw.shape,
                "preview": df_raw.head(30).fillna("").astype(str).to_dict(orient="split")
            }

        # === Limpieza de datos antes de enviar ===
        def limpiar_valores(obj):
            if isinstance(obj, dict):
                return {k: limpiar_valores(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [limpiar_valores(x) for x in obj]
            elif isinstance(obj, (float, np.floating)):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return float(obj)
            return obj

        salida = {
            "sheet": str(target),
            "meta": parsed.get("meta", {}),
            "totales": limpiar_valores(parsed.get("totales", {})),
            "tabla": limpiar_valores(
                parsed.get("tabla", pd.DataFrame()).to_dict(orient="records")
                if isinstance(parsed.get("tabla"), pd.DataFrame)
                else parsed.get("tabla", [])
            ),
            "detalle_yappy": limpiar_valores(parsed.get("detalle_yappy", [])),
            "detalle_ach": limpiar_valores(parsed.get("detalle_ach", [])),
            "detalle_pedidosya": limpiar_valores(parsed.get("detalle_pedidosya", []))
        }

        return salida

    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "trace": tb}

@router.post("/conciliar_auto")
async def conciliar_auto(
    cierre: UploadFile = File(...),
    banco: UploadFile = File(...),
    yappy: UploadFile = File(...),
    hoja_cierre: str = Form(None),
):
    """
    Conciliación automática entre:
      - Cierre POS (Black Dog)
      - Movimientos bancarios (Clave/VISA)
      - Movimientos Yappy

    Devuelve coincidencias y pendientes (en cierre y en banco).
    """
    try:
        # === LEER ARCHIVOS EN MEMORIA ===
        cierre_bytes = await cierre.read()
        banco_bytes = await banco.read()
        yappy_bytes = await yappy.read()

        # === LEER HOJA DEL CIERRE ===
        cierre_xls = pd.ExcelFile(io.BytesIO(cierre_bytes))
        if hoja_cierre:
            if str(hoja_cierre).isdigit():
                idx = int(hoja_cierre) - 1
                idx = max(0, min(idx, len(cierre_xls.sheet_names) - 1))
                hoja = cierre_xls.sheet_names[idx]
            else:
                hoja = hoja_cierre
        else:
            hoja = cierre_xls.sheet_names[0]

        df_cierre_raw = pd.read_excel(io.BytesIO(cierre_bytes), sheet_name=hoja, header=None)
        parsed_cierre = parse_cierre_blackdog_posicional(df_cierre_raw)

        if parsed_cierre is None:
            return {"error": "No se detectó formato válido de cierre Black Dog."}

        df_cierre = parsed_cierre["tabla"].copy()
        df_cierre["monto"] = df_cierre["monto"].astype(float)
        df_cierre["origen"] = df_cierre["origen"].str.upper()

        # === PARSEAR MOVIMIENTOS BANCARIOS ===
        df_banco = pd.read_excel(io.BytesIO(banco_bytes))
        df_banco.columns = [c.strip().upper() for c in df_banco.columns]
        # Suponemos columnas: FECHA, MONTO, DETALLE / DESCRIPCION
        df_banco["fecha"] = pd.to_datetime(df_banco["FECHA"], errors="coerce").dt.date
        df_banco["monto"] = df_banco["MONTO"].apply(_to_float)
        df_banco["origen"] = "BANCO"

        # === PARSEAR MOVIMIENTOS YAPPY ===
        df_yappy = pd.read_excel(io.BytesIO(yappy_bytes))
        df_yappy.columns = [c.strip().upper() for c in df_yappy.columns]
        # Suponemos columnas: FECHA, MONTO, REFERENCIA o DESCRIPCION
        df_yappy["fecha"] = pd.to_datetime(df_yappy["FECHA"], errors="coerce").dt.date
        df_yappy["monto"] = df_yappy["MONTO"].apply(_to_float)
        df_yappy["origen"] = "YAPPY"

        # === UNIFICAR TODAS LAS FUENTES EXTERNAS ===
        externos = pd.concat([df_banco, df_yappy], ignore_index=True)
        externos = externos.dropna(subset=["fecha", "monto"])

        # === CONCILIAR POR FECHA Y MONTO ===
        conciliado = df_cierre.merge(
            externos,
            on=["fecha", "monto"],
            suffixes=("_cierre", "_externo"),
            how="outer",
            indicator=True
        )

        pendientes_cierre = conciliado[conciliado["_merge"] == "left_only"]
        pendientes_banco = conciliado[conciliado["_merge"] == "right_only"]
        coincidencias = conciliado[conciliado["_merge"] == "both"]

        # === SALIDA LIMPIA ===
        def limpiar(df):
            df = df.fillna("")
            return df.to_dict(orient="records")

        salida = {
            "meta": parsed_cierre.get("meta", {}),
            "totales_cierre": parsed_cierre.get("totales", {}),
            "coincidencias": limpiar(coincidencias),
            "pendientes_cierre": limpiar(pendientes_cierre),
            "pendientes_banco": limpiar(pendientes_banco),
            "detalle_yappy": parsed_cierre.get("detalle_yappy", []),
            "detalle_ach": parsed_cierre.get("detalle_ach", []),
            "detalle_pedidosya": parsed_cierre.get("detalle_pedidosya", [])
        }

        return salida

    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "trace": tb}

@router.post("/conciliar_exportar")
async def conciliar_exportar(
    cierre: UploadFile = File(...),
    banco: UploadFile = File(...),
    yappy: UploadFile = File(...),
    hoja_cierre: str = Form(None),
):
    """
    Genera un Excel conciliado con tres hojas:
      - Coincidencias
      - Pendientes en Cierre
      - Pendientes en Banco
    """
    try:
        # === Reutiliza la lógica de conciliación ===
        resultado = await conciliar_auto(cierre, banco, yappy, hoja_cierre)
        if "error" in resultado:
            return resultado

        coincidencias = pd.DataFrame(resultado["coincidencias"])
        pendientes_cierre = pd.DataFrame(resultado["pendientes_cierre"])
        pendientes_banco = pd.DataFrame(resultado["pendientes_banco"])

        # === Crear el archivo Excel en memoria ===
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            coincidencias.to_excel(writer, index=False, sheet_name="Coincidencias")
            pendientes_cierre.to_excel(writer, index=False, sheet_name="Pendientes Cierre")
            pendientes_banco.to_excel(writer, index=False, sheet_name="Pendientes Banco")

            # Añadir meta y totales como hoja resumen
            meta_df = pd.DataFrame([resultado["meta"]])
            totales_df = pd.DataFrame([resultado["totales_cierre"]])
            meta_df.to_excel(writer, index=False, sheet_name="Meta")
            totales_df.to_excel(writer, index=False, startrow=4, sheet_name="Meta")

        output.seek(0)

        # === Enviar como archivo descargable ===
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=conciliado.xlsx"},
        )

    except Exception as e:
        tb = traceback.format_exc()
        return {"error": str(e), "trace": tb}

@router.post("/yappy_preview")
async def yappy_preview(file: UploadFile = File(...)):
    """
    Lee el archivo Yappy (hoja 'ExcelTransactionsYappy')
    con encabezados en la fila 12 y datos desde la fila 13.
    Extrae las columnas clave del formato oficial Yappy Panamá.
    """
    import io
    import pandas as pd
    import unicodedata
    import traceback

    try:
        print("🟣 Paso 1: Recibiendo archivo Yappy...")
        contents = await file.read()

        # === Leer hoja ===
        df = pd.read_excel(
            io.BytesIO(contents),
            sheet_name="ExcelTransactionsYappy",
            header=11,  # fila 12 en Excel
            engine="openpyxl",
        )
        print("🟣 Paso 2: Archivo leído correctamente.")
        print("🔹 Columnas detectadas (originales):", df.columns.tolist()[:20])

        # === Normalizar nombres ===
        def limpiar_nombre(col):
            col = unicodedata.normalize("NFKD", str(col)).encode("ascii", "ignore").decode("utf-8")
            return col.strip().lower().replace("  ", " ")

        df.columns = [limpiar_nombre(c) for c in df.columns]
        print("🔹 Columnas normalizadas:", df.columns.tolist()[:20])

        # === Buscar columnas ===
        def buscar_columna(nombre, excluir=None):
            for c in df.columns:
                if nombre in c and (excluir not in c if excluir else True):
                    return c
            return None

        columnas = {
            "fecha": buscar_columna("fecha"),
            "hora": buscar_columna("hora"),
            "referencia": buscar_columna("referencia"),
            "cliente": buscar_columna("cliente"),
            "celular": buscar_columna("celular"),
            "estado": buscar_columna("estado"),
            "punto_cobro": buscar_columna("punto"),
            "subtotal": buscar_columna("sub"),
            "propina": buscar_columna("propina"),
            "descuento": buscar_columna("descuento"),
            "impuesto": buscar_columna("impuesto"),
            "total": buscar_columna("total", excluir="sub"),
        }

        print("🟣 Paso 3: Mapeo de columnas detectadas:", columnas)

        if not columnas["total"]:
            raise ValueError("❌ No se encontró la columna de 'Total' en el archivo.")

        # === Crear DataFrame limpio ===
        df_clean = pd.DataFrame({
            "fecha": df[columnas["fecha"]],
            "hora": df[columnas["hora"]],
            "referencia": df[columnas["referencia"]],
            "cliente": df[columnas["cliente"]],
            "celular": df[columnas["celular"]],
            "estado": df[columnas["estado"]],
            "punto_cobro": df[columnas["punto_cobro"]],
            "subtotal": df[columnas["subtotal"]],
            "propina": df[columnas["propina"]],
            "descuento": df[columnas["descuento"]],
            "impuesto": df[columnas["impuesto"]],
            "total": df[columnas["total"]],
        })
        print("🟣 Paso 4: DataFrame limpio creado. Registros:", len(df_clean))

        # === Limpieza de fechas ===
        def convertir_fecha(valor):
            try:
                texto = str(valor)
                texto = re.sub(r"^(lun|mar|mie|mié|jue|vie|sab|dom)\s*", "", texto.strip(), flags=re.IGNORECASE)
                return pd.to_datetime(texto, format="%d/%m/%Y", errors="coerce")
            except Exception:
                return pd.NaT

        df_clean["fecha"] = df_clean["fecha"].apply(convertir_fecha).dt.date

        # === Limpieza de montos ===
        def convertir_monto(valor):
            if pd.isna(valor):
                return 0.0
            if isinstance(valor, (float, int)):
                return float(valor)
            s = str(valor).strip().replace("B/.", "").replace("B/", "").replace("$", "").replace(",", "").replace(" ", "")
            try:
                return float(s)
            except Exception:
                return 0.0

        for col in ["subtotal", "propina", "descuento", "impuesto", "total"]:
            df_clean[col] = df_clean[col].apply(convertir_monto)

        print("🟣 Paso 5: Montos convertidos correctamente.")
        print("🟣 Muestra de totales no nulos:", df_clean[df_clean["total"] > 0].head(3).to_dict(orient="records"))

        # === Respuesta final ===
        return {
            "hoja": "ExcelTransactionsYappy",
            "total_registros": len(df_clean),
            "columns": df_clean.columns.tolist(),
            "preview": df_clean.head(50).to_dict(orient="records"),
        }

    except Exception as e:
        print("❌ ERROR EN PROCESO YAPPY:")
        print(traceback.format_exc())
        return {"error": str(e), "trace": traceback.format_exc()}

@router.post("/api/banco_preview")
async def banco_preview(file: UploadFile):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    lista_pos_path = "data/Lista_Punto_Venta.xlsx"
    data = parse_banco(tmp_path, lista_pos_path)
    return data