"""
Modelos de datos para conciliaciones.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ConciliacionModel(Base):
    """Modelo SQLAlchemy para conciliaciones."""
    
    __tablename__ = "conciliaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha_conciliacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_cierre = Column(String, nullable=True)
    sucursal = Column(String, nullable=True)
    cajero = Column(String, nullable=True)
    
    # Archivos procesados
    archivo_cierre_nombre = Column(String, nullable=True)
    archivo_yappy_nombre = Column(String, nullable=True)
    archivo_banco_nombre = Column(String, nullable=True)
    
    # Resultados
    totales = Column(JSON, nullable=True)
    resultados_yappy = Column(JSON, nullable=True)
    resultados_banco = Column(JSON, nullable=True)
    
    # Estadísticas
    total_coincidencias_exactas = Column(Integer, default=0)
    total_coincidencias_parciales = Column(Integer, default=0)
    total_sin_coincidencia = Column(Integer, default=0)
    
    # Estado
    estado = Column(String, default="completa")
    notas = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

