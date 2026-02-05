"""
Módulo de detección inteligente de columnas con sistema multi-estrategia y scoring.

Este módulo implementa un sistema robusto para detectar columnas en archivos Excel/CSV
usando múltiples estrategias: búsqueda por nombre, análisis de contenido y posición.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from difflib import SequenceMatcher

# Import parser types for FieldEvidence
from app.utils.parser_types import FieldEvidence, ConfidenceLevel


def normalize_column_name(name: str) -> str:
    """
    Normaliza un nombre de columna para comparación.
    
    Args:
        name: Nombre de la columna
        
    Returns:
        Nombre normalizado (sin espacios, tildes, en minúsculas)
    """
    if not name or pd.isna(name):
        return ""
    
    # Convertir a string y normalizar
    name_str = str(name).strip()
    
    # Remover tildes y caracteres especiales comunes
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
        'ñ': 'n', 'Ñ': 'n'
    }
    for old, new in replacements.items():
        name_str = name_str.replace(old, new)
    
    # Convertir a minúsculas y remover espacios extra
    name_str = name_str.lower()
    name_str = re.sub(r'\s+', ' ', name_str).strip()
    
    return name_str


def fuzzy_match_score(name1: str, name2: str) -> float:
    """
    Calcula un score de similitud entre dos nombres (0-100).
    
    Args:
        name1: Primer nombre
        name2: Segundo nombre
        
    Returns:
        Score de similitud (0-100)
    """
    if not name1 or not name2:
        return 0.0
    
    norm1 = normalize_column_name(name1)
    norm2 = normalize_column_name(name2)
    
    if norm1 == norm2:
        return 100.0
    
    # Usar SequenceMatcher para similitud
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # También verificar si uno contiene al otro
    if norm1 in norm2 or norm2 in norm1:
        similarity = max(similarity, 0.8)
    
    return similarity * 100


def is_likely_date_column(series: pd.Series, sample_size: int = 100) -> Tuple[bool, float]:
    """
    Analiza si una serie parece contener fechas.
    
    Args:
        series: Serie de pandas a analizar
        sample_size: Número de valores a muestrear
        
    Returns:
        Tupla (es_fecha, score_0_100)
    """
    if len(series) == 0:
        return False, 0.0
    
    # Muestrear valores no nulos
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, 0.0
    
    sample = non_null.head(min(sample_size, len(non_null)))
    date_indicators = 0
    total_checked = 0
    
    for val in sample:
        if pd.isna(val):
            continue
        
        val_str = str(val).strip()
        total_checked += 1
        
        # Indicadores de fecha
        if isinstance(val, (datetime, pd.Timestamp)):
            date_indicators += 1
        elif '/' in val_str or '-' in val_str:
            # Intentar parsear como fecha
            try:
                # Formato DD/MM/YYYY o MM/DD/YYYY
                if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', val_str):
                    date_indicators += 1
            except:
                pass
        
        # Verificar si es un número que podría ser fecha serial de Excel
        try:
            num = float(val_str)
            # Fechas seriales de Excel están típicamente entre 40000-50000 (años 2000-2100)
            if 30000 < num < 60000:
                date_indicators += 0.5  # Pista parcial
        except:
            pass
    
    if total_checked == 0:
        return False, 0.0
    
    score = (date_indicators / total_checked) * 100
    return score > 30, score


def is_likely_amount_column(series: pd.Series, sample_size: int = 100) -> Tuple[bool, float]:
    """
    Analiza si una serie parece contener montos/dinero.
    
    Args:
        series: Serie de pandas a analizar
        sample_size: Número de valores a muestrear
        
    Returns:
        Tupla (es_monto, score_0_100)
    """
    if len(series) == 0:
        return False, 0.0
    
    # Muestrear valores no nulos
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, 0.0
    
    sample = non_null.head(min(sample_size, len(non_null)))
    amount_indicators = 0
    total_checked = 0
    numeric_count = 0
    
    for val in sample:
        if pd.isna(val):
            continue
        
        val_str = str(val).strip()
        total_checked += 1
        
        # Verificar si es numérico
        try:
            # Limpiar formato de dinero
            clean_val = val_str.replace('B/.', '').replace('$', '').replace(',', '').replace(' ', '')
            num = float(clean_val)
            numeric_count += 1
            
            # Montos típicamente están en rangos razonables (0.01 a millones)
            if 0.01 <= abs(num) <= 10000000:
                amount_indicators += 1
        except:
            # Verificar si tiene símbolos de dinero
            if any(symbol in val_str for symbol in ['B/.', '$', 'USD', 'PAB']):
                amount_indicators += 0.5
    
    if total_checked == 0:
        return False, 0.0
    
    # Score basado en porcentaje numérico y presencia de símbolos de dinero
    numeric_ratio = numeric_count / total_checked
    amount_ratio = amount_indicators / total_checked
    
    score = (numeric_ratio * 0.7 + amount_ratio * 0.3) * 100
    return score > 40, score


def is_likely_text_column(series: pd.Series, sample_size: int = 100) -> Tuple[bool, float]:
    """
    Analiza si una serie parece contener texto/descripciones.
    
    Args:
        series: Serie de pandas a analizar
        sample_size: Número de valores a muestrear
        
    Returns:
        Tupla (es_texto, score_0_100)
    """
    if len(series) == 0:
        return False, 0.0
    
    # Muestrear valores no nulos
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, 0.0
    
    sample = non_null.head(min(sample_size, len(non_null)))
    text_indicators = 0
    total_checked = 0
    avg_length = 0
    
    for val in sample:
        if pd.isna(val):
            continue
        
        val_str = str(val).strip()
        total_checked += 1
        avg_length += len(val_str)
        
        # Texto típicamente tiene más de 5 caracteres y contiene letras
        if len(val_str) > 5 and re.search(r'[a-zA-Z]', val_str):
            text_indicators += 1
    
    if total_checked == 0:
        return False, 0.0
    
    avg_length = avg_length / total_checked
    text_ratio = text_indicators / total_checked
    
    # Score basado en ratio de texto y longitud promedio
    length_score = min(avg_length / 20, 1.0) * 50  # Máximo 50 puntos por longitud
    ratio_score = text_ratio * 50  # Máximo 50 puntos por ratio
    
    score = length_score + ratio_score
    return score > 40, score


class ColumnDetector:
    """
    Detector inteligente de columnas con sistema multi-estrategia y scoring.
    """
    
    def __init__(self, df: pd.DataFrame, expected_columns: Dict[str, List[str]] = None):
        """
        Inicializa el detector.
        
        Args:
            df: DataFrame a analizar
            expected_columns: Diccionario con nombres esperados para cada tipo de columna
                Ejemplo: {"fecha": ["fecha", "date"], "monto": ["monto", "credito"]}
        """
        self.df = df
        self.expected_columns = expected_columns or {
            "fecha": ["fecha", "date", "fecha movimiento", "fecha de movimiento"],
            "descripcion": ["descripcion", "descripción", "desc", "concepto", "detalle", "movimiento"],
            "monto": ["credito", "crédito", "credit", "monto", "importe", "valor", "cantidad", "debito", "débito"]
        }
        self.detection_results = {}
    
    def detect_column(self, column_type: str, position_hint: Optional[int] = None) -> Dict[str, Any]:
        """
        Detecta una columna de un tipo específico.
        
        Args:
            column_type: Tipo de columna a detectar ("fecha", "monto", "descripcion")
            position_hint: Posición esperada (índice de columna, opcional)
            
        Returns:
            Diccionario con información de la detección:
            {
                "column_index": int o None,
                "column_name": str o None,
                "confidence": float (0-100),
                "scores": {
                    "name": float,
                    "content": float,
                    "position": float
                }
            }
        """
        if column_type not in self.expected_columns:
            return {
                "column_index": None,
                "column_name": None,
                "confidence": 0.0,
                "scores": {"name": 0.0, "content": 0.0, "position": 0.0}
            }
        
        candidates = []
        expected_names = self.expected_columns[column_type]
        
        # Analizar cada columna
        for col_idx, col_name in enumerate(self.df.columns):
            scores = {
                "name": 0.0,
                "content": 0.0,
                "position": 0.0
            }
            
            # Estrategia 1: Score por nombre
            best_name_score = 0.0
            for expected_name in expected_names:
                score = fuzzy_match_score(str(col_name), expected_name)
                best_name_score = max(best_name_score, score)
            scores["name"] = best_name_score
            
            # Estrategia 2: Score por contenido
            if len(self.df) > 0:
                series = self.df.iloc[:, col_idx]
                
                if column_type == "fecha":
                    _, content_score = is_likely_date_column(series)
                elif column_type == "monto":
                    _, content_score = is_likely_amount_column(series)
                elif column_type == "descripcion":
                    _, content_score = is_likely_text_column(series)
                else:
                    content_score = 0.0
                
                scores["content"] = content_score
            else:
                scores["content"] = 0.0
            
            # Estrategia 3: Score por posición
            if position_hint is not None:
                # Bonus si está cerca de la posición esperada
                distance = abs(col_idx - position_hint)
                if distance == 0:
                    scores["position"] = 50.0
                elif distance == 1:
                    scores["position"] = 30.0
                elif distance == 2:
                    scores["position"] = 15.0
                else:
                    scores["position"] = 0.0
            else:
                scores["position"] = 0.0
            
            # Score total ponderado
            total_score = (
                scores["name"] * 0.4 +      # 40% peso en nombre
                scores["content"] * 0.5 +   # 50% peso en contenido
                scores["position"] * 0.1    # 10% peso en posición
            )
            
            candidates.append({
                "column_index": col_idx,
                "column_name": col_name,
                "confidence": total_score,
                "scores": scores
            })
        
        # Ordenar por score y retornar el mejor
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        if candidates and candidates[0]["confidence"] > 30:  # Umbral mínimo
            return candidates[0]
        else:
            return {
                "column_index": None,
                "column_name": None,
                "confidence": 0.0,
                "scores": {"name": 0.0, "content": 0.0, "position": 0.0}
            }
    
    def detect_all(self, position_hints: Optional[Dict[str, int]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Detecta todas las columnas esperadas.
        
        Args:
            position_hints: Diccionario con posiciones esperadas por tipo
            
        Returns:
            Diccionario con resultados de detección para cada tipo
        """
        results = {}
        position_hints = position_hints or {}
        
        for column_type in self.expected_columns.keys():
            position_hint = position_hints.get(column_type)
            results[column_type] = self.detect_column(column_type, position_hint)
        
        self.detection_results = results
        return results
    
    def get_field_evidence(self) -> Dict[str, FieldEvidence]:
        """
        Genera evidencia auditable para cada campo detectado.
        Debe llamarse después de detect_all().
        
        Returns:
            Dict[str, FieldEvidence] con evidencia por campo
        """
        if not self.detection_results:
            return {}
        
        evidence = {}
        for field_type, detection in self.detection_results.items():
            if detection["column_index"] is None:
                continue
            
            scores = detection["scores"]
            
            # Determinar método principal usado
            if scores["name"] >= scores["content"] and scores["name"] >= scores["position"]:
                method = "NAME"
                evidence_detail = f"keyword match: '{detection['column_name']}'"
            elif scores["content"] >= scores["name"] and scores["content"] >= scores["position"]:
                method = "CONTENT"
                if field_type == "fecha":
                    evidence_detail = "date pattern detected"
                elif field_type == "monto":
                    evidence_detail = "numeric/currency values detected"
                else:
                    evidence_detail = "text pattern detected"
            else:
                method = "POSITIONAL"
                evidence_detail = f"column position: {detection['column_index']}"
            
            evidence[field_type] = FieldEvidence(
                column=str(detection["column_name"]),
                confidence=detection["confidence"],
                method=method,
                evidence=evidence_detail
            )
        
        return evidence
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """
        Determina el nivel de confianza global basado en todas las detecciones.
        
        Returns:
            ConfidenceLevel (HIGH, MEDIUM, LOW)
        """
        if not self.detection_results:
            return ConfidenceLevel.LOW
        
        # Calcular promedio de confianza de campos detectados
        confidences = []
        for detection in self.detection_results.values():
            if detection["column_index"] is not None:
                confidences.append(detection["confidence"])
        
        if not confidences:
            return ConfidenceLevel.LOW
        
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        
        # El nivel se determina por el mínimo (el eslabón más débil)
        if min_confidence >= 70:
            return ConfidenceLevel.HIGH
        elif min_confidence >= 40:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def validate_detection(self, min_confidence: float = 70.0, min_valid_rows_ratio: float = 0.5) -> Dict[str, Any]:
        """
        Valida que las columnas detectadas tienen datos válidos.
        
        Args:
            min_confidence: Confianza mínima requerida
            min_valid_rows_ratio: Ratio mínimo de filas válidas (0-1)
            
        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {
            "overall_valid": True,
            "column_validations": {},
            "warnings": []
        }
        
        for column_type, detection in self.detection_results.items():
            col_validation = {
                "valid": True,
                "confidence": detection["confidence"],
                "valid_rows": 0,
                "total_rows": len(self.df),
                "valid_ratio": 0.0,
                "issues": []
            }
            
            if detection["column_index"] is None:
                col_validation["valid"] = False
                col_validation["issues"].append(f"No se detectó columna para {column_type}")
                validation_results["overall_valid"] = False
            elif detection["confidence"] < min_confidence:
                col_validation["valid"] = False
                col_validation["issues"].append(f"Confianza baja: {detection['confidence']:.1f}%")
                validation_results["warnings"].append(
                    f"Columna {column_type} detectada con baja confianza ({detection['confidence']:.1f}%)"
                )
            else:
                # Validar contenido de la columna
                col_idx = detection["column_index"]
                series = self.df.iloc[:, col_idx]
                
                if column_type == "fecha":
                    valid_count = 0
                    for val in series.dropna():
                        try:
                            if isinstance(val, (datetime, pd.Timestamp)):
                                valid_count += 1
                            else:
                                val_str = str(val).strip()
                                if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', val_str):
                                    valid_count += 1
                        except:
                            pass
                    col_validation["valid_rows"] = valid_count
                
                elif column_type == "monto":
                    valid_count = 0
                    for val in series.dropna():
                        try:
                            val_str = str(val).replace('B/.', '').replace('$', '').replace(',', '').replace(' ', '')
                            num = float(val_str)
                            if num > 0:
                                valid_count += 1
                        except:
                            pass
                    col_validation["valid_rows"] = valid_count
                
                elif column_type == "descripcion":
                    valid_count = 0
                    for val in series.dropna():
                        val_str = str(val).strip()
                        if len(val_str) > 0:
                            valid_count += 1
                    col_validation["valid_rows"] = valid_count
                
                col_validation["valid_ratio"] = (
                    col_validation["valid_rows"] / col_validation["total_rows"]
                    if col_validation["total_rows"] > 0 else 0.0
                )
                
                if col_validation["valid_ratio"] < min_valid_rows_ratio:
                    col_validation["valid"] = False
                    col_validation["issues"].append(
                        f"Ratio de filas válidas bajo: {col_validation['valid_ratio']:.1%}"
                    )
                    validation_results["warnings"].append(
                        f"Columna {column_type} tiene solo {col_validation['valid_ratio']:.1%} de filas válidas"
                    )
                    validation_results["overall_valid"] = False
            
            validation_results["column_validations"][column_type] = col_validation
        
        return validation_results

