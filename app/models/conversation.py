from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.user import BaseModel


class Conversation(BaseModel):
    """
    Modelo para conversaciones activas de WhatsApp
    """
    __tablename__ = "conversations"
    
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    whatsapp_chat_id = Column(String(100), nullable=False, index=True)
    whatsapp_message_id = Column(String(100), nullable=True)
    
    # Estados: active, paused, completed, cancelled, timeout
    status = Column(String(20), default="active", nullable=False)
    
    # Estados conversacionales: conversando, recopilando, validando, revisando, cotizando
    current_state = Column(String(30), default="conversando", nullable=False)
    
    # Datos de contexto de la conversación (JSON)
    context = Column(JSON, default={}, nullable=False)
    
    # Historial de intenciones detectadas
    intent_history = Column(JSON, default=[], nullable=False)
    
    # Productos en progreso (temporal)
    products_in_progress = Column(JSON, default=[], nullable=False)
    
    # Resumen de la conversación al finalizar
    conversation_summary = Column(Text, nullable=True)
    
    # Estadísticas
    total_messages = Column(Integer, default=0, nullable=False)
    
    # Fechas importantes
    last_activity = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)  # 2 horas por defecto
    
    # Relaciones
    user = relationship("User", back_populates="conversations")
    quotes = relationship("Quote", back_populates="conversation")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ConversationMessage(BaseModel):
    """
    Modelo para mensajes individuales de conversación (debugging/análisis)
    """
    __tablename__ = "conversation_messages"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    
    # Tipos: user, bot, system, webhook
    message_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    # Análisis del mensaje
    intent_detected = Column(String(50), nullable=True)
    confidence = Column(String(10), nullable=True)  # 0.00-1.00 as string
    processing_time_ms = Column(Integer, nullable=True)
    
    # Metadatos adicionales (tokens, errores, etc.)
    message_metadata = Column(JSON, default={}, nullable=False)
    whatsapp_message_id = Column(String(100), nullable=True)
    
    # Relaciones
    conversation = relationship("Conversation")
    
    def __repr__(self):
        return f"<Message(type={self.message_type}, content={self.content[:50]}...)>"