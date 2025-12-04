"""
Utilidades para leer archivos Excel y CSV de manera unificada.
"""
import pandas as pd
import io
from typing import Union, Optional


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
    
    Args:
        content: Contenido del archivo en bytes
        filename: Nombre del archivo (para detectar tipo)
        sheet_name: Nombre o índice de la hoja (solo para Excel)
        header: Fila a usar como encabezado (None = sin encabezado)
        engine: Motor a usar para Excel (openpyxl por defecto)
    
    Returns:
        DataFrame de pandas
    """
    file_type = detect_file_type(filename)
    engine_override = None
    
    # Determinar el engine según el tipo de archivo
    if file_type == 'excel_xlrd':
        # Para .xls antiguo, intentar primero con xlrd, luego openpyxl
        engine_override = 'xlrd'
    elif file_type == 'excel_openpyxl':
        engine_override = 'openpyxl'
    elif file_type == 'excel_xlsb':
        # xlsb requiere pyxlsb, pero pandas no lo soporta directamente
        # Intentar sin engine específico, si falla dar error claro
        engine_override = None
    elif file_type == 'ods':
        # ODS requiere odfpy
        engine_override = 'odf'
    
    if file_type == 'csv':
        # Para CSV, intentar detectar el delimitador y encoding
        try:
            # Intentar con encoding UTF-8 primero
            df = pd.read_csv(
                io.BytesIO(content),
                header=header,
                encoding='utf-8',
                sep=',',
                skipinitialspace=True,
                on_bad_lines='skip'
            )
        except UnicodeDecodeError:
            # Si falla, intentar con latin-1
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    header=header,
                    encoding='latin-1',
                    sep=',',
                    skipinitialspace=True,
                    on_bad_lines='skip'
                )
            except Exception:
                # Último intento con diferentes delimitadores
                for sep in [';', '\t', '|']:
                    try:
                        df = pd.read_csv(
                            io.BytesIO(content),
                            header=header,
                            encoding='utf-8',
                            sep=sep,
                            skipinitialspace=True,
                            on_bad_lines='skip'
                        )
                        break
                    except:
                        continue
                else:
                    raise ValueError(
                        "No se pudo leer el archivo CSV. "
                        "Verifica que el archivo esté en formato CSV válido con delimitador ',' o ';'."
                    )
        
        if df.empty:
            raise ValueError("El archivo CSV está vacío o no contiene datos válidos")
        
        return df
    
    elif file_type.startswith('excel') or file_type == 'ods':
        # Para Excel y ODS, usar pd.read_excel con el engine apropiado
        excel_engine = engine_override if engine_override else engine
        
        try:
            if sheet_name is not None:
                return pd.read_excel(
                    io.BytesIO(content),
                    sheet_name=sheet_name,
                    header=header,
                    engine=excel_engine
                )
            else:
                return pd.read_excel(
                    io.BytesIO(content),
                    header=header,
                    engine=excel_engine
                )
        except Exception as e:
            # Si falla con xlrd para .xls, intentar con openpyxl
            if file_type == 'excel_xlrd' and excel_engine == 'xlrd':
                try:
                    print("⚠️ Intentando leer .xls con openpyxl como fallback...")
                    if sheet_name is not None:
                        return pd.read_excel(
                            io.BytesIO(content),
                            sheet_name=sheet_name,
                            header=header,
                            engine='openpyxl'
                        )
                    else:
                        return pd.read_excel(
                            io.BytesIO(content),
                            header=header,
                            engine='openpyxl'
                        )
                except:
                    # Si también falla, lanzar el error original
                    pass
            
            if file_type == 'excel_xlsb':
                raise ValueError(
                    "El formato .xlsb (Excel binario) no está soportado actualmente. "
                    "Por favor, convierte el archivo a .xlsx o .xls"
                ) from e
            elif file_type == 'ods':
                raise ValueError(
                    "El formato .ods (OpenDocument) requiere la librería 'odfpy'. "
                    "Por favor, instala 'odfpy' o convierte el archivo a .xlsx"
                ) from e
            raise
    
    else:
        supported = '.csv, .xlsx, .xls, .xlsm, .xlsb, .ods'
        raise ValueError(
            f"Tipo de archivo no soportado: {file_type}. "
            f"Formatos soportados: {supported}"
        )


def get_excel_sheets(content: bytes, filename: str = "archivo.xlsx") -> list:
    """
    Obtiene la lista de hojas disponibles en un archivo Excel/ODS.
    Retorna lista vacía si no es Excel/ODS o hay error.
    """
    try:
        file_type = detect_file_type(filename)
        
        # Determinar engine según tipo
        if file_type == 'excel_xlrd':
            engine = 'xlrd'
        elif file_type == 'excel_openpyxl':
            engine = 'openpyxl'
        elif file_type == 'ods':
            engine = 'odf'
        else:
            engine = None
        
        xls = pd.ExcelFile(io.BytesIO(content), engine=engine)
        return xls.sheet_names
    except:
        return []

