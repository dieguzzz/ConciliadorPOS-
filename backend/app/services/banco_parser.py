import pandas as pd
from datetime import datetime, timedelta

def parse_banco(file_path: str, lista_pos_path: str):
    """
    Parser de movimientos bancarios (CLAVE / VISA)
    Cruza los números de punto de venta con las sucursales
    y ajusta la fecha restando un día.
    """

    # === Leer lista de puntos de venta ===
    lista_df = pd.read_excel(lista_pos_path)
    lista_df.columns = lista_df.columns.str.strip().str.lower()
    # Se espera que tenga columnas como: 'sucursal' y 'numero pos'
    lista_df = lista_df.rename(columns={
        'numero pos': 'numero_pos',
        'número pos': 'numero_pos'
    })

    # Crear diccionario {numero_pos: sucursal}
    pos_map = {str(row['numero_pos']).strip(): str(row['sucursal']).strip()
               for _, row in lista_df.iterrows() if not pd.isna(row['numero_pos'])}

    # === Leer archivo de movimientos bancarios ===
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()

    # Normalizar columnas esperadas
    if not {'fecha', 'descripcion', 'crédito'}.issubset(df.columns):
        raise ValueError("El archivo bancario debe contener columnas: Fecha, Descripción, Crédito")

    df = df.rename(columns={'crédito': 'credito'})

    # Limpiar filas vacías
    df = df.dropna(subset=['fecha', 'descripcion', 'credito'])
    df = df[df['credito'] != 0]

    # === Ajustar la fecha (un día antes) ===
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce') - timedelta(days=1)
    df['fecha'] = df['fecha'].dt.date

    # === Determinar tipo (CLAVE o VISA) ===
    def get_tipo(desc):
        d = str(desc).upper()
        if 'POS' in d:
            return 'CLAVE'
        elif 'T/C' in d:
            return 'VISA'
        else:
            return 'OTRO'

    df['tipo'] = df['descripcion'].apply(get_tipo)

    # === Buscar sucursal según número POS ===
    def buscar_sucursal(desc):
        for num_pos, sucursal in pos_map.items():
            if str(num_pos) in str(desc):
                return sucursal
        return 'DESCONOCIDO'

    df['sucursal'] = df['descripcion'].apply(buscar_sucursal)

    # === Abreviaciones de sucursal ===
    abrevs = {
        "PLAZA EMPORIO": "PE",
        "OCEAN MALL": "OM",
        "BELLA VISTA": "BV",
        "ALBROOK FIELDS": "ALB",
        "BRISAS DEL GOLF": "BDG",
        "CALLE 50": "CA50",
        "SANTA MARÍA": "SM",
        "COSTA VERDE": "CV",
        "VILLA ZAITA": "VZ",
        "CONDADO DEL REY": "CDREY",
        "VERSALLES": "VERS",
        "BRISAS NORTE": "BNORT",
        "COCO DEL MAR": "CDM",
    }

    # === Crear campo tipo_sucursal ===
    def construir_tipo_sucursal(row):
        suc = abrevs.get(row['sucursal'].upper(), 'N/A')
        tipo = row['tipo']
        fecha = pd.to_datetime(row['fecha'])
        return f"{suc} {tipo} {fecha.strftime('%d-%m')}"
    
    df['tipo_sucursal'] = df.apply(construir_tipo_sucursal, axis=1)

    # === Rango de fechas ===
    fecha_inicio = str(df['fecha'].min())
    fecha_fin = str(df['fecha'].max())

    # === Construir preview ===
    preview = []
    for _, row in df.head(5).iterrows():
        preview.append({
            "fecha": str(row['fecha']),
            "descripcion": str(row['descripcion']).strip(),
            "sucursal": row['sucursal'],
            "tipo": row['tipo'],
            "tipo_sucursal": row['tipo_sucursal'],
            "monto": float(row['credito'])
        })

    # === Respuesta final ===
    result = {
        "hoja": "MovimientosBanco",
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_registros": len(df),
        "preview": preview
    }

    return result


# --- Ejemplo de uso ---
if __name__ == "__main__":
    salida = parse_banco(
        "MOVIMIENTOS-CLAVE VISA 30-08 AL 16-09 YAXEL.xlsx",
        "Lista_Punto_Venta.xlsx"
    )
    print(salida)
