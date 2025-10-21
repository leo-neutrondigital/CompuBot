"""
Repositorio para gestión de cotizaciones
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.repository import BaseRepository
from app.models.quote import Quote, QuoteItem


class QuoteRepository(BaseRepository[Quote, dict, dict]):
    def __init__(self):
        super().__init__(Quote)

    def create_quote(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        items_data: List[dict]
    ) -> Quote:
        """Crear una nueva cotización con sus items"""
        
        # Calcular totales
        subtotal = sum(item["quantity"] * item["unit_price"] for item in items_data)
        tax_rate = 16.0  # 16% IVA
        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount
        
        # Generar número de cotización único
        quote_number = self._generate_quote_number(db)
        
        # Crear cotización
        quote_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "quote_number": quote_number,
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total": total,
            "status": "draft",
            "valid_until": datetime.now() + timedelta(days=30)
        }
        
        quote = self.create(db, obj_in=quote_data)
        
        # Crear items de la cotización
        for item_data in items_data:
            item_data["quote_id"] = quote.id
            item = QuoteItem(**item_data)
            db.add(item)
        
        db.commit()
        db.refresh(quote)
        return quote

    def get_by_quote_number(self, db: Session, quote_number: str) -> Optional[Quote]:
        """Obtener cotización por número"""
        return db.query(Quote).filter(Quote.quote_number == quote_number).first()

    def get_quotes_by_user(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Quote]:
        """Obtener cotizaciones de un usuario"""
        return db.query(Quote).filter(
            Quote.user_id == user_id
        ).order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()

    def get_quotes_by_status(
        self, 
        db: Session, 
        status: str, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Quote]:
        """Obtener cotizaciones por estado"""
        return db.query(Quote).filter(
            Quote.status == status
        ).order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()

    def update_status(self, db: Session, quote_id: str, new_status: str) -> Optional[Quote]:
        """Actualizar estado de cotización"""
        quote = self.get(db, quote_id)
        if quote:
            update_data = {"status": new_status}
            if new_status == "sent":
                update_data["sent_at"] = datetime.now()
            return self.update(db, db_obj=quote, obj_in=update_data)
        return None

    def get_expired_quotes(self, db: Session) -> List[Quote]:
        """Obtener cotizaciones expiradas"""
        return db.query(Quote).filter(
            Quote.valid_until < datetime.now(),
            Quote.status.in_(["sent", "viewed"])
        ).all()

    def add_pdf_path(self, db: Session, quote_id: str, pdf_path: str) -> Optional[Quote]:
        """Agregar ruta del PDF generado"""
        quote = self.get(db, quote_id)
        if quote:
            return self.update(db, db_obj=quote, obj_in={"pdf_path": pdf_path})
        return None

    def _generate_quote_number(self, db: Session) -> str:
        """
        Generar número único de cotización en formato COT-YYYYMMDD-NNN
        Ejemplo: COT-20251020-001
        """
        from datetime import datetime
        
        # Obtener fecha actual en formato YYYYMMDD
        date_str = datetime.now().strftime("%Y%m%d")
        prefix = f"COT-{date_str}"
        
        # Buscar el último número de cotización del día
        last_quote = db.query(Quote).filter(
            Quote.quote_number.like(f"{prefix}%")
        ).order_by(Quote.quote_number.desc()).first()
        
        if last_quote:
            # Extraer el número secuencial y aumentarlo
            last_number = int(last_quote.quote_number.split("-")[-1])
            next_number = last_number + 1
        else:
            # Primera cotización del día
            next_number = 1
        
        # Formatear con 3 dígitos
        return f"{prefix}-{next_number:03d}"


class QuoteItemRepository(BaseRepository[QuoteItem, dict, dict]):
    def __init__(self):
        super().__init__(QuoteItem)

    def get_by_quote(self, db: Session, quote_id: str) -> List[QuoteItem]:
        """Obtener items de una cotización"""
        return db.query(QuoteItem).filter(
            QuoteItem.quote_id == quote_id
        ).order_by(QuoteItem.created_at).all()

    def update_quantity(self, db: Session, item_id: str, new_quantity: int) -> Optional[QuoteItem]:
        """Actualizar cantidad de un item"""
        item = self.get(db, item_id)
        if item:
            new_total = new_quantity * item.unit_price
            return self.update(db, db_obj=item, obj_in={
                "quantity": new_quantity,
                "total_price": new_total
            })
        return None


# Instancias globales
quote_repository = QuoteRepository()
quote_item_repository = QuoteItemRepository()