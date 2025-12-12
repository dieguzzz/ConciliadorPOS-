"""
API endpoints para el historial de conciliaciones.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database import get_db, init_db, Conciliacion
from app.utils.logger import app_logger
from app.utils.response_formatter import success_response, error_response

router = APIRouter()

# Inicializar BD al importar
init_db()


@router.get("/historial")
async def listar_historial(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sucursal: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Lista conciliaciones con paginación y filtros.
    """
    try:
        query = db.query(Conciliacion)
        
        # Filtros
        if fecha_inicio:
            try:
                fecha_inicio_obj = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                query = query.filter(Conciliacion.fecha_conciliacion >= fecha_inicio_obj)
            except ValueError:
                pass
        
        if fecha_fin:
            try:
                fecha_fin_obj = datetime.strptime(fecha_fin, "%Y-%m-%d")
                query = query.filter(Conciliacion.fecha_conciliacion <= fecha_fin_obj)
            except ValueError:
                pass
        
        if sucursal:
            query = query.filter(Conciliacion.sucursal.ilike(f"%{sucursal}%"))
        
        if estado:
            query = query.filter(Conciliacion.estado == estado)
        
        # Contar total
        total = query.count()
        
        # Paginación
        conciliaciones = query.order_by(Conciliacion.fecha_conciliacion.desc()).offset(skip).limit(limit).all()
        
        # Convertir a dict
        resultados = [
            {
                "id": c.id,
                "fecha_conciliacion": c.fecha_conciliacion.isoformat() if c.fecha_conciliacion else None,
                "fecha_cierre": c.fecha_cierre,
                "sucursal": c.sucursal,
                "cajero": c.cajero,
                "estado": c.estado,
                "total_coincidencias_exactas": c.total_coincidencias_exactas,
                "total_coincidencias_parciales": c.total_coincidencias_parciales,
                "total_sin_coincidencia": c.total_sin_coincidencia,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in conciliaciones
        ]
        
        return success_response(
            data={
                "conciliaciones": resultados,
                "total": total,
                "skip": skip,
                "limit": limit
            },
            message=f"{len(resultados)} conciliaciones encontradas"
        )
        
    except Exception as e:
        app_logger.error(f"Error listando historial: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar historial: {str(e)}"
        )


@router.get("/historial/{id}")
async def obtener_conciliacion(
    id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene los detalles de una conciliación específica.
    """
    try:
        conciliacion = db.query(Conciliacion).filter(Conciliacion.id == id).first()
        
        if not conciliacion:
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")
        
        return success_response(
            data={
                "id": conciliacion.id,
                "fecha_conciliacion": conciliacion.fecha_conciliacion.isoformat() if conciliacion.fecha_conciliacion else None,
                "fecha_cierre": conciliacion.fecha_cierre,
                "sucursal": conciliacion.sucursal,
                "cajero": conciliacion.cajero,
                "archivo_cierre_nombre": conciliacion.archivo_cierre_nombre,
                "archivo_yappy_nombre": conciliacion.archivo_yappy_nombre,
                "archivo_banco_nombre": conciliacion.archivo_banco_nombre,
                "totales": conciliacion.totales,
                "resultados_yappy": conciliacion.resultados_yappy,
                "resultados_banco": conciliacion.resultados_banco,
                "total_coincidencias_exactas": conciliacion.total_coincidencias_exactas,
                "total_coincidencias_parciales": conciliacion.total_coincidencias_parciales,
                "total_sin_coincidencia": conciliacion.total_sin_coincidencia,
                "estado": conciliacion.estado,
                "notas": conciliacion.notas,
                "created_at": conciliacion.created_at.isoformat() if conciliacion.created_at else None,
                "updated_at": conciliacion.updated_at.isoformat() if conciliacion.updated_at else None
            },
            message="Conciliación obtenida correctamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error obteniendo conciliación {id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener conciliación: {str(e)}"
        )


@router.post("/historial")
async def guardar_conciliacion(
    datos: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Guarda una nueva conciliación.
    """
    try:
        # Calcular estadísticas
        resultados_yappy = datos.get("resultados_yappy", [])
        resultados_banco = datos.get("resultados_banco", [])
        
        total_exactas = sum(1 for r in resultados_yappy + resultados_banco if r.get("estado") == "exacta")
        total_parciales = sum(1 for r in resultados_yappy + resultados_banco if r.get("estado") == "parcial")
        total_sin = sum(1 for r in resultados_yappy + resultados_banco if r.get("estado") == "sin_coincidencia")
        
        conciliacion = Conciliacion(
            fecha_cierre=datos.get("fecha_cierre"),
            sucursal=datos.get("sucursal"),
            cajero=datos.get("cajero"),
            archivo_cierre_nombre=datos.get("archivo_cierre_nombre"),
            archivo_yappy_nombre=datos.get("archivo_yappy_nombre"),
            archivo_banco_nombre=datos.get("archivo_banco_nombre"),
            totales=datos.get("totales"),
            resultados_yappy=resultados_yappy,
            resultados_banco=resultados_banco,
            total_coincidencias_exactas=total_exactas,
            total_coincidencias_parciales=total_parciales,
            total_sin_coincidencia=total_sin,
            estado=datos.get("estado", "completa"),
            notas=datos.get("notas")
        )
        
        db.add(conciliacion)
        db.commit()
        db.refresh(conciliacion)
        
        return success_response(
            data={"id": conciliacion.id},
            message="Conciliación guardada correctamente"
        )
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"Error guardando conciliación: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar conciliación: {str(e)}"
        )


@router.delete("/historial/{id}")
async def eliminar_conciliacion(
    id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Elimina una conciliación.
    """
    try:
        conciliacion = db.query(Conciliacion).filter(Conciliacion.id == id).first()
        
        if not conciliacion:
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")
        
        db.delete(conciliacion)
        db.commit()
        
        return success_response(
            data={"id": id},
            message="Conciliación eliminada correctamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        app_logger.error(f"Error eliminando conciliación {id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar conciliación: {str(e)}"
        )

