"""
Utilidades para formatear respuestas de API de manera consistente.
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


def create_response(
    success: bool = True,
    data: Any = None,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    start_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Crea una respuesta de API con estructura consistente.
    
    Args:
        success: Si la operación fue exitosa
        data: Datos a retornar
        message: Mensaje descriptivo
        warnings: Lista de advertencias
        errors: Lista de errores
        request_id: ID de la request (se genera si no se proporciona)
        start_time: Tiempo de inicio para calcular processing_time_ms
    
    Returns:
        Diccionario con la respuesta formateada
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    
    processing_time_ms = None
    if start_time is not None:
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
    
    response = {
        "success": success,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        }
    }
    
    if processing_time_ms is not None:
        response["meta"]["processing_time_ms"] = processing_time_ms
    
    if message:
        response["message"] = message
    
    if warnings:
        response["warnings"] = warnings
    
    if errors:
        response["errors"] = errors
    
    return response


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Crea una respuesta de éxito.
    """
    return create_response(
        success=True,
        data=data,
        message=message,
        warnings=warnings,
        **kwargs
    )


def error_response(
    errors: List[str],
    message: Optional[str] = None,
    data: Any = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Crea una respuesta de error.
    """
    return create_response(
        success=False,
        data=data,
        message=message,
        errors=errors,
        **kwargs
    )

