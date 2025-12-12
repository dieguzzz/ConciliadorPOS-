"""
Utilidades para extraer información de fecha del nombre del archivo.
"""
import re
from datetime import datetime
from typing import Optional, Tuple


# Mapeo de meses en español a números
MESES_ESPANOL = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    # Variaciones comunes
    'dic': 12, 'nov': 11, 'oct': 10, 'sep': 9,
    'ago': 8, 'jul': 7, 'jun': 6, 'may': 5,
    'abr': 4, 'mar': 3, 'feb': 2, 'ene': 1,
}


def extraer_fecha_del_nombre(filename: str) -> Optional[dict]:
    """
    Extrae información de fecha del nombre del archivo.
    
    Patrones soportados:
    - "CIERRE1-10 ALBROOK DICIEMBRE .xlsx" -> mes: 12, rango: 1-10
    - "CIERRE NOV DIEGO.xlsx" -> mes: 11
    - "MOVIMIENTOS-BANCO 1-11 DICIEMBRE DIEGO.xlsx" -> mes: 12, rango: 1-11
    
    Returns:
        dict con keys: 'mes', 'año', 'dia_inicio', 'dia_fin', 'mes_nombre'
        o None si no se encuentra información
    """
    if not filename:
        return None
    
    filename_upper = filename.upper()
    resultado = {
        'mes': None,
        'año': None,
        'dia_inicio': None,
        'dia_fin': None,
        'mes_nombre': None
    }
    
    # Buscar mes en español
    for mes_nombre, mes_num in MESES_ESPANOL.items():
        if mes_nombre.upper() in filename_upper:
            resultado['mes'] = mes_num
            resultado['mes_nombre'] = mes_nombre.capitalize()
            break
    
    # Buscar año (4 dígitos, típicamente 2024, 2025, etc.)
    año_match = re.search(r'\b(20\d{2})\b', filename)
    if año_match:
        resultado['año'] = int(año_match.group(1))
    else:
        # Si no hay año, usar el año actual
        resultado['año'] = datetime.now().year
    
    # Buscar rango de días (ej: "1-10", "1-11", "1-15")
    rango_match = re.search(r'(\d{1,2})[-\s]+(\d{1,2})', filename)
    if rango_match:
        dia_inicio = int(rango_match.group(1))
        dia_fin = int(rango_match.group(2))
        resultado['dia_inicio'] = dia_inicio
        resultado['dia_fin'] = dia_fin
    
    # Si encontramos al menos el mes, retornar resultado
    if resultado['mes']:
        return resultado
    
    return None


def validar_y_corregir_fecha_con_nombre(
    fecha_detectada: str,
    info_nombre: dict,
    fecha_original: Optional[str] = None
) -> Tuple[str, bool]:
    """
    Valida y corrige una fecha detectada usando información del nombre del archivo.
    
    Args:
        fecha_detectada: Fecha detectada en formato DD/MM/YYYY
        info_nombre: Información extraída del nombre del archivo
        fecha_original: Fecha original antes de procesar (opcional)
    
    Returns:
        Tuple (fecha_corregida, fue_corregida)
    """
    if not info_nombre or not info_nombre.get('mes'):
        return fecha_detectada, False
    
    try:
        # Parsear fecha detectada
        dt_detectada = datetime.strptime(fecha_detectada, "%d/%m/%Y")
        mes_detectado = dt_detectada.month
        año_detectado = dt_detectada.year
        dia_detectado = dt_detectada.day
        
        mes_esperado = info_nombre['mes']
        año_esperado = info_nombre.get('año', datetime.now().year)
        
        # Si el mes detectado no coincide con el mes del nombre, corregir
        if mes_detectado != mes_esperado:
            # Verificar si día y mes están intercambiados
            if dia_detectado == mes_esperado and mes_detectado <= 12:
                # Intercambiar día y mes
                try:
                    dt_corregida = datetime(año_esperado, dia_detectado, mes_detectado)
                    fecha_corregida = dt_corregida.strftime("%d/%m/%Y")
                    print(f"✅ Fecha corregida usando nombre del archivo: {fecha_detectada} -> {fecha_corregida} (mes esperado: {mes_esperado})")
                    return fecha_corregida, True
                except ValueError:
                    pass
            
            # Si no se puede intercambiar, usar el mes del nombre y mantener el día
            try:
                dt_corregida = datetime(año_esperado, mes_esperado, dia_detectado)
                fecha_corregida = dt_corregida.strftime("%d/%m/%Y")
                print(f"✅ Fecha corregida usando mes del nombre: {fecha_detectada} -> {fecha_corregida} (mes esperado: {mes_esperado})")
                return fecha_corregida, True
            except ValueError:
                pass
        
        # Si el año no coincide y el nombre tiene año, corregir año
        if año_detectado != año_esperado and info_nombre.get('año'):
            try:
                dt_corregida = datetime(año_esperado, mes_detectado, dia_detectado)
                fecha_corregida = dt_corregida.strftime("%d/%m/%Y")
                print(f"✅ Fecha corregida usando año del nombre: {fecha_detectada} -> {fecha_corregida} (año esperado: {año_esperado})")
                return fecha_corregida, True
            except ValueError:
                pass
        
        return fecha_detectada, False
        
    except ValueError:
        # Si no se puede parsear, retornar tal cual
        return fecha_detectada, False

