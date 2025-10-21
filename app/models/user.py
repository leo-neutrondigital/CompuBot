from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class BaseModel(Base):
    """
    Modelo base con campos comunes para todas las tablas
    Usa String para IDs para compatibilidad con SQLite
    """
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class User(BaseModel):
    """
    Modelo para usuarios autorizados del sistema
    """
    __tablename__ = "users"
    
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(20), default="employee", nullable=False)  # admin, manager, employee
    department = Column(String(50), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    conversations = relationship("Conversation", back_populates="user")
    quotes = relationship("Quote", back_populates="user")
    
    def __repr__(self):
        return f"<User(phone={self.phone_number}, name={self.name}, role={self.role})>"