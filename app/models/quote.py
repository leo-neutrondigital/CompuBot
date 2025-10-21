from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func, JSON, Numeric
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.user import BaseModel


class Quote(BaseModel):
    """
    Modelo para cotizaciones generadas
    """
    __tablename__ = "quotes"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Número único de cotización (Q2025-001234)
    quote_number = Column(String(20), unique=True, nullable=False)
    
    # Información del cliente (snapshot del momento)
    client_info = Column(JSON, default={}, nullable=False)
    
    # Cálculos financieros
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 2), default=16.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False)
    shipping_cost = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Archivos
    pdf_path = Column(String(500), nullable=True)
    pdf_size_bytes = Column(Integer, nullable=True)
    
    # Estados: draft, sent, viewed, accepted, rejected, expired
    status = Column(String(20), default="draft", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    valid_until = Column(DateTime, nullable=True)  # 30 días por defecto
    
    # Tracking
    view_count = Column(Integer, default=0, nullable=False)
    last_viewed = Column(DateTime, nullable=True)
    
    # Notas
    internal_notes = Column(Text, nullable=True)
    client_notes = Column(Text, nullable=True)
    
    # Fechas
    sent_at = Column(DateTime, nullable=True)
    
    # Relaciones
    user = relationship("User", back_populates="quotes")
    conversation = relationship("Conversation", back_populates="quotes")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quote(number={self.quote_number}, total=${self.total}, status={self.status})>"


class QuoteItem(BaseModel):
    """
    Modelo para items individuales de cada cotización
    """
    __tablename__ = "quote_items"
    
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    
    # Información del producto (snapshot para histórico)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=True)
    product_description = Column(Text, nullable=True)
    
    # Cantidades y precios
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    
    # Orden en la cotización
    line_order = Column(Integer, default=1, nullable=False)
    
    # Relaciones
    quote = relationship("Quote", back_populates="items")
    
    def __repr__(self):
        return f"<QuoteItem(product={self.product_name}, qty={self.quantity}, total=${self.total_price})>"