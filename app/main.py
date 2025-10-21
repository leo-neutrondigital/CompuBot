from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.api.webhooks import whatsapp

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_app() -> FastAPI:
    """
    Crear y configurar la aplicación FastAPI
    """
    app = FastAPI(
        title="Computel Bot - Sistema de Cotizaciones IA",
        description="Bot de WhatsApp para generar cotizaciones automáticas de papelería",
        version="1.0.0",
        debug=settings.DEBUG
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar dominios exactos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Incluir routers
    app.include_router(
        whatsapp.router,
        prefix="/webhooks",
        tags=["webhooks"]
    )
    
    # Router de testing (solo en desarrollo)
    if settings.ENVIRONMENT == "development":
        from app.api import test, chat_simulator
        app.include_router(test.router)
        app.include_router(chat_simulator.router)

    @app.get("/")
    async def root():
        """Health check básico"""
        return {
            "message": "Computel Bot API is running",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        }

    @app.get("/health")
    async def health_check():
        """Health check detallado"""
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "database": "connected",  # TODO: verificar conexión real
        }

    logger.info("FastAPI application created", environment=settings.ENVIRONMENT)
    return app

# Crear instancia de la aplicación
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )