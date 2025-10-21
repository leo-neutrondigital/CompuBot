"""
Repositorio para gestión de productos
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.core.repository import BaseRepository
from app.models.product import Product


class ProductRepository(BaseRepository[Product, dict, dict]):
    def __init__(self):
        super().__init__(Product)

    def search_products(
        self, 
        db: Session, 
        query: str, 
        limit: int = 10
    ) -> List[Product]:
        """Buscar productos por nombre o descripción con algoritmo mejorado"""
        import unicodedata
        import re
        
        # Normalizar query (quitar acentos y convertir a minúsculas)
        normalized_query = self._normalize_search_term(query)
        
        # Dividir en palabras individuales para búsqueda flexible
        words = [word.strip() for word in normalized_query.split() if len(word.strip()) > 2]
        
        if not words:
            return []
        
        # Buscar productos que contengan todas las palabras
        results = db.query(Product).filter(Product.active == True)
        
        for word in words:
            search_term = f"%{word}%"
            results = results.filter(
                or_(
                    func.lower(func.replace(func.replace(func.replace(func.replace(func.replace(
                        Product.name, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u')).contains(search_term),
                    func.lower(func.replace(func.replace(func.replace(func.replace(func.replace(
                        Product.description, 'á', 'a'), 'é', 'e'), 'í', 'i'), 'ó', 'o'), 'ú', 'u')).contains(search_term),
                    Product.sku.ilike(search_term)
                )
            )
        
        return results.limit(limit).all()
    
    def _normalize_search_term(self, text: str) -> str:
        """Normalizar texto para búsqueda (quitar acentos, minúsculas)"""
        import unicodedata
        # Quitar acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text.lower().strip()

    def get_by_sku(self, db: Session, sku: str) -> Optional[Product]:
        """Obtener producto por SKU"""
        return db.query(Product).filter(
            Product.sku == sku,
            Product.active == True
        ).first()

    def get_available_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        """Obtener productos disponibles"""
        return db.query(Product).filter(
            Product.active == True,
            Product.stock_quantity > 0
        ).offset(skip).limit(limit).all()

    def create_product(
        self, 
        db: Session,
        name: str,
        price: float,
        description: str = None,
        sku: str = None,
        stock_quantity: int = 0
    ) -> Product:
        """Crear un nuevo producto"""
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "stock_quantity": stock_quantity,
            "active": True
        }
        return self.create(db, obj_in=product_data)

    def update_stock(self, db: Session, product_id: str, new_quantity: int) -> Optional[Product]:
        """Actualizar stock de un producto"""
        product = self.get(db, product_id)
        if product:
            return self.update(db, db_obj=product, obj_in={"stock_quantity": new_quantity})
        return None

    def get_low_stock_products(self, db: Session, threshold: int = 5) -> List[Product]:
        """Obtener productos con stock bajo"""
        return db.query(Product).filter(
            Product.active == True,
            Product.stock_quantity <= threshold
        ).all()

    def bulk_create_products(self, db: Session, products_data: List[dict]) -> List[Product]:
        """Crear múltiples productos de una vez"""
        products = []
        for product_data in products_data:
            product = Product(**product_data)
            products.append(product)
        
        db.add_all(products)
        db.commit()
        
        for product in products:
            db.refresh(product)
        
        return products


# Instancia global del repositorio
product_repository = ProductRepository()