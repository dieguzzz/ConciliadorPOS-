"""
Funciones de validación y limpieza de datos.
"""
import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Optional, Union, Tuple


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
                    
                    # Intentar primero con el orden original (DD/MM/YYYY)
                    try:
                        dt = datetime(year_int, month_int, day_int)
                        # Validar que la fecha sea razonable (no muy futura, no muy antigua)
                        fecha_actual = datetime.now()
                        if dt.year > fecha_actual.year + 10 or dt.year < 2000:
                            # Si la fecha es muy futura o muy antigua, puede estar al revés
                            raise ValueError("Fecha fuera de rango razonable")
                        return dt.strftime("%d/%m/%Y")
                    except ValueError:
                        # Si falla, intentar intercambiar día y mes
                        # Ejemplo: 12/01/2025 -> 01/12/2025 (si 12 no es un mes válido)
                        if month_int > 12 and day_int <= 12:
                            # El mes es > 12, probablemente está al revés
                            try:
                                dt_corregido = datetime(year_int, day_int, month_int)
                                fecha_corregida = dt_corregido.strftime("%d/%m/%Y")
                                print(f"⚠️ Fecha corregida (intercambiado día/mes): {s} -> {fecha_corregida}")
                                return fecha_corregida
                            except ValueError:
                                pass
                        elif day_int > 31 and month_int <= 12:
                            # El día es > 31, probablemente está al revés
                            try:
                                dt_corregido = datetime(year_int, day_int, month_int)
                                fecha_corregida = dt_corregido.strftime("%d/%m/%Y")
                                print(f"⚠️ Fecha corregida (intercambiado día/mes): {s} -> {fecha_corregida}")
                                return fecha_corregida
                            except ValueError:
                                pass
                        # Si ambos son válidos pero la fecha original no funciona, probar intercambio
                        elif month_int <= 12 and day_int <= 31:
                            try:
                                dt_corregido = datetime(year_int, day_int, month_int)
                                # Si la fecha corregida es más razonable (no muy futura)
                                fecha_actual = datetime.now()
                                if dt_corregido.year <= fecha_actual.year + 10:
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

