"""
Funciones de validación y limpieza de datos.
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, Union, Tuple


# =============================================================================
# FINANCIAL-GRADE NORMALIZERS
# =============================================================================

def normalize_amount(value: Union[str, int, float, None]) -> Optional[Decimal]:
    """
    Normaliza un monto a Decimal para operaciones financieras precisas.
    
    Formatos soportados:
    - $1,234.56 → 1234.56
    - 1.234,56 (formato europeo) → 1234.56
    - (1,234.56) (negativo) → -1234.56
    - B/. 1,234.56 → 1234.56
    - -1234.56 → -1234.56
    
    Returns:
        Decimal or None if invalid
    """
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, Decimal):
        return value
    
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return Decimal(str(round(value, 2)))
    
    s = str(value).strip()
    if not s or s.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Detect negative from parentheses: (1,234.56) -> negative
    is_negative = s.startswith('(') and s.endswith(')')
    if is_negative:
        s = s[1:-1]
    
    # Remove currency symbols
    s = re.sub(r'[Bb]/\.?\s*', '', s)  # B/. or B/
    s = re.sub(r'[$€£]', '', s)
    s = s.strip()
    
    # Detect format: European (1.234,56) vs US (1,234.56)
    # European: last separator is comma, thousands are dots
    # US: last separator is dot, thousands are commas
    
    comma_pos = s.rfind(',')
    dot_pos = s.rfind('.')
    
    if comma_pos > dot_pos and comma_pos > 0:
        # European format: 1.234,56
        s = s.replace('.', '')  # Remove thousand separators
        s = s.replace(',', '.')  # Convert decimal separator
    else:
        # US format: 1,234.56
        s = s.replace(',', '')  # Remove thousand separators
    
    # Handle negative sign
    if '-' in s:
        is_negative = True
        s = s.replace('-', '')
    
    try:
        result = Decimal(s)
        if is_negative:
            result = -result
        return result.quantize(Decimal('0.01'))
    except InvalidOperation:
        # Try regex extraction as last resort
        match = re.search(r'[\d.]+', s)
        if match:
            try:
                result = Decimal(match.group(0))
                if is_negative:
                    result = -result
                return result.quantize(Decimal('0.01'))
            except InvalidOperation:
                return None
        return None


def normalize_date(value: Union[str, int, float, datetime, date, pd.Timestamp, None]) -> Optional[date]:
    """
    Normaliza una fecha a objeto date de Python.
    
    Formatos soportados:
    - dd/mm/yyyy, mm/dd/yyyy, yyyy-mm-dd
    - Excel serial date (número como 45678)
    - Timestamp de pandas
    - datetime de Python
    
    Returns:
        date object or None if invalid
    """
    if value is None or pd.isna(value):
        return None
    
    # Already a date
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    
    # datetime or Timestamp → extract date
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date() if hasattr(value, 'date') else value
    
    # Excel serial date (number between ~30000 and ~60000 for years 1980-2060)
    if isinstance(value, (int, float)):
        if 30000 <= value <= 60000:
            try:
                # Excel's epoch is 1899-12-30 (with a bug for 1900 leap year)
                excel_epoch = datetime(1899, 12, 30)
                delta = pd.Timedelta(days=int(value))
                return (excel_epoch + delta).date()
            except:
                pass
        return None
    
    # String parsing
    s = str(value).strip()
    if not s or s.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Remove weekday prefix (lun, mar, mié, etc.)
    s = re.sub(r'^(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)\.?\s+', '', s, flags=re.IGNORECASE).strip()
    
    # Try common formats
    formats = [
        ('%d/%m/%Y', True),   # DD/MM/YYYY (dayfirst)
        ('%Y-%m-%d', False),  # YYYY-MM-DD (ISO)
        ('%d-%m-%Y', True),   # DD-MM-YYYY
        ('%m/%d/%Y', False),  # MM/DD/YYYY (US)
        ('%d.%m.%Y', True),   # DD.MM.YYYY (European)
    ]
    
    for fmt, is_dayfirst in formats:
        try:
            dt = datetime.strptime(s, fmt)
            # Validate year is reasonable
            if 1990 <= dt.year <= 2100:
                return dt.date()
        except ValueError:
            continue
    
    # Fallback: pandas with dayfirst=True (Panama uses DD/MM/YYYY)
    try:
        dt = pd.to_datetime(s, dayfirst=True)
        if 1990 <= dt.year <= 2100:
            return dt.date()
    except:
        pass
    
    return None


# =============================================================================
# LEGACY FUNCTIONS (keeping for backwards compatibility)
# =============================================================================



def clean_amount(value: Union[str, int, float, None]) -> Optional[float]:
    """
    Limpia y convierte un valor a float (monto).
    Maneja formatos como 'B/. 59.95', '$59,95', '(59.95)', etc.
    """
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return round(float(value), 2)
    
    # Convertir a string y limpiar
    s = str(value).strip()
    if not s or s.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Remover símbolos de moneda y espacios
    s = s.replace("B/.", "").replace("B/ ", "").replace("$", "").replace(",", "")
    s = s.replace("(", "-").replace(")", "")  # Manejar valores negativos entre paréntesis
    
    # Remover todo excepto números, punto y signo menos
    s = re.sub(r"[^\d.\-]", "", s)
    
    try:
        val = float(s)
        if np.isnan(val) or np.isinf(val):
            return None
        return round(abs(val), 2)  # Siempre positivo para montos
    except (ValueError, TypeError):
        # Intentar extraer número con regex
        match = re.search(r"[-+]?\d*\.?\d+", s)
        if match:
            try:
                return round(abs(float(match.group(0))), 2)
            except:
                return None
        return None


def clean_date(value: Union[str, datetime, pd.Timestamp, None]) -> Optional[str]:
    """
    Limpia y normaliza una fecha a formato DD/MM/YYYY (string).
    Detecta y corrige automáticamente fechas con día/mes intercambiados.
    Si detecta que una fecha es inválida (ej: 12/01/2025 cuando debería ser 01/12/2025),
    intenta intercambiar día/mes automáticamente.
    Retorna None si no se puede parsear.
    """
    if value is None or pd.isna(value):
        return None
    
    # Si ya es un objeto date/datetime
    if isinstance(value, (datetime, pd.Timestamp)):
        try:
            # Intentar interpretar como DD/MM/YYYY
            fecha_iso = value.strftime("%Y-%m-%d")
            year, month, day = fecha_iso.split("-")
            
            # Validar fecha original
            try:
                dt_original = datetime(int(year), int(month), int(day))
                fecha_str = f"{day}/{month}/{year}"
                # Si la fecha original es válida, usarla
                return dt_original.strftime("%d/%m/%Y")
            except ValueError:
                # Si la fecha original no es válida, intentar intercambiar día/mes
                try:
                    dt_intercambiado = datetime(int(year), int(day), int(month))
                    fecha_str = f"{month}/{day}/{year}"
                    print(f"⚠️ Fecha corregida (intercambiado día/mes): {fecha_str}")
                    return dt_intercambiado.strftime("%d/%m/%Y")
                except ValueError:
                    pass
            
            # Fallback: usar fecha tal cual
            try:
                return value.strftime("%d/%m/%Y")
            except:
                return None
        except:
            # Fallback: usar fecha tal cual
            try:
                return value.strftime("%d/%m/%Y")
            except:
                return None
    
    # Si es string, intentar parsear
    s = str(value).strip()
    if not s or s.lower() in ['nan', 'none', 'null', '']:
        return None
    
    # Remover día de la semana si existe
    s = re.sub(r'^(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)\.?\s+', '', s, flags=re.IGNORECASE).strip()
    
    # Intentar diferentes formatos
    formats = [
        r'^(\d{1,2})/(\d{1,2})/(\d{4})$',  # DD/MM/YYYY
        r'^(\d{4})-(\d{2})-(\d{2})$',      # YYYY-MM-DD
        r'^(\d{1,2})-(\d{1,2})-(\d{4})$',  # DD-MM-YYYY
    ]
    
    for pattern in formats:
        match = re.match(pattern, s)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    if pattern.startswith(r'^(\d{4})'):  # YYYY-MM-DD
                        year, month, day = groups
                    else:  # DD/MM/YYYY o DD-MM-YYYY
                        day, month, year = groups
                    
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    # Obtener mes y año actuales para priorizar fechas del mes actual
                    fecha_actual = datetime.now()
                    mes_actual = fecha_actual.month
                    año_actual = fecha_actual.year
                    
                    # Intentar ambas interpretaciones: DD/MM/YYYY y MM/DD/YYYY
                    interpretaciones = []
                    
                    # Interpretación 1: DD/MM/YYYY (original)
                    try:
                        dt1 = datetime(year_int, month_int, day_int)
                        if dt1.year >= 2000 and dt1.year <= año_actual + 10:
                            # Calcular score: más puntos si es del mes/año actual
                            score1 = 0
                            if dt1.month == mes_actual and dt1.year == año_actual:
                                score1 = 10  # Máxima prioridad: mes y año actual
                            elif dt1.year == año_actual:
                                score1 = 5   # Prioridad media: año actual
                            elif abs((dt1.year - año_actual) * 12 + (dt1.month - mes_actual)) <= 2:
                                score1 = 3  # Prioridad baja: mes cercano (dentro de 2 meses)
                            else:
                                score1 = 1  # Prioridad mínima
                            interpretaciones.append((dt1, score1, f"{day_int:02d}/{month_int:02d}/{year_int}"))
                    except ValueError:
                        pass
                    
                    # Interpretación 2: MM/DD/YYYY (intercambiado) - solo si ambos valores son válidos
                    if month_int <= 12 and day_int <= 31:
                        try:
                            dt2 = datetime(year_int, day_int, month_int)
                            if dt2.year >= 2000 and dt2.year <= año_actual + 10:
                                # Calcular score: más puntos si es del mes/año actual
                                score2 = 0
                                if dt2.month == mes_actual and dt2.year == año_actual:
                                    score2 = 10  # Máxima prioridad: mes y año actual
                                elif dt2.year == año_actual:
                                    score2 = 5   # Prioridad media: año actual
                                elif abs((dt2.year - año_actual) * 12 + (dt2.month - mes_actual)) <= 2:
                                    score2 = 3  # Prioridad baja: mes cercano
                                else:
                                    score2 = 1  # Prioridad mínima
                                interpretaciones.append((dt2, score2, f"{month_int:02d}/{day_int:02d}/{year_int}"))
                        except ValueError:
                            pass
                    
                    # Si hay interpretaciones válidas, elegir la de mayor score (prioriza mes actual)
                    if interpretaciones:
                        # Ordenar por score descendente
                        interpretaciones.sort(key=lambda x: x[1], reverse=True)
                        dt_final, score_final, fecha_str_final = interpretaciones[0]
                        
                        # Si se eligió la interpretación intercambiada, mostrar advertencia
                        if len(interpretaciones) > 1 and interpretaciones[0][2] != f"{day_int:02d}/{month_int:02d}/{year_int}":
                            print(f"⚠️ Fecha corregida (priorizado mes actual): {s} -> {fecha_str_final} (score: {score_final})")
                        elif score_final >= 5:
                            print(f"✅ Fecha detectada (mes actual): {fecha_str_final}")
                        
                        return dt_final.strftime("%d/%m/%Y")
                    
                    # Si ninguna interpretación es válida, intentar forzar con el orden original
                    try:
                        dt = datetime(year_int, month_int, day_int)
                        return dt.strftime("%d/%m/%Y")
                    except ValueError:
                        # Si falla, intentar intercambiado como último recurso
                        if month_int <= 12 and day_int <= 31:
                            try:
                                dt_corregido = datetime(year_int, day_int, month_int)
                                fecha_corregida = dt_corregido.strftime("%d/%m/%Y")
                                print(f"⚠️ Fecha corregida (intercambiado día/mes): {s} -> {fecha_corregida}")
                                return fecha_corregida
                            except ValueError:
                                pass
            except (ValueError, TypeError):
                continue
    
    # Último intento con pd.to_datetime (con detección de intercambio)
    try:
        # Intentar primero con dayfirst=True (DD/MM/YYYY)
        dt = pd.to_datetime(s, dayfirst=True)
        fecha_str = dt.strftime("%d/%m/%Y")
        
        # Validar que la fecha sea razonable
        fecha_actual = datetime.now()
        if dt.year > fecha_actual.year + 10:
            # Si es muy futura, intentar sin dayfirst
            try:
                dt_alt = pd.to_datetime(s, dayfirst=False)
                if dt_alt.year <= fecha_actual.year + 10:
                    fecha_str_alt = dt_alt.strftime("%d/%m/%Y")
                    print(f"⚠️ Fecha corregida (cambiado dayfirst): {s} -> {fecha_str_alt}")
                    return fecha_str_alt
            except:
                pass
        
        return fecha_str
    except:
        return None


def validate_dataframe(df: pd.DataFrame, required_columns: list, min_rows: int = 1) -> Tuple[bool, Optional[str]]:
    """
    Valida que un DataFrame tenga las columnas requeridas y al menos min_rows filas.
    Retorna (is_valid, error_message).
    """
    if df is None or df.empty:
        return False, "El DataFrame está vacío"
    
    if len(df) < min_rows:
        return False, f"El DataFrame tiene menos de {min_rows} fila(s)"
    
    # Normalizar nombres de columnas para comparación
    df_cols_lower = [str(c).strip().lower() for c in df.columns]
    required_lower = [str(c).strip().lower() for c in required_columns]
    
    missing = []
    for req in required_lower:
        if not any(req in col for col in df_cols_lower):
            missing.append(req)
    
    if missing:
        return False, f"Faltan las siguientes columnas: {', '.join(missing)}"
    
    return True, None


def normalize_text(text: Union[str, None]) -> str:
    """
    Normaliza texto: elimina espacios, convierte a mayúsculas, elimina tildes.
    """
    if text is None or pd.isna(text):
        return ""
    
    s = str(text).strip().upper()
    # Eliminar tildes
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'á': 'A', 'é': 'E', 'í': 'I', 'ó': 'O', 'ú': 'U',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    
    return s


# Importar funciones del column_detector para mantener compatibilidad
from app.utils.column_detector import (
    is_likely_date_column,
    is_likely_amount_column,
    is_likely_text_column,
    normalize_column_name,
    fuzzy_match_score
)

# Re-exportar para uso directo desde validators
__all__ = [
    # Financial-grade normalizers
    'normalize_amount',
    'normalize_date',
    # Legacy cleaners
    'clean_amount',
    'clean_date',
    'validate_dataframe',
    'normalize_text',
    # Column detection utilities
    'is_likely_date_column',
    'is_likely_amount_column',
    'is_likely_text_column',
    'normalize_column_name',
    'fuzzy_match_score'
]

