"""
Modelo de datos para productos
"""
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    sku = Column(String(100), unique=True, index=True)
    stock_quantity = Column(Integer, default=0)
    category = Column(String(100))
    active = Column(Boolean, default=True, index=True)
    
    # Metadatos adicionales como JSON
    attributes = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

    def to_dict(self):
        """Convertir a diccionario para serialización"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "category": self.category,
            "active": self.active,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }