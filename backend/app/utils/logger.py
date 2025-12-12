"""
Sistema de logging estructurado para el backend.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class StructuredFormatter(logging.Formatter):
    """
    Formateador que convierte logs a formato JSON estructurado.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Agregar información adicional si existe
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        # Agregar excepción si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None
            }
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_json: bool = True
) -> logging.Logger:
    """
    Configura un logger con formato estructurado.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        log_file: Archivo donde escribir logs (opcional)
        use_json: Si True, usa formato JSON; si False, usa formato legible
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Logger principal de la aplicación
app_logger = setup_logger("conciliador", level=logging.INFO, use_json=False)

# Logger para requests HTTP
request_logger = setup_logger("conciliador.requests", level=logging.INFO, use_json=False)

# Logger para errores
error_logger = setup_logger("conciliador.errors", level=logging.ERROR, use_json=True)

# Logger para debugging
debug_logger = setup_logger("conciliador.debug", level=logging.DEBUG, use_json=False)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    exc_info: Optional[Exception] = None
):
    """
    Log con contexto adicional.
    
    Args:
        logger: Logger a usar
        level: Nivel de logging
        message: Mensaje a loguear
        request_id: ID de la request (opcional)
        user_id: ID del usuario (opcional)
        extra_data: Datos adicionales (opcional)
        exc_info: Excepción a incluir (opcional)
    """
    extra = {}
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    if extra_data:
        extra["extra_data"] = extra_data
    
    logger.log(level, message, extra=extra, exc_info=exc_info)

