"""
Configuración de base de datos para el sistema de conciliación.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path

# Base para modelos
Base = declarative_base()


class Conciliacion(Base):
    """Modelo para almacenar conciliaciones."""
    
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
    estado = Column(String, default="completa")  # completa, parcial, con_errores
    notas = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent.parent / 'data' / 'conciliador.db'}"
)

# Crear directorio de datos si no existe
if DATABASE_URL.startswith("sqlite"):
    db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Inicializa la base de datos creando las tablas."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Obtiene una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

