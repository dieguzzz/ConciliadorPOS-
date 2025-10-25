# backend/app/api_banco.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import pandas as pd
import io
import re
import traceback
from datetime import datetime
from pathlib import Path

router = APIRouter()

# --- Funciones auxiliares ---

def limpiar_monto(valor):
    """Convierte montos tipo 'B/. 59.95', '$59,95', '(59.95)' en float."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    val = str(valor).strip()
    val = val.replace("B/.", "").replace("B/ ", "").replace("$", "").replace(",", ".")
    val = re.sub(r"[^0-9.\-]", "", val)
    try:
        return abs(float(val))
    except:
        return None


def limpiar_fecha(valor):
    """Intenta convertir fechas a formato datetime.date."""
    if pd.isna(valor):
        return None
    try:
        return pd.to_datetime(valor, dayfirst=True).date()
    except Exception:
        try:
            return datetime.strptime(str(valor), "%d/%m/%Y").date()
        except Exception:
            return None


def detectar_tipo(descripcion):
    """Detecta si es CLAVE o VISA según la descripción."""
    if not isinstance(descripcion, str):
        return "OTRO"
    desc = descripcion.upper().strip()
    # Revisar VISA primero
    if "T/C" in desc or "TC" in desc or "TARJETA" in desc:
        return "VISA"
    elif "POS" in desc:
        return "CLAVE"
    else:
        return "OTRO"


def extraer_codigo(descripcion):
    """Extrae el número terminal tipo 908068171 de la descripción (últimos 9 dígitos)."""
    if not isinstance(descripcion, str):
        return None
    # Buscar todos los grupos de 9 dígitos seguidos
    matches = re.findall(r"(\d{9})", descripcion)
    if matches:
        return matches[-1]  # tomar el último grupo
    return None


# 🔥 Normalizar nombre de sucursal
def normalizar_sucursal(nombre):
    """Normaliza el nombre de la sucursal para comparación."""
    if not nombre:
        return ""
    return str(nombre).strip().upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")


# --- Endpoint principal ---
@router.post("/banco_preview")
async def banco_preview(
    file: UploadFile = File(...),
    fecha_cierre: str = Form(None),  # 🔥 NUEVO: Fecha del cierre
    sucursal_cierre: str = Form(None)  # 🔥 NUEVO: Sucursal del cierre
):
    """
    Lee el archivo de movimientos bancarios (CLAVE/VISA),
    limpia y filtra por fecha y sucursal del cierre.
    """
    try:
        print(f"📥 Recibido archivo banco: {file.filename}")
        print(f"📅 Fecha del cierre: {fecha_cierre}")
        print(f"🏢 Sucursal del cierre: {sucursal_cierre}")

        # Leer contenido del Excel subido
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo vacío o no recibido.")

        # Leer hoja principal con encabezados en la fila 7
        df = pd.read_excel(io.BytesIO(content), header=6, engine="openpyxl")

        # Normalizar nombres de columnas (por si varían en tildes o mayúsculas)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Verificar columnas mínimas necesarias
        required_cols = ["fecha", "descripción", "crédito"]
        if not all(any(rc in c for c in df.columns) for rc in required_cols):
            raise HTTPException(status_code=400, detail="No se encontraron las columnas requeridas: Fecha, Descripción, Crédito")

        # Extraer columnas relevantes
        col_fecha = next(c for c in df.columns if "fecha" in c)
        col_desc = next(c for c in df.columns if "descr" in c)
        col_credito = next(c for c in df.columns if "crédit" in c or "credit" in c)

        df_proc = df[[col_fecha, col_desc, col_credito]].copy()
        df_proc.columns = ["fecha", "descripcion", "monto"]

        # Limpiar columnas
        df_proc["fecha"] = df_proc["fecha"].apply(limpiar_fecha)
        df_proc["monto"] = df_proc["monto"].apply(limpiar_monto)
        df_proc["tipo"] = df_proc["descripcion"].apply(detectar_tipo)
        df_proc["codigo"] = df_proc["descripcion"].apply(extraer_codigo)

        # Filtrar solo CLAVE o VISA
        df_proc = df_proc[df_proc["tipo"].isin(["CLAVE", "VISA"])]
        
        # Eliminar filas sin código
        df_proc = df_proc[df_proc["codigo"].astype(str).str.match(r"^\d{9}$")]

        # Eliminar filas vacías o sin monto
        df_proc = df_proc[df_proc["monto"].notna()]
        df_proc = df_proc[df_proc["fecha"].notna()]
        df_proc = df_proc[df_proc["descripcion"].notna()]

        print(f"📊 Total registros después de limpieza: {len(df_proc)}")

        # --- Cargar lista de puntos de venta ---
        lista_path = Path("data/Lista_Punto_Venta.xlsx")
        try:
            lista_df = pd.read_excel(lista_path, engine="openpyxl")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo leer Lista_Punto_Venta.xlsx: {e}")

        lista_df.columns = [str(c).strip().upper() for c in lista_df.columns]

        # Extraer mapa {codigo: sucursal}
        lista_df["CODIGO"] = lista_df["NÚMERO DE PUNTO DE VENTA"].astype(str).apply(extraer_codigo)
        map_suc = dict(zip(lista_df["CODIGO"], lista_df["SUCURSAL"]))

        # Asignar sucursal
        df_proc["sucursal"] = df_proc["codigo"].map(map_suc).fillna("DESCONOCIDO")

        # 🔥 FILTRAR POR FECHA DEL CIERRE
        if fecha_cierre:
            # Convertir fecha del cierre a date object
            try:
                # Intentar DD/MM/YYYY
                fecha_obj = datetime.strptime(fecha_cierre, "%d/%m/%Y").date()
            except:
                try:
                    # Intentar YYYY-MM-DD
                    fecha_obj = datetime.strptime(fecha_cierre, "%Y-%m-%d").date()
                except:
                    print(f"⚠️ No se pudo parsear la fecha del cierre: {fecha_cierre}")
                    fecha_obj = None
            
            if fecha_obj:
                antes_fecha = len(df_proc)
                df_proc = df_proc[df_proc["fecha"] == fecha_obj]
                print(f"✅ Filtrado por fecha {fecha_obj}: {len(df_proc)} de {antes_fecha} registros")

        # 🔥 FILTRAR POR SUCURSAL DEL CIERRE
        if sucursal_cierre:
            sucursal_norm = normalizar_sucursal(sucursal_cierre)
            df_proc["sucursal_norm"] = df_proc["sucursal"].apply(normalizar_sucursal)
            
            antes_sucursal = len(df_proc)
            df_proc = df_proc[df_proc["sucursal_norm"] == sucursal_norm]
            print(f"✅ Filtrado por sucursal '{sucursal_cierre}': {len(df_proc)} de {antes_sucursal} registros")
            
            # Eliminar columna temporal
            df_proc = df_proc.drop(columns=["sucursal_norm"])

        # Limpiar duplicados y resetear índice
        df_proc = df_proc.drop_duplicates().reset_index(drop=True)

        # Convertir fechas a string para serialización JSON
        df_proc["fecha"] = df_proc["fecha"].astype(str)

        # Retornar todos los resultados filtrados (sin límite)
        preview = df_proc.to_dict(orient="records")

        return {
            "ok": True,
            "message": f"Archivo procesado: {len(preview)} registros coinciden",
            "total_registros": len(preview),
            "preview": preview,
            "filtros": {
                "fecha": fecha_cierre,
                "sucursal": sucursal_cierre
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error procesando archivo bancario: {e}")