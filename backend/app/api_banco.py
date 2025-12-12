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
    Es robusto ante cambios en la estructura del Excel.
    
    Args:
        content: Contenido del archivo en bytes
        filename: Nombre del archivo
        columnas_esperadas: Lista de nombres de columnas a buscar (case-insensitive)
    
    Returns:
        Número de fila del header (0-indexed) o None si no se encuentra
    """
    if columnas_esperadas is None:
        # Variaciones comunes de nombres de columnas
        columnas_esperadas = [
            "fecha", "date", "fecha movimiento", "fecha de movimiento",
            "descripcion", "descripción", "desc", "concepto", "detalle", "movimiento",
            "credito", "crédito", "credit", "monto", "importe", "valor", "cantidad",
            "debito", "débito", "debit"
        ]
    
    # Intentar leer las primeras 30 filas para buscar el header
    mejor_coincidencia = None
    mejor_score = 0
    
    for header_row in range(30):
        try:
            df_temp = read_file(content, filename, sheet_name=0, header=header_row)  # Siempre usar hoja 1
            
            if df_temp.empty or len(df_temp.columns) < 2:
                continue
            
            # Normalizar nombres de columnas
            cols_lower = [str(c).strip().lower() for c in df_temp.columns]
            
            # Verificar si contiene las columnas esperadas
            coincidencias = 0
            for col_esperada in columnas_esperadas:
                for col in cols_lower:
                    # Buscar coincidencias exactas o parciales
                    if col_esperada == col or col_esperada in col or col in col_esperada:
                        coincidencias += 1
                        break
            
            # Calcular score: más columnas coincidentes = mejor
            # También considerar si hay datos válidos en las primeras filas
            score = coincidencias
            if len(df_temp) > 0:
                # Verificar que haya datos no vacíos
                non_empty_rows = df_temp.dropna(how='all').shape[0]
                if non_empty_rows > 0:
                    score += 1
            
            # Si encontramos al menos 2 columnas esperadas, considerar este header
            if coincidencias >= 2 and score > mejor_score:
                mejor_score = score
                mejor_coincidencia = header_row
                
        except Exception as e:
            # Continuar con la siguiente fila si hay error
            continue
    
    if mejor_coincidencia is not None:
        print(f"✅ Header detectado en fila {mejor_coincidencia + 1} (índice {mejor_coincidencia}) con score {mejor_score}")
        return mejor_coincidencia
    
    # Si no se encuentra, intentar con filas comunes (6, 0, 1)
    filas_comunes = [6, 0, 1, 2, 3]
    for fila in filas_comunes:
        try:
            df_temp = read_file(content, filename, sheet_name=0, header=fila)  # Siempre usar hoja 1
            if not df_temp.empty and len(df_temp.columns) >= 2:
                print(f"⚠️ No se detectó header automáticamente, usando fila {fila + 1} (índice {fila}) por defecto")
                return fila
        except:
            continue
    
    # Último recurso: fila 0
    print(f"⚠️ Usando fila 1 (índice 0) como último recurso")
    return 0

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
    Busca TODOS los códigos de 9 dígitos y valida cuál es el código de terminal.
    Ejemplo: 'DEPOSITO POS-070800001908068184' tiene dos códigos,
    pero 908068184 es el terminal (empieza con 90).
    """
    if not isinstance(descripcion, str):
        return None
    
    desc = descripcion.upper()
    
    # Primero buscar patrones con guiones o espacios (ej: 908-068-171 o 908 068 171)
    match_guiones = re.search(r'(\d{3})[-\s](\d{3})[-\s](\d{3})', desc)
    if match_guiones:
        codigo_con_guiones = ''.join(match_guiones.groups())
        # Verificar si empieza con 90 o 91 (códigos de terminales)
        if codigo_con_guiones.startswith(('90', '91')):
            return codigo_con_guiones
    
    # Buscar TODOS los números de 9 dígitos en la descripción
    todos_codigos = re.findall(r'\b(\d{9})\b', desc)
    
    if not todos_codigos:
        # Si no encuentra con word boundary, buscar sin boundary
        # Útil para casos como "POS-070800001908068184" donde están pegados
        todos_codigos = re.findall(r'(\d{9})', desc)
    
    # Si encontramos código con guiones y no empieza con 90/91, agregarlo a la lista
    if match_guiones and match_guiones.group(0) not in todos_codigos:
        todos_codigos.append(''.join(match_guiones.groups()))
    
    if not todos_codigos:
        return None
    
    # Si solo hay uno, retornarlo
    if len(todos_codigos) == 1:
        return todos_codigos[0]
    
    # 🔥 Si hay múltiples, preferir los que empiezan con 90 o 91 (patrón común de terminales)
    codigos_terminales = [c for c in todos_codigos if c.startswith(('90', '91'))]
    
    if len(codigos_terminales) == 1:
        return codigos_terminales[0]
    elif len(codigos_terminales) > 1:
        # Si hay múltiples que empiezan con 90/91, tomar el último (más a la derecha)
        return codigos_terminales[-1]
    
    # Fallback: tomar el último código encontrado (más a la derecha en la descripción)
    return todos_codigos[-1]


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
        # Siempre usar la primera hoja (índice 0 o nombre "Sheet1")
        header_row = detectar_header_row(content, filename)
        df = read_file(content, filename, sheet_name=0, header=header_row)  # sheet_name=0 = primera hoja

        # Normalizar nombres de columnas (por si varían en tildes o mayúsculas)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        print(f"📋 Columnas detectadas: {list(df.columns)}")

        # Verificar columnas mínimas necesarias con variaciones
        # Buscar columnas de manera flexible
        col_fecha = None
        col_desc = None
        col_credito = None
        
        # Buscar columna de fecha (múltiples variaciones)
        for col in df.columns:
            col_lower = str(col).lower()
            if not col_fecha and any(x in col_lower for x in ["fecha", "date"]):
                col_fecha = col
                break
        
        # Buscar columna de descripción (múltiples variaciones)
        for col in df.columns:
            col_lower = str(col).lower()
            if not col_desc and any(x in col_lower for x in ["descripcion", "descripción", "desc", "concepto", "detalle", "movimiento"]):
                col_desc = col
                break
        
        # Buscar columna de crédito/monto (múltiples variaciones)
        for col in df.columns:
            col_lower = str(col).lower()
            if not col_credito and any(x in col_lower for x in ["credito", "crédito", "credit", "monto", "importe", "valor"]):
                col_credito = col
                break
        
        # Validar que se encontraron las columnas necesarias
        missing_cols = []
        if not col_fecha:
            missing_cols.append("Fecha (o Date)")
        if not col_desc:
            missing_cols.append("Descripción (o Concepto/Detalle)")
        if not col_credito:
            missing_cols.append("Crédito (o Monto/Importe)")
        
        if missing_cols:
            columnas_disponibles = ", ".join(df.columns)
            raise HTTPException(
                status_code=400,
                detail=f"El archivo no tiene el formato esperado. Faltan las siguientes columnas: {', '.join(missing_cols)}. "
                       f"Columnas disponibles en el archivo: {columnas_disponibles}. "
                       f"Verifica que el archivo contenga columnas de Fecha, Descripción y Crédito/Monto."
            )
        
        # Validar que el DataFrame tenga datos
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío o no contiene datos. Verifica que el archivo tenga filas de datos."
            )
        
        print(f"✅ Columnas encontradas: Fecha='{col_fecha}', Descripción='{col_desc}', Crédito='{col_credito}'")

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
        
        # 🔍 DEBUG: Mostrar códigos que no se pudieron mapear
        desconocidos = df_proc[df_proc["sucursal"] == "DESCONOCIDO"]
        if len(desconocidos) > 0:
            codigos_desconocidos = desconocidos["codigo"].unique()
            print(f"⚠️ {len(desconocidos)} registros con sucursal DESCONOCIDO")
            print(f"   Códigos no mapeados: {list(codigos_desconocidos)[:10]}")  # Primeros 10
            print(f"   Ejemplo de descripción: {desconocidos.iloc[0]['descripcion']}")

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

        # 🔥 FILTRAR POR SUCURSAL DEL CIERRE
        if sucursal_cierre:
            # Mostrar qué sucursales se detectaron ANTES de filtrar
            sucursales_detectadas = df_proc["sucursal"].value_counts()
            print(f"🏢 Sucursales detectadas en los registros filtrados por fecha:")
            for suc, count in sucursales_detectadas.items():
                print(f"   - {suc}: {count} registros")
            
            sucursal_norm = normalizar_sucursal(sucursal_cierre)
            print(f"🔍 Filtrando por sucursal normalizada: '{sucursal_norm}' (original: '{sucursal_cierre}')")
            
            df_proc["sucursal_norm"] = df_proc["sucursal"].apply(normalizar_sucursal)
            
            antes_sucursal = len(df_proc)
            # 🔥 FILTRAR: Mostrar SOLO los de la sucursal del cierre
            df_proc = df_proc[df_proc["sucursal_norm"] == sucursal_norm]
            
            print(f"✅ Filtrado por sucursal '{sucursal_cierre}': {len(df_proc)} de {antes_sucursal} registros")
            
            if len(df_proc) == 0:
                print(f"⚠️ ADVERTENCIA: No se encontraron registros para la sucursal '{sucursal_cierre}'")
                print(f"   Sucursales disponibles en esa fecha: {list(sucursales_detectadas.index)}")
            else:
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
    except ValueError as e:
        # Errores de formato o validación
        error_msg = str(e)
        traceback.print_exc()
        
        # Hacer el mensaje más específico según el tipo de error
        if "no se pudo leer" in error_msg.lower() or "no está soportado" in error_msg.lower():
            detail_msg = (
                f"Error al leer el archivo: {error_msg}. "
                f"Verifica que el archivo sea un Excel válido (.xlsx, .xls, .xlsm) o CSV. "
                f"Si el archivo está corrupto, intenta abrirlo en Excel y guardarlo nuevamente."
            )
        elif "vacío" in error_msg.lower() or "empty" in error_msg.lower():
            detail_msg = (
                f"El archivo está vacío o no contiene datos válidos. "
                f"Verifica que el archivo tenga filas de datos después de los encabezados."
            )
        elif "columnas" in error_msg.lower() or "columns" in error_msg.lower():
            detail_msg = error_msg
        else:
            detail_msg = f"Error en el formato del archivo: {error_msg}. Verifica que el archivo tenga el formato correcto."
        
        raise HTTPException(status_code=400, detail=detail_msg)
    except Exception as e:
        traceback.print_exc()
        error_type = type(e).__name__
        error_msg = str(e)
        
        # Mensajes más específicos según el tipo de error
        if "FileNotFoundError" in error_type or "No such file" in error_msg:
            detail_msg = (
                f"Error: No se encontró un archivo necesario. "
                f"Verifica que todos los archivos requeridos estén disponibles. "
                f"Error original: {error_msg}"
            )
        elif "PermissionError" in error_type:
            detail_msg = (
                f"Error de permisos: No se puede acceder al archivo. "
                f"Verifica los permisos del archivo. Error: {error_msg}"
            )
        elif "MemoryError" in error_type:
            detail_msg = (
                f"Error de memoria: El archivo es demasiado grande para procesar. "
                f"Intenta con un archivo más pequeño o divide los datos. Error: {error_msg}"
            )
        else:
            detail_msg = (
                f"Error procesando archivo bancario: {error_msg} "
                f"(Tipo: {error_type}). "
                f"Verifica que el archivo sea válido y tenga el formato correcto. "
                f"Si el problema persiste, contacta al administrador."
            )
        
        print(f"❌ {detail_msg}")
        raise HTTPException(status_code=500, detail=detail_msg)