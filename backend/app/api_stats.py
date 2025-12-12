"""
API endpoints para estadísticas y dashboard.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.utils.logger import app_logger
from app.utils.response_formatter import success_response

router = APIRouter()


@router.get("/stats")
async def get_stats(
    days: int = 30,
    sucursal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene estadísticas agregadas para el dashboard.
    
    Args:
        days: Número de días hacia atrás para calcular estadísticas (default: 30)
        sucursal: Filtrar por sucursal específica (opcional)
    
    Returns:
        Estadísticas agregadas
    """
    try:
        app_logger.info(f"Obteniendo estadísticas para últimos {days} días")
        
        # Por ahora retornamos estadísticas mock
        # En el futuro, esto se conectará a la base de datos
        fecha_inicio = datetime.now() - timedelta(days=days)
        
        stats = {
            "periodo": {
                "inicio": fecha_inicio.strftime("%Y-%m-%d"),
                "fin": datetime.now().strftime("%Y-%m-%d"),
                "dias": days
            },
            "resumen": {
                "total_conciliaciones": 0,  # Se actualizará cuando haya BD
                "coincidencias_exactas": 0,
                "coincidencias_parciales": 0,
                "sin_coincidencia": 0,
                "tasa_coincidencia": 0.0
            },
            "por_tipo": {
                "yappy": {
                    "total": 0,
                    "coincidencias": 0,
                    "discrepancias": 0
                },
                "banco": {
                    "total": 0,
                    "coincidencias": 0,
                    "discrepancias": 0
                }
            },
            "por_sucursal": {},
            "tendencias": {
                "fechas": [],
                "conciliaciones": [],
                "coincidencias": []
            }
        }
        
        return success_response(
            data=stats,
            message=f"Estadísticas de los últimos {days} días"
        )
        
    except Exception as e:
        app_logger.error(f"Error obteniendo estadísticas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/stats/recent")
async def get_recent_conciliaciones(limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene las conciliaciones más recientes.
    
    Args:
        limit: Número máximo de conciliaciones a retornar
    
    Returns:
        Lista de conciliaciones recientes
    """
    try:
        app_logger.info(f"Obteniendo {limit} conciliaciones recientes")
        
        # Por ahora retornamos lista vacía
        # En el futuro, esto se conectará a la base de datos
        conciliaciones = []
        
        return success_response(
            data={
                "conciliaciones": conciliaciones,
                "total": len(conciliaciones)
            },
            message=f"{len(conciliaciones)} conciliaciones recientes"
        )
        
    except Exception as e:
        app_logger.error(f"Error obteniendo conciliaciones recientes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener conciliaciones recientes: {str(e)}"
        )

