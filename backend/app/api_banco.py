# backend/app/api_banco.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import pandas as pd
import io
import re
import traceback
from datetime import datetime
from pathlib import Path
from app.utils.file_reader import read_file, detect_file_type
from app.utils.validators import clean_amount, clean_date, validate_dataframe, normalize_text

router = APIRouter()

# --- Funciones auxiliares ---

# Usar funciones de validación centralizadas
limpiar_monto = clean_amount

def detectar_header_row(content, filename, columnas_esperadas=None):
    """
    Detecta automáticamente la fila del header buscando las columnas esperadas.
    
    Args:
        content: Contenido del archivo en bytes
        filename: Nombre del archivo
        columnas_esperadas: Lista de nombres de columnas a buscar (case-insensitive)
    
    Returns:
        Número de fila del header (0-indexed) o None si no se encuentra
    """
    if columnas_esperadas is None:
        columnas_esperadas = ["fecha", "descripcion", "credito", "descripción", "crédito"]
    
    # Intentar leer las primeras 20 filas sin header para buscar
    for header_row in range(20):
        try:
            df_temp = read_file(content, filename, header=header_row)
            
            # Normalizar nombres de columnas
            cols_lower = [str(c).strip().lower() for c in df_temp.columns]
            
            # Verificar si contiene las columnas esperadas
            coincidencias = sum(1 for col_esperada in columnas_esperadas 
                              if any(col_esperada in col for col in cols_lower))
            
            # Si encontramos al menos 2 columnas esperadas, este es el header
            if coincidencias >= 2:
                print(f"✅ Header detectado en fila {header_row + 1} (índice {header_row})")
                return header_row
        except:
            continue
    
    # Si no se encuentra, asumir fila 6 (comportamiento original)
    print(f"⚠️ No se detectó header automáticamente, usando fila 7 (índice 6) por defecto")
    return 6

def limpiar_fecha(valor):
    """Convierte fecha a date object."""
    fecha_str = clean_date(valor)
    if fecha_str:
        try:
            return datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except:
            return None
    return None


def detectar_tipo(descripcion):
    """Detecta si es CLAVE o VISA según la descripción."""
    if not isinstance(descripcion, str):
        return "OTRO"
    desc = descripcion.upper().strip()
    # Revisar VISA primero
    if "T/C" in desc or "TC" in desc or "TARJETA" in desc:
        return "VISA"
    # Buscar POS como palabra completa (word boundary) para evitar falsos positivos como "Deposito"
    elif re.search(r'\bPOS\b', desc):
        return "CLAVE"
    else:
        return "OTRO"


def extraer_codigo(descripcion):
    """
    Extrae el número terminal de 9 dígitos de la descripción.
    Busca específicamente después de palabras clave como POS, TERM, TERMINAL.
    Si no las encuentra, toma los últimos 9 dígitos como fallback.
    """
    if not isinstance(descripcion, str):
        return None
    
    desc = descripcion.upper()
    
    # Intento 1: Buscar después de palabras clave específicas
    match = re.search(r'(?:POS|TERM(?:INAL)?)\s*[:#]?\s*(\d{9})', desc, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Intento 2: Buscar patrón con guiones o espacios (ej: 908-068-171 o 908 068 171)
    match = re.search(r'(\d{3})[-\s]?(\d{3})[-\s]?(\d{3})', desc)
    if match:
        return ''.join(match.groups())
    
    # Intento 3 (Fallback): Buscar cualquier secuencia de 9 dígitos (comportamiento original)
    matches = re.findall(r'\b(\d{9})\b', desc)  # \b = word boundary para ser más preciso
    if matches:
        return matches[-1]  # tomar el último grupo
    
    return None


# 🔥 Normalizar nombre de sucursal
# Usar función de validación centralizada
normalizar_sucursal = normalize_text


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

        # Leer contenido del archivo subido
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo vacío o no recibido.")

        filename = file.filename or "archivo.xlsx"
        
        # 🔥 DETECTAR HEADER AUTOMÁTICAMENTE
        header_row = detectar_header_row(content, filename)
        df = read_file(content, filename, header=header_row)

        # Normalizar nombres de columnas (por si varían en tildes o mayúsculas)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Verificar columnas mínimas necesarias
        required_cols = ["fecha", "descripción", "crédito"]
        is_valid, error_msg = validate_dataframe(df, required_cols, min_rows=1)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg or "El archivo no tiene el formato esperado")

        # Extraer columnas relevantes
        col_fecha = next(c for c in df.columns if "fecha" in c)
        col_desc = next(c for c in df.columns if "descr" in c)
        col_credito = next(c for c in df.columns if "crédit" in c or "credit" in c)

        df_proc = df[[col_fecha, col_desc, col_credito]].copy()
        df_proc.columns = ["fecha", "descripcion", "monto"]

        # Limpiar columnas
        df_proc["fecha"] = df_proc["fecha"].apply(limpiar_fecha)
        print(f"📊 Fechas originales (primeras 5): {df_proc['fecha'].head(5).tolist()}")
        
        # 🔥 AJUSTAR FECHA: El banco registra transacciones al día siguiente
        # Por ejemplo: una venta del 14/11 aparece en el banco el 15/11
        # Restamos 1 día para que coincida con la fecha real de la transacción
        from datetime import timedelta
        df_proc["fecha"] = df_proc["fecha"].apply(lambda x: x - timedelta(days=1) if x else None)
        print(f"📊 Fechas ajustadas (-1 día, primeras 5): {df_proc['fecha'].head(5).tolist()}")
        
        df_proc["monto"] = df_proc["monto"].apply(limpiar_monto)
        df_proc["tipo"] = df_proc["descripcion"].apply(detectar_tipo)
        df_proc["codigo"] = df_proc["descripcion"].apply(extraer_codigo)

        # Filtrar solo CLAVE o VISA
        df_proc = df_proc[df_proc["tipo"].isin(["CLAVE", "VISA"])]
        
        # Eliminar filas sin código
        df_proc = df_proc[df_proc["codigo"].astype(str).str.match(r"^\d{9}$")]

        # Eliminar filas vacías o sin monto
        antes_filtrado = len(df_proc)
        df_proc = df_proc[
            df_proc["monto"].notna() & 
            df_proc["fecha"].notna() & 
            df_proc["descripcion"].notna()
        ]
        print(f"📊 Filas después de limpieza: {len(df_proc)} de {antes_filtrado}")
        
        if df_proc.empty:
            raise HTTPException(
                status_code=400, 
                detail="No se encontraron registros válidos después de la limpieza. Verifica que el archivo tenga datos en las columnas Fecha, Descripción y Crédito."
            )

        print(f"📊 Total registros después de limpieza: {len(df_proc)}")

        # --- Cargar lista de puntos de venta ---
        # Buscar el archivo en diferentes ubicaciones posibles
        posibles_rutas = [
            Path("data/Lista_Punto_Venta.xlsx"),
            Path("app/data/Lista_Punto_Venta.xlsx"),
            Path("../data/Lista_Punto_Venta.xlsx"),
            Path("/app/data/Lista_Punto_Venta.xlsx"),
            Path("/app/app/data/Lista_Punto_Venta.xlsx"),
        ]
        lista_path = None
        for ruta in posibles_rutas:
            if ruta.exists():
                lista_path = ruta
                break
        
        if not lista_path:
            # Intentar buscar en el directorio actual y subdirectorios
            import os
            for root, dirs, files in os.walk("."):
                if "Lista_Punto_Venta.xlsx" in files:
                    lista_path = Path(root) / "Lista_Punto_Venta.xlsx"
                    break
        
        if not lista_path:
            raise HTTPException(status_code=500, detail="No se encontró el archivo Lista_Punto_Venta.xlsx")
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
            print(f"🔍 DEBUG: Fecha cierre recibida: '{fecha_cierre}' (tipo: {type(fecha_cierre).__name__})")
            # Convertir fecha del cierre a date object
            try:
                # Intentar DD/MM/YYYY
                fecha_obj = datetime.strptime(fecha_cierre, "%d/%m/%Y").date()
                print(f"✅ Fecha parseada como DD/MM/YYYY: {fecha_obj}")
            except Exception as e1:
                print(f"⚠️ No se pudo parsear como DD/MM/YYYY: {e1}")
                try:
                    # Intentar YYYY-MM-DD
                    fecha_obj = datetime.strptime(fecha_cierre, "%Y-%m-%d").date()
                    print(f"✅ Fecha parseada como YYYY-MM-DD: {fecha_obj}")
                except Exception as e2:
                    print(f"❌ No se pudo parsear la fecha del cierre: {fecha_cierre}")
                    print(f"   Error DD/MM/YYYY: {e1}")
                    print(f"   Error YYYY-MM-DD: {e2}")
                    fecha_obj = None
            
            if fecha_obj:
                antes_fecha = len(df_proc)
                # Intentar primero con fecha exacta
                df_filtrado = df_proc[df_proc["fecha"] == fecha_obj]
                
                # 🔥 Si no encuentra registros, buscar en rango de hasta 4 días
                if len(df_filtrado) == 0:
                    print(f"⚠️ No se encontraron registros bancarios para {fecha_obj}")
                    print(f"   Buscando en rango de hasta 4 días...")
                    
                    fecha_inicio = fecha_obj
                    fecha_fin = fecha_obj + timedelta(days=4)
                    
                    df_filtrado = df_proc[
                        (df_proc["fecha"] >= fecha_inicio) & 
                        (df_proc["fecha"] <= fecha_fin)
                    ]
                    
                    if len(df_filtrado) > 0:
                        fechas_encontradas = sorted(df_filtrado["fecha"].unique())
                        print(f"✅ Encontrados {len(df_filtrado)} registros en rango {fecha_inicio} a {fecha_fin}")
                        print(f"   Fechas con registros: {fechas_encontradas}")
                    else:
                        print(f"❌ No se encontraron registros ni en el rango de 4 días")
                else:
                    print(f"✅ Filtrado por fecha {fecha_obj}: {len(df_filtrado)} de {antes_fecha} registros")
                
                df_proc = df_filtrado

        # 🔥 MARCAR SUCURSAL DEL CIERRE (en lugar de filtrar estrictamente)
        if sucursal_cierre:
            # Mostrar qué sucursales se detectaron
            sucursales_detectadas = df_proc["sucursal"].value_counts()
            print(f"🏢 Sucursales detectadas en los registros filtrados por fecha:")
            for suc, count in sucursales_detectadas.items():
                print(f"   - {suc}: {count} registros")
            
            sucursal_norm = normalizar_sucursal(sucursal_cierre)
            print(f"🔍 Sucursal del cierre normalizada: '{sucursal_norm}' (original: '{sucursal_cierre}')")
            
            df_proc["sucursal_norm"] = df_proc["sucursal"].apply(normalizar_sucursal)
            
            # Marcar si coincide con la sucursal del cierre (en lugar de filtrar)
            df_proc["es_sucursal_cierre"] = df_proc["sucursal_norm"] == sucursal_norm
            
            coinciden = df_proc["es_sucursal_cierre"].sum()
            total = len(df_proc)
            
            print(f"✅ Registros que coinciden con '{sucursal_cierre}': {coinciden} de {total}")
            
            if coinciden == 0:
                print(f"⚠️ ADVERTENCIA: Ningún registro coincide con la sucursal '{sucursal_cierre}'")
                print(f"   Mostrando TODOS los {total} registros de la fecha")
                print(f"   Sucursales encontradas: {list(sucursales_detectadas.index)}")
            
            # NO filtrar, mostrar todos pero marcados
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
    except ValueError as e:
        # Errores de formato o validación
        traceback.print_exc()
        raise HTTPException(
            status_code=400, 
            detail=f"Error en el formato del archivo: {str(e)}"
        )
    except Exception as e:
        traceback.print_exc()
        error_msg = f"Error procesando archivo bancario: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(
            status_code=500, 
            detail=error_msg
        )