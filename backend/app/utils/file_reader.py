"""
Utilidades para leer archivos Excel y CSV de manera unificada.
Soporta múltiples formatos y es robusto ante cambios en la estructura de los archivos.
"""
import pandas as pd
import io
from typing import Union, Optional, List
import traceback


def detect_file_type(filename: str) -> str:
    """
    Detecta el tipo de archivo basándose en la extensión.
    Soporta: CSV, Excel (.xlsx, .xls, .xlsm, .xlsb), ODS
    """
    filename_lower = filename.lower()
    
    # Formatos CSV
    if filename_lower.endswith('.csv'):
        return 'csv'
    
    # Formatos Excel modernos (requieren openpyxl)
    elif filename_lower.endswith(('.xlsx', '.xlsm')):
        return 'excel_openpyxl'
    
    # Formatos Excel antiguos (requieren xlrd)
    elif filename_lower.endswith('.xls'):
        return 'excel_xlrd'
    
    # Excel binario (requiere pyxlsb)
    elif filename_lower.endswith('.xlsb'):
        return 'excel_xlsb'
    
    # OpenDocument Spreadsheet (requiere odfpy)
    elif filename_lower.endswith('.ods'):
        return 'ods'
    
    else:
        supported = '.csv, .xlsx, .xls, .xlsm, .xlsb, .ods'
        raise ValueError(
            f"Formato de archivo no soportado: {filename}. "
            f"Formatos soportados: {supported}"
        )


def read_file(
    content: bytes,
    filename: str,
    sheet_name: Optional[Union[str, int]] = None,
    header: Optional[int] = None,
    engine: str = "openpyxl"
) -> pd.DataFrame:
    """
    Lee un archivo Excel o CSV y retorna un DataFrame.
    Intenta múltiples métodos y engines para maximizar compatibilidad.
    
    Args:
        content: Contenido del archivo en bytes
        filename: Nombre del archivo (para detectar tipo)
        sheet_name: Nombre o índice de la hoja (solo para Excel)
        header: Fila a usar como encabezado (None = sin encabezado)
        engine: Motor a usar para Excel (openpyxl por defecto)
    
    Returns:
        DataFrame de pandas
    
    Raises:
        ValueError: Con mensaje específico sobre qué falló y cómo solucionarlo
    """
    if not content or len(content) == 0:
        raise ValueError("El archivo está vacío o no se recibió contenido")
    
    file_type = detect_file_type(filename)
    errors = []  # Para acumular errores y dar mensaje detallado
    
    if file_type == 'csv':
        # Para CSV, intentar detectar el delimitador y encoding
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t', '|']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(
                        io.BytesIO(content),
                        header=header,
                        encoding=encoding,
                        sep=sep,
                        skipinitialspace=True,
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if not df.empty:
                        return df
                except Exception as e:
                    errors.append(f"Encoding {encoding}, separador '{sep}': {str(e)}")
                    continue
        
        raise ValueError(
            f"No se pudo leer el archivo CSV '{filename}'. "
            f"Se intentaron múltiples encodings ({', '.join(encodings)}) y separadores ({', '.join(separators)}). "
            f"Verifica que el archivo esté en formato CSV válido. "
            f"Errores: {'; '.join(errors[:3])}"
        )
    
    elif file_type.startswith('excel') or file_type == 'ods':
        # Lista de engines a intentar en orden de preferencia
        engines_to_try = []
        
        if file_type == 'excel_xlrd':
            engines_to_try = ['xlrd', 'openpyxl', 'calamine']
        elif file_type == 'excel_openpyxl':
            engines_to_try = ['openpyxl', 'calamine', 'xlrd']
        elif file_type == 'excel_xlsb':
            engines_to_try = ['pyxlsb', 'openpyxl']
        elif file_type == 'ods':
            engines_to_try = ['odf', 'openpyxl']
        else:
            engines_to_try = ['openpyxl', 'xlrd', 'calamine']
        
        # Intentar con cada engine
        last_error = None
        for excel_engine in engines_to_try:
            try:
                if sheet_name is not None:
                    df = pd.read_excel(
                        io.BytesIO(content),
                        sheet_name=sheet_name,
                        header=header,
                        engine=excel_engine
                    )
                else:
                    df = pd.read_excel(
                        io.BytesIO(content),
                        header=header,
                        engine=excel_engine
                    )
                
                if df is not None and not df.empty:
                    return df
                elif df is not None and df.empty:
                    # DataFrame vacío pero válido - puede ser que el header esté mal
                    continue
                    
            except ImportError as e:
                error_msg = f"Engine '{excel_engine}' no está instalado"
                errors.append(error_msg)
                print(f"⚠️ {error_msg}: {str(e)}")
                continue
            except Exception as e:
                error_msg = f"Error con engine '{excel_engine}': {str(e)}"
                errors.append(error_msg)
                last_error = e
                print(f"⚠️ {error_msg}")
                continue
        
        # Si llegamos aquí, todos los engines fallaron
        if file_type == 'excel_xlsb':
            raise ValueError(
                f"No se pudo leer el archivo .xlsb '{filename}'. "
                f"El formato Excel binario (.xlsb) requiere la librería 'pyxlsb'. "
                f"Instala con: pip install pyxlsb. "
                f"O convierte el archivo a .xlsx. "
                f"Errores: {'; '.join(errors[:3])}"
            ) from last_error
        elif file_type == 'ods':
            raise ValueError(
                f"No se pudo leer el archivo .ods '{filename}'. "
                f"El formato OpenDocument requiere la librería 'odfpy'. "
                f"Instala con: pip install odfpy. "
                f"O convierte el archivo a .xlsx. "
                f"Errores: {'; '.join(errors[:3])}"
            ) from last_error
        else:
            raise ValueError(
                f"No se pudo leer el archivo Excel '{filename}'. "
                f"Se intentaron los engines: {', '.join(engines_to_try)}. "
                f"Posibles causas: archivo corrupto, formato no soportado, o falta instalar librerías. "
                f"Verifica que el archivo sea un Excel válido (.xlsx, .xls, .xlsm). "
                f"Errores: {'; '.join(errors[:3])}"
            ) from last_error
    
    else:
        supported = '.csv, .xlsx, .xls, .xlsm, .xlsb, .ods'
        raise ValueError(
            f"Tipo de archivo no soportado: {file_type}. "
            f"Formatos soportados: {supported}"
        )


def get_excel_sheets(content: bytes, filename: str = "archivo.xlsx") -> List[str]:
    """
    Obtiene la lista de hojas disponibles en un archivo Excel/ODS.
    Intenta múltiples engines para maximizar compatibilidad.
    Retorna lista vacía si no es Excel/ODS o hay error.
    """
    if not content or len(content) == 0:
        return []
    
    try:
        file_type = detect_file_type(filename)
        
        if not (file_type.startswith('excel') or file_type == 'ods'):
            return []
        
        # Lista de engines a intentar
        engines_to_try = []
        if file_type == 'excel_xlrd':
            engines_to_try = ['xlrd', 'openpyxl', 'calamine']
        elif file_type == 'excel_openpyxl':
            engines_to_try = ['openpyxl', 'calamine', 'xlrd']
        elif file_type == 'excel_xlsb':
            engines_to_try = ['pyxlsb', 'openpyxl']
        elif file_type == 'ods':
            engines_to_try = ['odf', 'openpyxl']
        else:
            engines_to_try = ['openpyxl', 'xlrd', 'calamine']
        
        # Intentar con cada engine
        for engine in engines_to_try:
            try:
                xls = pd.ExcelFile(io.BytesIO(content), engine=engine)
                if xls.sheet_names:
                    return xls.sheet_names
            except ImportError:
                continue
            except Exception:
                continue
        
        return []
    except Exception as e:
        print(f"⚠️ Error obteniendo hojas de '{filename}': {str(e)}")
        return []

