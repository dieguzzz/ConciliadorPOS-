import pandas as pd
import re
from datetime import datetime, date

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

def parsear_fecha_yappy(fecha_str):
    """
    Parsea fechas con formato: 'sáb 22/11/2025' o '22/11/2025'
    Remueve el día de la semana si existe.
    """
    if pd.isna(fecha_str):
        return None
    
    fecha_str = str(fecha_str).strip()
    
    # Remover día de la semana si existe (lun, mar, mié, jue, vie, sáb, dom)
    fecha_str = re.sub(r'^(lun|mar|mi[ée]|jue|vie|s[áa]b|dom)\s+', '', fecha_str, flags=re.IGNORECASE)
    
    try:
        # Intentar parsear DD/MM/YYYY (formato español)
        return datetime.strptime(fecha_str, '%d/%m/%Y').date()
    except:
        try:
            # Fallback: usar pandas con dayfirst=True
            return pd.to_datetime(fecha_str, dayfirst=True).date()
        except:
            return None

def corregir_fecha_excel(fecha_raw):
    """
    Corrige el problema de Excel/pandas que confunde día y mes.
    Si Excel guardó 14/11/2025, pandas puede leerlo como 2025-01-14 en lugar de 2025-11-14.
    """
    if fecha_raw is None:
        return None
    
    # Si es string, intentar parsearlo
    if isinstance(fecha_raw, str):
        try:
            fecha = pd.to_datetime(fecha_raw, dayfirst=True).date()
            return fecha
        except:
            return None
    
    # Si es datetime de pandas/Excel
    if isinstance(fecha_raw, (datetime, pd.Timestamp)):
        fecha = fecha_raw.date() if isinstance(fecha_raw, datetime) else fecha_raw.to_pydatetime().date()
        
        # Verificar si mes y día podrían estar intercambiados
        # Solo si ambos valores son <= 12 (pueden ser válidos en ambas posiciones)
        if fecha.month <= 12 and fecha.day <= 12:
            # Retornar ambas posibilidades para que el sistema elija la correcta
            # por ahora, asumimos que DD/MM es más común en Panamá
            # Si pandas leyó 2025-01-14, lo correcto probablemente sea 2025-14-01 (imposible)
            # o realmente es 2025-11-14 (14 de noviembre)
            # Por simplicidad, retornamos la fecha tal cual y dejamos que el matching decida
            pass
        
        return fecha
    
    # Si ya es date
    if isinstance(fecha_raw, date):
        return fecha_raw
    
    return None

def parse_yappy_cierre(file_path: str):
    """Extrae la fecha y tabla Yappy del archivo de cierre POS"""
    df = pd.read_excel(file_path, header=None)
    fecha_cierre = None

    # Buscar la celda que contiene "FECHA DE CIERRE"
    for i, row in df.iterrows():
        for j, val in enumerate(row):
            if isinstance(val, str) and "FECHA DE CIERRE" in val.upper():
                fecha_cierre_raw = df.iloc[i + 1, j]
                
                # Usar la función de corrección
                fecha_cierre = corregir_fecha_excel(fecha_cierre_raw)
                
                # 🔥 FIX: Si pandas confundió día/mes (típico problema)
                # Intentar intercambiar si es posible
                if isinstance(fecha_cierre_raw, (datetime, pd.Timestamp)) and fecha_cierre:
                    if fecha_cierre.month <= 12 and fecha_cierre.day <= 12:
                        # Ambos valores son válidos, crear fecha alternativa
                        try:
                            fecha_alternativa = date(fecha_cierre.year, fecha_cierre.day, fecha_cierre.month)
                            # Guardamos ambas para comparar después
                            # Por ahora usamos la alternativa si el mes es pequeño (< 13)
                            # La lógica real se hará en conciliar_yappy
                            print(f"⚠️ Fecha ambigua detectada: {fecha_cierre} vs {fecha_alternativa}")
                        except:
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
    
    # 🔥 FIX: Usar el parseador custom que maneja el formato 'sáb 22/11/2025'
    df["fecha"] = df["fecha"].apply(parsear_fecha_yappy)
    
    df["celular"] = df["celular"].astype(str).apply(format_phone)
    df["monto"] = df["monto"].astype(float)
    
    # Eliminar filas sin fecha válida
    df = df[df["fecha"].notna()]
    
    return df


def conciliar_yappy(cierre_path: str, yappy_path: str):
    """Compara las transacciones del cierre con las del archivo Yappy"""
    from datetime import timedelta
    
    fecha_cierre, cierre_yappy = parse_yappy_cierre(cierre_path)
    df_yappy = parse_yappy_transacciones(yappy_path)

    # 🔥 FIX 1: Si la fecha puede estar confundida (día/mes intercambiados)
    # Intentar con ambas versiones y usar la que tenga más coincidencias
    df_filtrado = df_yappy[df_yappy["fecha"] == fecha_cierre]
    
    # Si no hay transacciones y es posible que día/mes estén intercambiados
    if len(df_filtrado) == 0 and fecha_cierre.month <= 12 and fecha_cierre.day <= 12:
        try:
            fecha_alternativa = date(fecha_cierre.year, fecha_cierre.day, fecha_cierre.month)
            df_filtrado_alt = df_yappy[df_yappy["fecha"] == fecha_alternativa]
            
            if len(df_filtrado_alt) > 0:
                print(f"⚠️ Usando fecha alternativa {fecha_alternativa} en lugar de {fecha_cierre}")
                print(f"   Encontradas {len(df_filtrado_alt)} transacciones")
                df_filtrado = df_filtrado_alt
                fecha_cierre = fecha_alternativa
        except:
            pass
    
    # 🔥 FIX 2: Si aún no hay transacciones, buscar en rango de hasta 4 días
    # Los Yappy pueden llegar con retraso de varios días
    if len(df_filtrado) == 0:
        print(f"⚠️ No se encontraron transacciones para {fecha_cierre}")
        print(f"   Buscando en rango de hasta 4 días después...")
        
        fecha_inicio = fecha_cierre
        fecha_fin = fecha_cierre + timedelta(days=4)
        
        df_filtrado = df_yappy[
            (df_yappy["fecha"] >= fecha_inicio) & 
            (df_yappy["fecha"] <= fecha_fin)
        ]
        
        if len(df_filtrado) > 0:
            fechas_encontradas = df_filtrado["fecha"].unique()
            print(f"✅ Encontradas {len(df_filtrado)} transacciones en el rango {fecha_inicio} a {fecha_fin}")
            print(f"   Fechas con transacciones: {sorted(fechas_encontradas)}")
        else:
            print(f"❌ No se encontraron transacciones ni en el rango de 4 días")

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

    # Determinar rango de fechas usado
    fechas_usadas = sorted(df_filtrado["fecha"].unique()) if len(df_filtrado) > 0 else []
    fecha_min = str(min(fechas_usadas)) if fechas_usadas else str(fecha_cierre)
    fecha_max = str(max(fechas_usadas)) if fechas_usadas else str(fecha_cierre)
    
    # Armar salida
    return {
        "fecha": str(fecha_cierre),
        "fecha_rango": {
            "inicio": fecha_min,
            "fin": fecha_max,
            "dias": len(fechas_usadas)
        } if len(fechas_usadas) > 1 else None,
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
