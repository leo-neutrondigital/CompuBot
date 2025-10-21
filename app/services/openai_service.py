"""
Servicio para integración con OpenAI ChatGPT
"""
import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    async def detect_intent(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Detectar la intención del usuario usando OpenAI
        """
        try:
            system_prompt = self._get_intent_detection_prompt()
            user_prompt = self._format_user_message_for_intent(message, context)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )

            # Intentar parsear como JSON
            content = response.choices[0].message.content.strip()
            
            # Si la respuesta no empieza con {, buscar el JSON dentro del texto
            if not content.startswith('{'):
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group()
            
            result = json.loads(content)
            
            logger.info("Intent detected", intent=result.get("intent"), confidence=result.get("confidence"))
            return result

        except json.JSONDecodeError:
            # Si no es JSON válido, intentar extraer manualmente
            content = response.choices[0].message.content.lower()
            if any(word in content for word in ["cotización", "cotizacion", "precio"]):
                return {"intent": "COTIZAR", "confidence": 0.8, "entities": []}
            elif any(word in content for word in ["producto", "buscar", "necesito"]):
                return {"intent": "BUSCAR_PRODUCTOS", "confidence": 0.7, "entities": []}
            elif any(word in content for word in ["hola", "hello", "hi", "buenas"]):
                return {"intent": "SALUDO", "confidence": 0.8, "entities": []}
            else:
                return {"intent": "OTRO", "confidence": 0.6, "entities": []}
        except Exception as e:
            logger.error("Error detecting intent", error=str(e))
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "entities": [],
                "error": str(e)
            }

    async def generate_response(
        self, 
        user_message: str, 
        context: Dict = None,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generar respuesta conversacional usando OpenAI
        """
        try:
            system_prompt = self._get_conversation_prompt()
            messages = [{"role": "system", "content": system_prompt}]

            # Agregar historial de conversación si existe
            if conversation_history:
                for msg in conversation_history[-5:]:  # Solo los últimos 5 mensajes
                    messages.append({
                        "role": "user" if msg["type"] == "user" else "assistant",
                        "content": msg["content"]
                    })

            # Agregar contexto actual
            user_prompt = self._format_user_message_for_response(user_message, context)
            messages.append({"role": "user", "content": user_prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )

            result = response.choices[0].message.content.strip()
            
            logger.info("Response generated", response_length=len(result))
            return result

        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return "Lo siento, ocurrió un error al procesar tu mensaje. ¿Podrías intentarlo de nuevo?"

    async def extract_products_from_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Extraer productos mencionados en el mensaje
        """
        try:
            system_prompt = self._get_product_extraction_prompt()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.2
            )

            result = json.loads(response.choices[0].message.content)
            products = result.get("products", [])
            
            logger.info("Products extracted", count=len(products))
            return products

        except json.JSONDecodeError:
            # Si no es JSON válido, intentar extraer manualmente
            content = response.choices[0].message.content.lower()
            products = []
            
            # Búsqueda simple de productos comunes
            if "lápiz" in content or "lapiz" in content:
                products.append({"name": "Lápices", "quantity": 1})
            if "papel" in content:
                products.append({"name": "Papel", "quantity": 1})
            if "cuaderno" in content:
                products.append({"name": "Cuadernos", "quantity": 1})
            if "folder" in content or "carpeta" in content:
                products.append({"name": "Folders", "quantity": 1})
                
            return products
        except Exception as e:
            logger.error("Error extracting products", error=str(e))
            return []

    def _get_intent_detection_prompt(self) -> str:
        """Prompt para detección de intenciones"""
        return """
Analiza el mensaje del usuario y determina su intención principal. 

RESPONDE EXACTAMENTE en este formato (incluyendo las llaves):
{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "entities": ["entidad1", "entidad2"],
    "description": "Descripción breve"
}

INTENCIONES POSIBLES:
- SALUDO: El usuario saluda o inicia conversación
- COTIZAR: Quiere una cotización o conocer precios  
- BUSCAR_PRODUCTOS: Busca productos específicos o información del catálogo
- AGREGAR_PRODUCTO: Quiere agregar un producto a su cotización
- MODIFICAR_CANTIDAD: Quiere cambiar cantidades de productos
- FINALIZAR_COTIZACION: Quiere completar/generar/finalizar la cotización. Palabras clave: "generar", "finalizar", "terminar", "listo", "es todo", "ya está"
- CANCELAR: Quiere cancelar el proceso
- AYUDA: Pide ayuda o información sobre cómo funciona
- DESPEDIDA: Se despide o termina la conversación
- OTRO: Cualquier otra intención no clasificada

IMPORTANTE: 
- Si el mensaje contiene palabras como "generar", "generar cotización", "generar PDF", "finalizar", usa FINALIZAR_COTIZACION
- Tu respuesta debe ser SOLO el JSON, sin texto adicional antes o después.
"""

    def _get_conversation_prompt(self) -> str:
        """Prompt principal para conversación"""
        return """
Eres el asistente virtual de COMPUTEL, una empresa mexicana de papelería y artículos de oficina.

PERSONALIDAD:
- Amigable, profesional y eficiente
- Usas lenguaje natural mexicano (tuteas al cliente)
- Siempre helpful y orientado a soluciones
- Conocedor de productos de papelería

TU TRABAJO:
1. Ayudar a clientes a encontrar productos
2. Generar cotizaciones precisas
3. Proporcionar información de precios y disponibilidad
4. Guiar el proceso de compra de manera natural

REGLAS IMPORTANTES:
- NUNCA inventes precios o productos que no existen
- Si no sabes algo, pregunta o pide más información
- Mantén las respuestas concisas pero completas
- Siempre confirma detalles importantes
- Usa emojis moderadamente para ser más amigable

PRODUCTOS COMUNES:
Papel (bond, couché, cartulina), lápices, plumas, marcadores, folders, cuadernos, 
calculadoras, engrapadoras, clips, gomas, correctores, etc.

Responde de manera natural y conversacional.
"""

    def _get_product_extraction_prompt(self) -> str:
        """Prompt para extraer productos del mensaje"""
        return """
Eres un experto en identificar productos de papelería y oficina mencionados en mensajes.

Analiza el mensaje y extrae TODOS los productos mencionados, incluyendo cantidades si se especifican.

IMPORTANTE - NORMALIZACIÓN ESTRICTA:
- El "name" debe ser ESPECÍFICO y CONSISTENTE
- Usar términos de búsqueda comunes sin acentos
- Ejemplos de normalización:
  * "calculadoras científicas" → "calculadora cientifica"
  * "hojas bond" / "papel bond" → "papel bond"
  * "lápices" / "lapiceros" → "lapiz"
  * "plumas BIC" / "lapiceros bic" → "pluma bic"
  * "cuadernos" → "cuaderno"

MAPEO DE PRODUCTOS COMUNES:
- Papel/hojas: "papel bond", "papel couche", "cartulina"
- Escritura: "lapiz", "pluma bic", "marcador", "color"
- Cuadernos: "cuaderno"
- Folders: "folder"
- Calculadoras: "calculadora cientifica", "calculadora basica"

Responde SIEMPRE en formato JSON:
{
    "products": [
        {
            "name": "nombre normalizado (específico, sin acentos, minúsculas)",
            "quantity": 10,
            "unit": "piezas",
            "description": "descripción adicional si la hay"
        }
    ]
}

Si no se especifica cantidad, usa 1 como default.
Si no hay productos mencionados, devuelve array vacío.
"""

    def _format_user_message_for_intent(self, message: str, context: Dict = None) -> str:
        """Formatear mensaje para detección de intención"""
        formatted = f"Mensaje del usuario: '{message}'"
        
        if context:
            if context.get("current_state"):
                formatted += f"\nEstado actual de la conversación: {context['current_state']}"
            if context.get("products_in_progress"):
                formatted += f"\nProductos en proceso: {len(context['products_in_progress'])} items"
        
        return formatted

    def _format_user_message_for_response(self, message: str, context: Dict = None) -> str:
        """Formatear mensaje para generar respuesta"""
        formatted = f"Cliente dice: '{message}'"
        
        if context:
            if context.get("current_state"):
                formatted += f"\n\nContexto: El cliente está en estado '{context['current_state']}'"
            if context.get("products_in_progress"):
                products = context['products_in_progress']
                if products:
                    formatted += f"\nProductos agregados hasta ahora: {len(products)} items"
        
        return formatted


# Instancia global del servicio
openai_service = OpenAIService()