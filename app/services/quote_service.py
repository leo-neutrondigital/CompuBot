"""
Servicio para gestión de cotizaciones
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from app.repositories.quote_repository import quote_repository
from app.repositories.product_repository import product_repository
from app.services.pdf_service import pdf_service
from app.models.quote import Quote

logger = structlog.get_logger()


class QuoteService:
    def __init__(self):
        self.quote_repo = quote_repository
        self.product_repo = product_repository
        self.pdf_service = pdf_service

    async def create_quote_from_conversation(
        self,
        db: Session,
        conversation_id: str,
        user_id: str,
        products_data: List[Dict[str, Any]],
        client_info: Dict[str, Any] = None
    ) -> Quote:
        """
        Crear cotización a partir de datos de conversación
        
        Args:
            db: Sesión de base de datos
            conversation_id: ID de la conversación
            user_id: ID del usuario que genera la cotización
            products_data: Lista de productos con cantidades
            client_info: Información adicional del cliente
            
        Returns:
            Quote: Cotización creada
        """
        try:
            logger.info(
                "Creating quote from conversation",
                conversation_id=conversation_id,
                user_id=user_id,
                products_count=len(products_data)
            )
            
            # Preparar items de la cotización
            quote_items = []
            
            for product_data in products_data:
                # Obtener información actualizada del producto
                product_options = product_data.get("options", [])
                if not product_options:
                    continue
                    
                # Usar el primer producto (mejor match)
                product_info = product_options[0]
                requested_quantity = product_data.get("requested", {}).get("quantity", 1)
                
                # Validar que el producto aún existe y tiene stock
                product = self.product_repo.get(db, product_info["id"])
                if not product or not product.active:
                    logger.warning("Product not found or inactive", product_id=product_info["id"])
                    continue
                
                # Verificar stock disponible
                if product.stock_quantity < requested_quantity:
                    logger.warning(
                        "Insufficient stock", 
                        product_id=product.id,
                        requested=requested_quantity,
                        available=product.stock_quantity
                    )
                    # Usar la cantidad disponible
                    requested_quantity = max(1, product.stock_quantity)
                
                # Agregar item a la cotización
                item_data = {
                    "product_name": product.name,
                    "product_sku": product.sku,
                    "product_description": product.description,
                    "quantity": requested_quantity,
                    "unit_price": float(product.price),
                    "total_price": requested_quantity * float(product.price)
                }
                
                quote_items.append(item_data)
            
            if not quote_items:
                raise ValueError("No se pudieron procesar los productos para la cotización")
            
            # Crear la cotización
            quote = self.quote_repo.create_quote(
                db, conversation_id, user_id, quote_items
            )
            
            logger.info("Quote created successfully", quote_id=quote.id, quote_number=quote.quote_number)
            return quote
            
        except Exception as e:
            logger.error("Error creating quote", error=str(e))
            raise

    async def generate_quote_pdf(
        self,
        db: Session,
        quote_id: str,
        client_name: str = "Cliente"
    ) -> str:
        """
        Generar PDF para una cotización existente
        
        Args:
            db: Sesión de base de datos
            quote_id: ID de la cotización
            client_name: Nombre del cliente
            
        Returns:
            str: Ruta al archivo PDF generado
        """
        try:
            # Obtener la cotización
            quote = self.quote_repo.get(db, quote_id)
            if not quote:
                raise ValueError(f"Cotización no encontrada: {quote_id}")
            
            # Obtener items de la cotización
            from app.repositories.quote_repository import quote_item_repository
            quote_items = quote_item_repository.get_by_quote(db, quote_id)
            
            # Preparar datos para el PDF
            pdf_data = {
                "quote_number": quote.quote_number,
                "client_name": client_name,
                "valid_until": (quote.valid_until or datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
                "subtotal": float(quote.subtotal),
                "tax_rate": float(quote.tax_rate),
                "tax_amount": float(quote.tax_amount),
                "total": float(quote.total),
                "items": [
                    {
                        "quantity": item.quantity,
                        "product_name": item.product_name,
                        "unit_price": float(item.unit_price),
                        "total_price": float(item.total_price)
                    }
                    for item in quote_items
                ]
            }
            
            logger.info("Generating PDF for quote", quote_id=quote_id, quote_number=quote.quote_number)
            
            # Generar PDF
            pdf_path = await self.pdf_service.generate_quote_pdf(pdf_data)
            
            # Actualizar la cotización con la ruta del PDF
            self.quote_repo.add_pdf_path(db, quote_id, pdf_path)
            
            # Marcar como enviada
            self.quote_repo.update_status(db, quote_id, "sent")
            
            logger.info("PDF generated and quote updated", pdf_path=pdf_path)
            return pdf_path
            
        except Exception as e:
            logger.error("Error generating quote PDF", quote_id=quote_id, error=str(e))
            raise

    def get_quote_summary(self, db: Session, quote_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener resumen de una cotización
        
        Args:
            db: Sesión de base de datos
            quote_id: ID de la cotización
            
        Returns:
            Dict: Resumen de la cotización o None si no existe
        """
        try:
            quote = self.quote_repo.get(db, quote_id)
            if not quote:
                return None
            
            from app.repositories.quote_repository import quote_item_repository
            quote_items = quote_item_repository.get_by_quote(db, quote_id)
            
            return {
                "quote_id": quote.id,
                "quote_number": quote.quote_number,
                "status": quote.status,
                "total": float(quote.total),
                "item_count": len(quote_items),
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "pdf_path": quote.pdf_path,
                "items": [
                    {
                        "name": item.product_name,
                        "quantity": item.quantity,
                        "unit_price": float(item.unit_price),
                        "total": float(item.total_price)
                    }
                    for item in quote_items
                ]
            }
            
        except Exception as e:
            logger.error("Error getting quote summary", quote_id=quote_id, error=str(e))
            return None

    def prepare_products_for_quote(self, products_in_progress: List[Dict]) -> List[Dict[str, Any]]:
        """
        Preparar productos de conversación para crear cotización
        
        Args:
            products_in_progress: Lista de productos desde la conversación
            
        Returns:
            List: Lista de productos preparada para cotización
        """
        prepared_products = []
        
        for product_data in products_in_progress:
            if "options" in product_data and product_data["options"]:
                # Tomar el mejor match (primer elemento)
                best_option = product_data["options"][0]
                requested = product_data.get("requested", {})
                
                prepared_product = {
                    "requested": {
                        "name": requested.get("name", ""),
                        "quantity": requested.get("quantity", 1),
                        "unit": requested.get("unit", "piezas")
                    },
                    "options": [best_option]
                }
                
                prepared_products.append(prepared_product)
        
        return prepared_products

    async def validate_products_availability(
        self, 
        db: Session, 
        products_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validar disponibilidad de productos para cotización
        
        Args:
            db: Sesión de base de datos
            products_data: Lista de productos a validar
            
        Returns:
            Dict: Resultado de validación con productos disponibles e issues
        """
        validation_result = {
            "valid": True,
            "available_products": [],
            "issues": []
        }
        
        for product_data in products_data:
            options = product_data.get("options", [])
            if not options:
                continue
                
            product_info = options[0]
            requested_quantity = product_data.get("requested", {}).get("quantity", 1)
            
            # Verificar producto en BD
            product = self.product_repo.get(db, product_info["id"])
            
            if not product:
                validation_result["issues"].append(f"Producto no encontrado: {product_info.get('name')}")
                validation_result["valid"] = False
                continue
                
            if not product.active:
                validation_result["issues"].append(f"Producto no disponible: {product.name}")
                validation_result["valid"] = False
                continue
            
            if product.stock_quantity < requested_quantity:
                validation_result["issues"].append(
                    f"Stock insuficiente para {product.name}. "
                    f"Solicitado: {requested_quantity}, Disponible: {product.stock_quantity}"
                )
                # No marcamos como inválido, solo ajustamos cantidad
            
            validation_result["available_products"].append({
                "product": product,
                "requested_quantity": requested_quantity,
                "available_quantity": product.stock_quantity,
                "adjusted_quantity": min(requested_quantity, product.stock_quantity)
            })
        
        return validation_result


# Instancia global del servicio
quote_service = QuoteService()