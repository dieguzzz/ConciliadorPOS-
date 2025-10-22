import pandas as pd
import re
from datetime import datetime

def format_phone(phone):
    """Formatea el número de teléfono al estilo (+507) 6615-3492"""
    if not isinstance(phone, str):
        return ""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("507"):
        digits = digits[3:]
    if len(digits) == 8:
        return f"(+507) {digits[:4]}-{digits[4:]}"
    return phone

def parse_yappy_cierre(file_path: str):
    """Extrae la fecha y tabla Yappy del archivo de cierre POS"""
    df = pd.read_excel(file_path, header=None)
    fecha_cierre = None

    # Buscar la celda que contiene "FECHA DE CIERRE"
    for i, row in df.iterrows():
        for j, val in enumerate(row):
            if isinstance(val, str) and "FECHA DE CIERRE" in val.upper():
                fecha_cierre = df.iloc[i + 1, j]
                if isinstance(fecha_cierre, datetime):
                    fecha_cierre = fecha_cierre.date()
                elif isinstance(fecha_cierre, str):
                    try:
                        fecha_cierre = pd.to_datetime(fecha_cierre, dayfirst=True).date()
                    except Exception:
                        pass

    # Buscar columna YAPPY
    col_yappy = None
    for col in df.columns:
        if df[col].astype(str).str.contains("YAPPY", case=False, na=False).any():
            col_yappy = col
            break
    if col_yappy is None:
        raise ValueError("No se encontró la columna 'YAPPY' en el archivo de cierre.")

    # La siguiente columna es la de montos
    col_monto = col_yappy + 1

    # Extraer filas con datos (nombres válidos)
    data = []
    for i in range(col_yappy + 1, len(df)):
        nombre = df.iloc[i, col_yappy]
        monto = df.iloc[i, col_monto]
        if pd.isna(nombre) or str(nombre).strip() == "":
            continue
        if isinstance(monto, str):
            monto = re.sub(r"[^\d.,]", "", monto)
        try:
            monto = float(str(monto).replace(",", ""))
        except:
            continue
        data.append({"cliente": str(nombre).strip(), "monto": monto})

    return fecha_cierre, data


def parse_yappy_transacciones(file_path: str):
    """Lee las transacciones Yappy originales (formato ExcelTransactionsYappy)"""
    df = pd.read_excel(file_path, sheet_name="ExcelTransactionsYappy", header=11)

    df = df.rename(
        columns={
            "Fecha": "fecha",
            "Referencia": "referencia",
            "Nombre del cliente": "cliente",
            "Celular": "celular",
            "Estado": "estado",
            "Total": "monto",
        }
    )

    df = df[["fecha", "referencia", "cliente", "celular", "estado", "monto"]].dropna(how="all")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    df["celular"] = df["celular"].astype(str).apply(format_phone)
    df["monto"] = df["monto"].astype(float)
    return df


def conciliar_yappy(cierre_path: str, yappy_path: str):
    """Compara las transacciones del cierre con las del archivo Yappy"""
    fecha_cierre, cierre_yappy = parse_yappy_cierre(cierre_path)
    df_yappy = parse_yappy_transacciones(yappy_path)

    # Filtrar solo las transacciones de la misma fecha
    df_filtrado = df_yappy[df_yappy["fecha"] == fecha_cierre]

    comparacion = []
    for linea in cierre_yappy:
        nombre_cierre = linea["cliente"].strip().upper()
        monto_cierre = round(linea["monto"], 2)

        # Coincidencias exactas
        match_exacto = df_filtrado[
            (df_filtrado["cliente"].str.upper() == nombre_cierre)
            & (df_filtrado["monto"].round(2) == monto_cierre)
        ]

        # Coincidencias por monto
        match_monto = df_filtrado[df_filtrado["monto"].round(2) == monto_cierre]

        if len(match_exacto) > 0:
            estado = "coincide"      # Verde
        elif len(match_monto) > 0:
            estado = "monto_igual"   # Naranja
        else:
            estado = "sin_match"     # Blanco

        comparacion.append({
            "cliente": linea["cliente"],
            "monto": linea["monto"],
            "estado": estado
        })

    # Armar salida
    return {
        "fecha": str(fecha_cierre),
        "yappy_cierre": cierre_yappy,
        "yappy_app": df_filtrado.to_dict(orient="records"),
        "comparacion": comparacion,
    }


# 🔍 Prueba manual
if __name__ == "__main__":
    salida = conciliar_yappy(
        "CIERRE CONDADO SEPTIEMBRE 2025 16-24 YAXEL.xlsx",
        "transacciones_yappyBASE.xlsx"
    )
    print(salida)
