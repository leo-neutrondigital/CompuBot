from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings
    """
    
    # Configuración general
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True
    API_BASE_URL: str = "http://localhost:8000"  # URL base de la API
    
    # Base de datos
    DATABASE_URL: str = "sqlite:///./computel_bot.db"  # Default para desarrollo local
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_MAX_TOKENS: int = 1000
    
    # WhatsApp
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    
    # WooCommerce
    WOOCOMMERCE_URL: Optional[str] = None
    WOOCOMMERCE_KEY: Optional[str] = None
    WOOCOMMERCE_SECRET: Optional[str] = None
    
    # Configuración del bot
    DEFAULT_TAX_RATE: float = 16.0
    QUOTE_VALIDITY_DAYS: int = 30
    MAX_CONVERSATION_TIMEOUT_HOURS: int = 2
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()


def get_database_url() -> str:
    """
    Obtener URL de base de datos, priorizando Supabase si está configurado
    """
    if settings.SUPABASE_URL and "postgresql" in settings.DATABASE_URL:
        return settings.DATABASE_URL
    elif settings.DATABASE_URL:
        return settings.DATABASE_URL
    else:
        # Fallback a SQLite para desarrollo local
        return "sqlite:///./computel_bot.db"


def is_production() -> bool:
    """Verificar si estamos en producción"""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Verificar si estamos en desarrollo"""
    return settings.ENVIRONMENT.lower() == "development"