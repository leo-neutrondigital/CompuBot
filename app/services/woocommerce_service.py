"""
Servicio para integración con WooCommerce
"""
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.product_repository import product_repository

logger = structlog.get_logger()


class WooCommerceService:
    def __init__(self):
        self.base_url = settings.WOOCOMMERCE_URL
        self.consumer_key = settings.WOOCOMMERCE_KEY
        self.consumer_secret = settings.WOOCOMMERCE_SECRET
        
    async def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con WooCommerce"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
                
                async with session.get(
                    f"{self.base_url}/wp-json/wc/v3/system_status",
                    auth=auth
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "connected",
                            "store_info": {
                                "name": data.get("settings", {}).get("title", "N/A"),
                                "version": data.get("environment", {}).get("wp_version", "N/A"),
                                "wc_version": data.get("environment", {}).get("wc_version", "N/A")
                            }
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}: {await response.text()}"
                        }
        except Exception as e:
            logger.error("Error testing WooCommerce connection", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }

    async def fetch_products(self, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Obtener productos de WooCommerce"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
                
                params = {
                    "page": page,
                    "per_page": per_page,
                    "status": "publish",
                    "stock_status": "instock"
                }
                
                async with session.get(
                    f"{self.base_url}/wp-json/wc/v3/products",
                    auth=auth,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        products = await response.json()
                        return [self._transform_wc_product(product) for product in products]
                    else:
                        error_text = await response.text()
                        logger.error("Error fetching products", status=response.status, error=error_text)
                        return []
                        
        except Exception as e:
            logger.error("Error fetching WooCommerce products", error=str(e))
            return []

    async def sync_products_to_database(self, db: Session) -> Dict[str, Any]:
        """Sincronizar productos de WooCommerce a la base de datos local"""
        try:
            logger.info("Starting WooCommerce product sync")
            
            # Obtener productos de WooCommerce
            all_products = []
            page = 1
            
            while True:
                products = await self.fetch_products(page=page, per_page=100)
                if not products:
                    break
                    
                all_products.extend(products)
                page += 1
                
                # Evitar páginas infinitas
                if page > 10:  # Máximo 1000 productos
                    break
            
            if not all_products:
                return {
                    "status": "error",
                    "message": "No se pudieron obtener productos de WooCommerce"
                }
            
            # Sincronizar con base de datos
            created_count = 0
            updated_count = 0
            errors = []
            
            for product_data in all_products:
                try:
                    # Buscar producto existente por SKU o nombre
                    existing_product = None
                    if product_data.get("sku"):
                        existing_product = product_repository.get_by_sku(db, product_data["sku"])
                    
                    if existing_product:
                        # Actualizar producto existente
                        product_repository.update(
                            db, 
                            db_obj=existing_product, 
                            obj_in=product_data
                        )
                        updated_count += 1
                    else:
                        # Crear nuevo producto
                        product_repository.create(db, obj_in=product_data)
                        created_count += 1
                        
                except Exception as e:
                    errors.append(f"Error with product {product_data.get('name', 'Unknown')}: {str(e)}")
                    logger.error("Error syncing product", product=product_data.get('name'), error=str(e))
            
            return {
                "status": "success",
                "total_fetched": len(all_products),
                "created": created_count,
                "updated": updated_count,
                "errors": errors[:10]  # Solo primeros 10 errores
            }
            
        except Exception as e:
            logger.error("Error in product sync", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }

    def _transform_wc_product(self, wc_product: Dict[str, Any]) -> Dict[str, Any]:
        """Transformar producto de WooCommerce al formato de nuestra BD"""
        return {
            "name": wc_product.get("name", ""),
            "description": wc_product.get("description", ""),
            "price": float(wc_product.get("price", 0)),
            "sku": wc_product.get("sku", ""),
            "stock_quantity": wc_product.get("stock_quantity", 0) or 0,
            "category": self._get_main_category(wc_product.get("categories", [])),
            "active": wc_product.get("status") == "publish",
            "attributes": {
                "wc_id": wc_product.get("id"),
                "weight": wc_product.get("weight"),
                "dimensions": wc_product.get("dimensions", {}),
                "images": [img.get("src") for img in wc_product.get("images", [])],
                "tags": [tag.get("name") for tag in wc_product.get("tags", [])]
            }
        }

    def _get_main_category(self, categories: List[Dict]) -> Optional[str]:
        """Obtener la categoría principal del producto"""
        if not categories:
            return None
        
        # Tomar la primera categoría
        return categories[0].get("name", "Sin categoría")

    async def create_mock_woocommerce_data(self) -> List[Dict[str, Any]]:
        """
        Crear datos mock de WooCommerce para testing local
        (Simula lo que vendría de una tienda real)
        """
        mock_products = [
            {
                "id": 1,
                "name": "Papel Bond A4 Premium",
                "description": "Papel bond de alta calidad, ideal para impresiones profesionales",
                "price": "2.75",
                "sku": "PB-A4-PREM-001",
                "stock_quantity": 500,
                "status": "publish",
                "categories": [{"name": "Papel y Cartón"}],
                "images": [{"src": "https://example.com/papel-a4.jpg"}],
                "weight": "2.5",
                "dimensions": {"length": "29.7", "width": "21.0", "height": "0.1"}
            },
            {
                "id": 2,
                "name": "Lápiz Mongol #2 Caja x12",
                "description": "Caja con 12 lápices de grafito #2, marca Mongol",
                "price": "8.50",
                "sku": "LAP-MONGOL-12",
                "stock_quantity": 150,
                "status": "publish",
                "categories": [{"name": "Útiles Escolares"}],
                "images": [{"src": "https://example.com/lapiz-mongol.jpg"}],
                "weight": "0.2"
            },
            {
                "id": 3,
                "name": "Calculadora Científica Casio FX-991",
                "description": "Calculadora científica con 417 funciones",
                "price": "285.00",
                "sku": "CALC-CASIO-FX991",
                "stock_quantity": 25,
                "status": "publish",
                "categories": [{"name": "Electrónicos"}],
                "images": [{"src": "https://example.com/calculadora-casio.jpg"}],
                "weight": "0.11"
            },
            {
                "id": 4,
                "name": "Folder Manila Carta Pack x25",
                "description": "Pack de 25 folders manila tamaño carta",
                "price": "35.00",
                "sku": "FOL-MAN-25",
                "stock_quantity": 80,
                "status": "publish",
                "categories": [{"name": "Organización"}],
                "images": [{"src": "https://example.com/folder-manila.jpg"}],
                "weight": "0.5"
            },
            {
                "id": 5,
                "name": "Plumas BIC Cristal Azul Caja x50",
                "description": "Caja con 50 plumas BIC Cristal color azul",
                "price": "45.00",
                "sku": "PLU-BIC-AZ-50",
                "stock_quantity": 60,
                "status": "publish",
                "categories": [{"name": "Útiles de Escritura"}],
                "images": [{"src": "https://example.com/plumas-bic.jpg"}],
                "weight": "1.2"
            }
        ]
        
        return [self._transform_wc_product(product) for product in mock_products]


# Instancia global del servicio
woocommerce_service = WooCommerceService()