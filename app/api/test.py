"""
Endpoints de testing y desarrollo
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import structlog
import os
from pathlib import Path

from app.core.database import get_db
from app.services.user_service import user_service
from app.repositories.product_repository import product_repository
from app.services.woocommerce_service import WooCommerceService
from app.services.conversation_engine import conversation_engine
from app.models.user import User
from app.models.product import Product
from app.models.quote import Quote

logger = structlog.get_logger()
router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/")
async def test_endpoint():
    """Endpoint básico de prueba"""
    return {"message": "Test endpoint working!", "status": "ok"}


@router.post("/users")
async def create_test_user(
    phone_number: str,
    name: str,
    role: str = "employee",
    db: Session = Depends(get_db)
):
    """Crear usuario de prueba"""
    try:
        user = user_service.create_user(db, phone_number, name, role)
        return {
            "message": "Usuario creado exitosamente",
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "name": user.name,
                "role": user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{phone_number}")
async def get_user_by_phone(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """Obtener usuario por teléfono"""
    user = user_service.get_user_by_phone(db, phone_number)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "user": {
            "id": user.id,
            "phone_number": user.phone_number,
            "name": user.name,
            "role": user.role,
            "active": user.active
        }
    }


@router.post("/products")
async def create_test_product(
    name: str,
    price: float,
    description: str = None,
    sku: str = None,
    stock_quantity: int = 0,
    db: Session = Depends(get_db)
):
    """Crear producto de prueba"""
    try:
        product = product_repository.create_product(
            db, name, price, description, sku, stock_quantity
        )
        return {
            "message": "Producto creado exitosamente",
            "product": product.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products/search")
async def search_products(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Buscar productos"""
    products = product_repository.search_products(db, q, limit)
    return {
        "query": q,
        "found": len(products),
        "products": [product.to_dict() for product in products]
    }


@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Listar productos disponibles"""
    products = product_repository.get_available_products(db, skip, limit)
    return {
        "total": len(products),
        "products": [product.to_dict() for product in products]
    }


@router.post("/sample-data")
async def create_sample_data(db: Session = Depends(get_db)):
    """Crear datos de muestra para testing"""
    try:
        # Crear usuarios de prueba
        users_data = [
            {"phone_number": "5215551234567", "name": "Admin Usuario", "role": "admin"},
            {"phone_number": "5215557654321", "name": "Empleado Test", "role": "employee"},
            {"phone_number": "5215559876543", "name": "Manager Test", "role": "manager"}
        ]
        
        created_users = []
        for user_data in users_data:
            try:
                user = user_service.create_user(db, **user_data)
                created_users.append(user.phone_number)
            except:
                pass  # Usuario ya existe
        
        # Crear productos de prueba
        products_data = [
            {"name": "Papel Bond A4", "price": 2.50, "description": "Papel bond blanco tamaño carta", "sku": "PB-A4-001", "stock_quantity": 100},
            {"name": "Lápiz #2", "price": 0.50, "description": "Lápiz de grafito número 2", "sku": "LAP-002", "stock_quantity": 200},
            {"name": "Borrador Rosa", "price": 0.25, "description": "Borrador rosa para lápiz", "sku": "BOR-001", "stock_quantity": 150},
            {"name": "Folder Manila", "price": 1.20, "description": "Folder manila tamaño carta", "sku": "FOL-MAN-001", "stock_quantity": 80},
            {"name": "Pluma Azul Bic", "price": 1.00, "description": "Pluma de tinta azul marca Bic", "sku": "PLU-BIC-AZ", "stock_quantity": 120},
            {"name": "Cuaderno 100 hojas", "price": 5.50, "description": "Cuaderno rayado 100 hojas", "sku": "CUA-100-001", "stock_quantity": 60},
            {"name": "Marcador Negro", "price": 2.00, "description": "Marcador permanente negro", "sku": "MAR-NEG-001", "stock_quantity": 90},
            {"name": "Cinta Adhesiva", "price": 3.50, "description": "Cinta adhesiva transparente", "sku": "CIN-ADH-001", "stock_quantity": 75}
        ]
        
        created_products = []
        for product_data in products_data:
            try:
                product = product_repository.create_product(db, **product_data)
                created_products.append(product.name)
            except:
                pass  # Producto ya existe
        
        return {
            "message": "Datos de muestra creados exitosamente",
            "users_created": created_users,
            "products_created": created_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando datos de muestra: {str(e)}")


@router.post("/test-conversation")
async def test_conversation_flow(
    user_phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Probar flujo completo de conversación"""
    from app.services.user_service import user_service
    from app.repositories.conversation_repository import conversation_repository
    
    try:
        # Autenticar usuario
        logger.info("TEST: Starting conversation test", user_phone=user_phone, message=message)
        user = user_service.authenticate_user(db, user_phone)
        if not user:
            return {"error": "Usuario no encontrado", "user_phone": user_phone}
        
        # Obtener o crear conversación
        conversation = conversation_repository.get_active_by_user(db, user.id)
        if not conversation:
            conversation = conversation_repository.create_conversation(
                db, user.id, f"test_chat_{user.id}"
            )
        
        # Procesar mensaje
        logger.info("🔍 TRACE: About to call conversation_engine.process_message", 
                   user_id=user.id, message=message, state=conversation.current_state)
        
        # Verificar que el objeto es el correcto
        logger.info("🔍 TRACE: conversation_engine object info", 
                   engine_class=type(conversation_engine).__name__,
                   engine_module=type(conversation_engine).__module__)
        
        response = await conversation_engine.process_message(
            db, user, conversation, message
        )
        
        # CRITICAL: Re-obtener conversation desde la BD después del procesamiento
        from app.repositories.conversation_repository import conversation_repository
        conversation = conversation_repository.get(db, conversation.id)
        
        logger.info("🔍 TRACE: Conversation engine completed", 
                   response_length=len(response), 
                   response_preview=response[:100] if response else "None")

        # Preparar respuesta base
        response_data = {
            "user": {"name": user.name, "phone": user.phone_number},
            "conversation_id": conversation.id,
            "current_state": conversation.current_state,
            "message": message,
            "response": response,
            "context": conversation.context,
            "products_in_progress": conversation.products_in_progress
        }
        
        # Si hay información de PDF en el contexto, agregarla a la respuesta
        if conversation.context and isinstance(conversation.context, dict):
            if conversation.context.get("last_quote_id"):
                response_data["quote_id"] = conversation.context["last_quote_id"]
                # Importar settings para obtener la URL base
                from app.core.config import settings
                response_data["pdf_url"] = f"{settings.API_BASE_URL}/test/quotes/{conversation.context['last_quote_id']}/pdf"
            if conversation.context.get("last_quote_number"):
                response_data["quote_number"] = conversation.context["last_quote_number"]
        
        return response_data
        
    except Exception as e:
        logger.error("TEST ENDPOINT ERROR", error=str(e), traceback=str(e.__traceback__))
        raise HTTPException(status_code=500, detail=f"Error en conversación: {str(e)}")
@router.get("/quotes")
async def list_quotes(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Listar cotizaciones existentes"""
    from app.repositories.quote_repository import quote_repository
    
    quotes = quote_repository.get_multi(db, skip=skip, limit=limit)
    
    return {
        "total": len(quotes),
        "quotes": [
            {
                "id": quote.id,
                "quote_number": quote.quote_number,
                "status": quote.status,
                "total": float(quote.total),
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "pdf_path": quote.pdf_path
            }
            for quote in quotes
        ]
    }


@router.post("/woocommerce/sync-mock")
async def sync_mock_woocommerce_products(db: Session = Depends(get_db)):
    """Sincronizar productos mock de WooCommerce (para testing local)"""
    from app.services.woocommerce_service import woocommerce_service
    
    try:
        # Obtener productos mock
        mock_products = await woocommerce_service.create_mock_woocommerce_data()
        
        # Sincronizar a base de datos
        created_count = 0
        updated_count = 0
        
        for product_data in mock_products:
            try:
                # Buscar producto existente por SKU
                existing_product = product_repository.get_by_sku(db, product_data.get("sku", ""))
                
                if existing_product:
                    # Actualizar producto existente
                    product_repository.update(db, db_obj=existing_product, obj_in=product_data)
                    updated_count += 1
                else:
                    # Crear nuevo producto
                    product_repository.create(db, obj_in=product_data)
                    created_count += 1
                    
            except Exception as e:
                continue  # Saltar errores individuales
        
        return {
            "message": "Sincronización mock de WooCommerce completada",
            "products_created": created_count,
            "products_updated": updated_count,
            "total_processed": len(mock_products)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en sincronización: {str(e)}")


@router.get("/woocommerce/test-connection")
async def test_woocommerce_connection():
    """Probar conexión con WooCommerce (requiere configuración real)"""
    from app.services.woocommerce_service import woocommerce_service
    
    result = await woocommerce_service.test_connection()
    
    if result["status"] == "error":
        return {
            "status": "error",
            "message": result["message"],
            "note": "Para testing local, usa el endpoint /test/woocommerce/sync-mock"
        }
    
    return result


@router.delete("/reset-data")
async def reset_test_data(db: Session = Depends(get_db)):
    """Limpiar todos los datos de prueba (CUIDADO!)"""
    try:
        # Eliminar todos los productos
        db.query(Product).delete()
        
        # Eliminar todos los usuarios
        db.query(User).delete()
        
        db.commit()
        
        return {"message": "Todos los datos de prueba han sido eliminados"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando datos: {str(e)}")


@router.get("/woocommerce/test-connection")
async def test_woocommerce_connection():
    """Probar conexión con WooCommerce"""
    try:
        wc_service = WooCommerceService()
        result = await wc_service.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error probando conexión: {str(e)}")


@router.get("/woocommerce/products")
async def fetch_woocommerce_products(limit: int = 10):
    """Obtener productos de WooCommerce"""
    try:
        wc_service = WooCommerceService()
        products = await wc_service.fetch_products(per_page=limit)
        return {
            "total_products": len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")


@router.post("/woocommerce/sync-products")
async def sync_woocommerce_products(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Sincronizar productos de WooCommerce a base de datos local"""
    try:
        wc_service = WooCommerceService()
        result = await wc_service.sync_products_to_database(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando productos: {str(e)}")


@router.get("/woocommerce/mock-products")
async def get_mock_woocommerce_products():
    """Obtener productos mock de WooCommerce para testing"""
    try:
        wc_service = WooCommerceService()
        products = await wc_service.create_mock_woocommerce_data()
        return {
            "total_products": len(products),
            "products": products,
            "note": "Estos son datos mock para testing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos mock: {str(e)}")


@router.post("/woocommerce/sync-mock")
async def sync_mock_products_to_db(
    db: Session = Depends(get_db)
):
    """Sincronizar productos mock a la base de datos para testing"""
    try:
        wc_service = WooCommerceService()
        mock_products = await wc_service.create_mock_woocommerce_data()
        
        # Contar productos existentes
        existing_count = product_repository.count_all(db)
        
        # Agregar productos mock
        created_count = 0
        for product_data in mock_products:
            try:
                # Verificar si ya existe
                existing = product_repository.get_by_sku(db, product_data.get("sku", ""))
                if not existing:
                    product_repository.create_product(
                        db,
                        name=product_data["name"],
                        description=product_data.get("description", ""),
                        price=float(product_data["price"]),
                        sku=product_data.get("sku", ""),
                        category=product_data.get("category", "General"),
                        stock_quantity=product_data.get("stock_quantity", 0),
                        weight=product_data.get("weight"),
                        dimensions=product_data.get("dimensions", {}),
                        meta_data=product_data.get("meta_data", {})
                    )
                    created_count += 1
            except Exception as product_error:
                logger.warning(f"Error creando producto {product_data.get('name')}: {product_error}")
                continue
        
        return {
            "message": "Productos mock sincronizados exitosamente",
            "existing_products": existing_count,
            "new_products_added": created_count,
            "total_mock_products": len(mock_products)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando productos mock: {str(e)}")


@router.post("/test-openai")
async def test_openai_intent(
    message: str = Form(...),
    context: str = Form("{}"),
    db: Session = Depends(get_db)
):
    """Probar detección de intención con OpenAI directamente"""
    try:
        from app.services.openai_service import openai_service
        import json
        
        # Parsear contexto si viene como string
        try:
            context_dict = json.loads(context) if isinstance(context, str) else context
        except:
            context_dict = {}
        
        # Detectar intención
        intent_result = await openai_service.detect_intent(message, context_dict)
        
        # También probar extracción de productos
        products = await openai_service.extract_products_from_message(message)
        
        return {
            "message": message,
            "context": context_dict,
            "intent_result": intent_result,
            "detected_products": products,
            "openai_status": "working"
        }
        
    except Exception as e:
        logger.error("Error testing OpenAI", error=str(e))
        return {
            "message": message,
            "context": context_dict if 'context_dict' in locals() else {},
            "error": str(e),
            "openai_status": "failed"
        }

@router.get("/quotes/{quote_id}/pdf")
async def get_quote_pdf(
    quote_id: str,
    db: Session = Depends(get_db)
):
    """
    Servir PDF de cotización generado.
    """
    try:
        logger.info("PDF endpoint called", quote_id=quote_id)
        
        # Buscar la cotización
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            logger.error("Quote not found in database", quote_id=quote_id)
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        
        logger.info("Quote found", quote_id=quote_id, pdf_path=quote.pdf_path)
        
        # Verificar que la cotización tiene PDF
        if not quote.pdf_path:
            logger.error("PDF path not set", quote_id=quote_id)
            raise HTTPException(status_code=404, detail="PDF no ha sido generado")
        
        # Construir ruta absoluta del PDF
        # Si el path es relativo, convertirlo a absoluto desde el directorio actual
        pdf_path = Path(quote.pdf_path)
        if not pdf_path.is_absolute():
            pdf_path = Path.cwd() / pdf_path
        
        # Verificar que el archivo existe
        if not pdf_path.exists():
            logger.error("PDF file not found", quote_id=quote_id, path=str(pdf_path), cwd=str(Path.cwd()))
            raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")
        
        # Extraer solo el nombre del archivo para la descarga
        pdf_filename = f"cotizacion_{quote.quote_number}.pdf"
        
        # Servir el archivo
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error serving PDF", quote_id=quote_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al obtener PDF: {str(e)}")

