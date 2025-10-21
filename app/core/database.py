from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import structlog

from app.core.config import settings, get_database_url

logger = structlog.get_logger()

# URL de base de datos
DATABASE_URL = get_database_url()

# Configuración del engine según el tipo de BD
if "sqlite" in DATABASE_URL:
    # Configuración para SQLite (desarrollo local)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # Configuración para PostgreSQL (Supabase/producción)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db() -> Session:
    """
    Dependencia para obtener sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_database():
    """
    Inicializar base de datos
    """
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully", database_url=DATABASE_URL)
    except Exception as e:
        logger.error("Error initializing database", error=str(e), database_url=DATABASE_URL)
        raise


async def check_database_connection() -> bool:
    """
    Verificar conexión a la base de datos
    """
    try:
        db = SessionLocal()
        # Ejecutar una consulta simple
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False