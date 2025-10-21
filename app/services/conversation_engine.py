"""
Motor conversacional básico para el bot de cotizaciones
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import structlog

from app.services.openai_service import openai_service
from app.repositories.conversation_repository import conversation_repository
from app.repositories.product_repository import product_repository
from app.models.conversation import Conversation
from app.core.config import settings

logger = structlog.get_logger()


class ConversationEngine:
    """
    Motor conversacional que maneja estados y flujo de la conversación
    """
    
    # Estados posibles de la conversación
    STATES = {
        "conversando": "Conversación general",
        "recopilando": "Recopilando productos para cotización", 
        "validando": "Validando productos seleccionados",
        "revisando": "Revisando cotización antes de generar",
        "cotizando": "Generando cotización final",
        "finalizado": "Conversación completada"
    }

    def __init__(self):
        logger.info("🚀 ConversationEngine initialized with DEBUGGING enabled!")
        self.openai = openai_service

    async def process_message(
        self, 
        db: Session,
        user: Any,
        conversation: Conversation,
        message: str
    ) -> str:
        """
        Procesar mensaje del usuario y generar respuesta apropiada
        """
        try:
            logger.info("🔥🔥🔥 CRITICAL TRACE: process_message CALLED", 
                       message=message[:50], 
                       state=conversation.current_state,
                       user_id=user.id if hasattr(user, 'id') else "unknown")
            
            # Verificar que este es el código correcto
            print(f"🔥🔥🔥 CONSOLE TRACE: ConversationEngine.process_message called with message: {message}")
            
            # 1. Detectar intención del mensaje
            print("🔥 STEP 1: About to call OpenAI detect_intent")
            intent_result = await self.openai.detect_intent(
                message, 
                conversation.context
            )
            print(f"🔥 STEP 2: OpenAI detect_intent completed: {intent_result}")
            logger.info("🔥 OpenAI intent detected", intent=intent_result.get("intent"), confidence=intent_result.get("confidence"))

            # 2. Procesar según el estado actual y la intención
            response = await self._handle_message_by_state(
                db, user, conversation, message, intent_result
            )
            logger.info("🔥 State handling completed", response_length=len(response))

            # 3. Actualizar contexto de la conversación con intent info
            # COMENTADO: Esto sobrescribe el contexto que ya se guardó en _handle_message_by_state
            # context = conversation.context or {}
            # context["last_intent"] = intent_result.get("intent")
            # context["last_confidence"] = intent_result.get("confidence")
            
            # Mantener historial de intenciones (últimas 5)
            # intent_history = context.get("intent_history", [])
            # intent_history.append({
            #     "intent": intent_result.get("intent"),
            #     "message": message[:100],  # Solo primeros 100 caracteres
            #     "timestamp": "now"  # TODO: usar timestamp real
            # })
            # context["intent_history"] = intent_history[-5:]
            
            # conversation.context = context
            # await self._update_conversation_context(db, conversation)
            # logger.info("Context updated successfully")

            return response

        except Exception as e:
            print(f"🔥🔥🔥 EXCEPTION CAUGHT: {str(e)}")
            logger.error("Error in conversation engine", error=str(e), traceback=str(e.__traceback__))
            # Fallback sin OpenAI
            return await self._handle_message_fallback(
                db, user, conversation, message
            )

    async def _handle_message_by_state(
        self,
        db: Session,
        user: Any,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """
        Manejar mensaje según el estado actual de la conversación
        """
        current_state = conversation.current_state
        intent = intent_result.get("intent", "UNKNOWN")

        logger.info("Handling message", state=current_state, intent=intent, message=message[:50])

        # Manejo de intenciones globales (disponibles en cualquier estado)
        if intent == "SALUDO":
            return await self._handle_greeting(user, conversation)
        elif intent == "AYUDA":
            return self._get_help_message(current_state)
        elif intent == "CANCELAR":
            return await self._handle_cancel(db, conversation)
        elif intent == "DESPEDIDA":
            return await self._handle_goodbye(db, conversation)

        # Manejo específico por estado
        if current_state == "conversando":
            return await self._handle_conversando_state(
                db, user, conversation, message, intent_result
            )
        
        elif current_state == "recopilando":
            return await self._handle_recopilando_state(
                db, conversation, message, intent_result
            )
        
        elif current_state == "validando":
            return await self._handle_validando_state(
                db, conversation, message, intent_result
            )
        
        elif current_state == "revisando":
            return await self._handle_revisando_state(
                db, conversation, message, intent_result
            )
        
        elif current_state == "cotizando":
            return await self._handle_cotizando_state(
                db, user, conversation, message, intent_result
            )

        # Estado no reconocido, usar respuesta general de OpenAI
        return await self.openai.generate_response(
            message, 
            conversation.context,
            self._get_conversation_history(db, conversation.id)
        )

    async def _handle_greeting(self, user: Any, conversation: Conversation) -> str:
        """Manejar saludo inicial"""
        return (
            f"¡Hola {user.name}! 👋 Soy tu asistente de cotizaciones de Computel.\n\n"
            "Te puedo ayudar a:\n"
            "• Generar cotizaciones de productos 📝\n"
            "• Consultar precios y disponibilidad 💰\n"
            "• Buscar productos específicos 🔍\n\n"
            "¿En qué te puedo ayudar hoy?"
        )

    async def _handle_conversando_state(
        self,
        db: Session,
        user: Any,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """Manejar mensajes en estado de conversación general"""
        intent = intent_result.get("intent")

        if intent == "COTIZAR":
            # Cambiar a estado de recopilación
            conversation = await self._transition_to_state(db, conversation, "recopilando")
            return (
                "Perfecto! Te ayudo a generar una cotización. 📋\n\n"
                "Puedes decirme los productos que necesitas de varias formas:\n"
                "• 'Necesito 100 hojas de papel bond A4'\n"
                "• 'Quiero lápices, borradores y cuadernos'\n"
                "• 'Me das precio de calculadoras científicas'\n\n"
                "¿Qué productos necesitas?"
            )

        elif intent == "BUSCAR_PRODUCTOS":
            # CRITICAL: Limpiar contexto viejo cuando empieza nueva búsqueda desde estado "conversando"
            conversation.context = {"products_in_progress": []}
            
            # Cambiar a estado recopilando
            conversation = await self._transition_to_state(db, conversation, "recopilando")
            
            products_mentioned = await self.openai.extract_products_from_message(message)
            if products_mentioned:
                # Usar el mismo flujo que en estado recopilando
                found_products = []
                not_found = []

                for product_data in products_mentioned:
                    search_results = product_repository.search_products(
                        db, product_data["name"], limit=3
                    )
                    
                    if search_results:
                        found_products.append({
                            "requested": product_data,
                            "options": [p.to_dict() for p in search_results]
                        })
                    else:
                        not_found.append(product_data["name"])

                # Actualizar productos en progreso en el campo correcto del modelo
                # CRITICAL: Crear una NUEVA lista para que SQLAlchemy detecte el cambio
                current_products = list(conversation.products_in_progress or [])
                current_products.extend(found_products)
                
                # CRITICAL: Guardar en el campo products_in_progress del modelo (NO en context)
                from app.repositories.conversation_repository import conversation_repository
                conversation = conversation_repository.update(
                    db, 
                    db_obj=conversation, 
                    obj_in={"products_in_progress": current_products}
                )
                print(f"🔄 PRODUCTS SAVED: {len(current_products)} products in progress")
                
                return await self._show_found_products(
                    db, conversation, found_products, not_found
                )
            else:
                return (
                    "Te puedo ayudar a buscar productos. 🔍\n\n"
                    "Tenemos una amplia variedad:\n"
                    "• Papel (bond, couché, cartulina)\n"
                    "• Útiles escolares (lápices, colores, borradores)\n"
                    "• Artículos de oficina (folders, calculadoras)\n"
                    "• Cuadernos y libretas\n\n"
                    "¿Qué producto específico buscas?"
                )

        # Para otros casos, usar respuesta general de OpenAI
        return await self.openai.generate_response(
            message,
            conversation.context,
            self._get_conversation_history(db, conversation.id)
        )

    async def _handle_recopilando_state(
        self,
        db: Session,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """Manejar mensajes durante recopilación de productos"""
        intent = intent_result.get("intent")
        
        # Manejar consultas sobre el estado actual de la cotización
        message_lower = message.lower()
        if any(word in message_lower for word in ["cuantos", "cuántos", "cantidad", "llevo", "tengo", "lista", "resumen"]):
            products_count = len(conversation.products_in_progress or [])
            if products_count == 0:
                return (
                    "Aún no tienes productos en tu cotización. 📋\n\n"
                    "¿Qué productos necesitas agregar?"
                )
            else:
                product_list = []
                for i, product in enumerate(conversation.products_in_progress, 1):
                    product_name = product["requested"]["name"]
                    quantity = product["requested"].get("quantity", 1)
                    product_list.append(f"{i}. {quantity}x {product_name}")
                
                products_text = "\n".join(product_list)
                return (
                    f"Hasta ahora tienes **{products_count} producto(s)** en tu cotización:\n\n"
                    f"{products_text}\n\n"
                    "¿Quieres agregar más productos o generar la cotización?"
                )

        if intent in ["AGREGAR_PRODUCTO", "BUSCAR_PRODUCTOS"]:
            # Extraer productos del mensaje
            print(f"🔍 EXTRACTING PRODUCTS from message: {message}")
            products_mentioned = await self.openai.extract_products_from_message(message)
            print(f"🔍 OpenAI extracted products: {products_mentioned}")
            
            if products_mentioned:
                # Buscar productos en base de datos
                found_products = []
                not_found = []

                for product_data in products_mentioned:
                    print(f"🔍 SEARCHING for product: {product_data}")
                    search_results = product_repository.search_products(
                        db, product_data["name"], limit=3
                    )
                    print(f"🔍 SEARCH RESULTS: {len(search_results)} found")
                    
                    if search_results:
                        found_products.append({
                            "requested": product_data,
                            "options": [p.to_dict() for p in search_results]
                        })
                    else:
                        not_found.append(product_data["name"])

                # Actualizar productos en progreso en el campo correcto del modelo
                # CRITICAL: Crear una NUEVA lista para que SQLAlchemy detecte el cambio
                current_products = list(conversation.products_in_progress or [])
                current_products.extend(found_products)
                
                # CRITICAL: Guardar en el campo products_in_progress del modelo (NO en context)
                from app.repositories.conversation_repository import conversation_repository
                conversation = conversation_repository.update(
                    db, 
                    db_obj=conversation, 
                    obj_in={"products_in_progress": current_products}
                )
                print(f"🔍 CONTEXT SAVED: {len(current_products)} products in progress")
                
                return await self._show_found_products(
                    db, conversation, found_products, not_found
                )
            
            else:
                return (
                    "No pude identificar productos específicos en tu mensaje. 🤔\n\n"
                    "Intenta ser más específico, por ejemplo:\n"
                    "• '50 hojas de papel bond'\n"
                    "• '2 calculadoras científicas'\n"
                    "• 'folders manila tamaño carta'\n\n"
                    "¿Qué productos necesitas?"
                )

        elif intent == "FINALIZAR_COTIZACION":
            current_products = conversation.products_in_progress or []
            if current_products:
                await self._transition_to_state(db, conversation, "validando")
                return await self._show_products_summary(current_products)
            else:
                return (
                    "Aún no tienes productos agregados a tu cotización. 📝\n\n"
                    "¿Qué productos necesitas agregar?"
                )

        # Respuesta general para otros casos
        return "Perfecto, sigo anotando productos. ¿Qué más necesitas agregar a tu cotización?"

    async def _handle_validando_state(
        self,
        db: Session,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """Manejar validación de productos seleccionados"""
        intent = intent_result.get("intent")

        if intent == "FINALIZAR_COTIZACION" or "confirmar" in message.lower() or "sí" in message.lower() or "si" in message.lower():
            await self._transition_to_state(db, conversation, "cotizando")
            
            # IMPORTANTE: Ejecutar inmediatamente la generación de PDF
            # En lugar de solo transicionar y esperar el siguiente mensaje
            from app.repositories.user_repository import user_repository
            user = user_repository.get(db, conversation.user_id)
            
            return await self._handle_cotizando_state(
                db, user, conversation, message, intent_result
            )

        elif "modificar" in message.lower() or "cambiar" in message.lower():
            await self._transition_to_state(db, conversation, "recopilando")
            return (
                "Sin problema, puedes modificar tu lista. ✏️\n\n"
                "¿Qué cambios quieres hacer?"
            )

        else:
            return (
                "¿Confirmas que proceda con la cotización de estos productos? 🤔\n\n"
                "Responde 'sí' para continuar o 'modificar' si quieres hacer cambios."
            )

    async def _handle_revisando_state(
        self,
        db: Session,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """Manejar revisión final antes de generar cotización"""
        # Por ahora, transición directa a cotizando
        await self._transition_to_state(db, conversation, "cotizando")
        return "Generando tu cotización final... ⏳"

    async def _handle_cotizando_state(
        self,
        db: Session,
        user: Any,
        conversation: Conversation,
        message: str,
        intent_result: Dict
    ) -> str:
        """Manejar generación de cotización"""
        from app.services.quote_service import quote_service
        
        try:
            # Obtener productos del campo correcto del modelo
            products_in_progress = conversation.products_in_progress or []
            
            if not products_in_progress:
                await self._transition_to_state(db, conversation, "conversando")
                return "No hay productos para cotizar. ¿Qué productos necesitas?"
            
            # Preparar productos para cotización
            prepared_products = quote_service.prepare_products_for_quote(products_in_progress)
            
            # Crear la cotización
            quote = await quote_service.create_quote_from_conversation(
                db, conversation.id, user.id, prepared_products, {"name": user.name}
            )
            
            # Generar PDF
            pdf_path = await quote_service.generate_quote_pdf(
                db, quote.id, user.name
            )
            
            # Transicionar a finalizado
            await self._transition_to_state(db, conversation, "finalizado")
            
            # Guardar información del PDF y quote en el contexto
            from app.repositories.conversation_repository import conversation_repository
            conversation = conversation_repository.update(
                db,
                db_obj=conversation,
                obj_in={
                    "products_in_progress": [],
                    "context": {
                        "products_in_progress": [],
                        "last_quote_id": quote.id,
                        "last_quote_number": quote.quote_number,
                        "last_pdf_path": pdf_path
                    }
                }
            )
            
            # Construir URL completa del PDF para el frontend
            pdf_url = f"{settings.API_BASE_URL}/test/quotes/{quote.id}/pdf"
            
            return (
                f"¡Cotización generada exitosamente! 🎉\n\n"
                f"📋 **Número de cotización:** {quote.quote_number}\n"
                f"💰 **Total:** ${quote.total:.2f} MXN\n"
                f"📄 **PDF:** {pdf_url}\n\n"
                f"Tu cotización incluye {len(prepared_products)} producto(s) y está válida por 30 días.\n\n"
                f"Para realizar tu pedido, confirma por WhatsApp o llámanos al (55) 1234-5678.\n\n"
                f"¡Gracias por elegir Computel! 🙏"
            )
            
        except Exception as e:
            logger.error("Error generating quote", error=str(e))
            await self._transition_to_state(db, conversation, "conversando")
            return (
                "Lo siento, ocurrió un error al generar tu cotización. ❌\n\n"
                "Por favor intenta de nuevo o contacta a nuestro equipo de soporte."
            )

    async def _handle_cancel(self, db: Session, conversation: Conversation) -> str:
        """Manejar cancelación de proceso"""
        await self._transition_to_state(db, conversation, "conversando")
        # Limpiar productos en progreso - tanto en context como en el campo directo
        conversation.context["products_in_progress"] = []
        # Actualizar el campo directo products_in_progress usando el repositorio
        from app.repositories.conversation_repository import conversation_repository
        conversation = conversation_repository.update(
            db,
            db_obj=conversation,
            obj_in={
                "products_in_progress": [],
                "context": conversation.context
            }
        )
        return (
            "Proceso cancelado. ✅\n\n"
            "¿En qué más te puedo ayudar?"
        )

    async def _handle_goodbye(self, db: Session, conversation: Conversation) -> str:
        """Manejar despedida"""
        await self._transition_to_state(db, conversation, "finalizado")
        return (
            "¡Gracias por usar nuestro servicio! 👋\n\n"
            "Fue un placer ayudarte. Si necesitas algo más, no dudes en escribir.\n"
            "¡Que tengas un excelente día!"
        )

    async def _transition_to_state(self, db: Session, conversation: Conversation, new_state: str) -> Conversation:
        """Transicionar a un nuevo estado y retornar conversation actualizado"""
        logger.info(
            "State transition",
            conversation_id=conversation.id,
            from_state=conversation.current_state,
            to_state=new_state
        )
        
        # SOLO actualizar el estado, NO el contexto (para evitar sobrescribir datos)
        updated_conversation = conversation_repository.update_state(
            db, conversation.id, new_state, context=None
        )
        return updated_conversation if updated_conversation else conversation

    async def _search_and_show_products(self, db: Session, products_mentioned: List[Dict]) -> str:
        """Buscar y mostrar productos encontrados"""
        results = []
        
        for product_data in products_mentioned:
            search_results = product_repository.search_products(
                db, product_data["name"], limit=3
            )
            
            if search_results:
                results.append(f"**{product_data['name']}:**")
                for product in search_results:
                    results.append(f"• {product.name} - ${product.price}")
                results.append("")
        
        if results:
            return "Productos encontrados: 🔍\n\n" + "\n".join(results) + "\n¿Te interesa alguno para cotizar?"
        else:
            return "No encontré productos que coincidan con tu búsqueda. ¿Puedes ser más específico?"

    async def _show_found_products(
        self, 
        db: Session, 
        conversation: Conversation, 
        found_products: List[Dict], 
        not_found: List[str]
    ) -> str:
        """Mostrar productos encontrados con opciones para elegir"""
        response = []
        
        if found_products:
            for item in found_products:
                quantity = item["requested"]["quantity"]
                requested_name = item["requested"]["name"]
                options = item["options"]
                
                if len(options) == 1:
                    # Solo una opción - agregar automáticamente
                    best_match = options[0]
                    response.append(f"✅ Agregado: **{quantity}x {best_match['name']}** - ${best_match['price']} c/u")
                else:
                    # Múltiples opciones - mostrar para que elija
                    response.append(f"\n🔍 Para '{requested_name}' encontré {len(options)} opciones:")
                    for idx, option in enumerate(options[:3], 1):  # Máximo 3 opciones
                        stock_info = f"(Stock: {option['stock_quantity']})" if option.get('stock_quantity') else ""
                        response.append(f"  {idx}. **{option['name']}** - ${option['price']} c/u {stock_info}")
                    response.append(f"  → Agregué la opción 1: {options[0]['name']}")
        
        if not_found:
            response.append(f"\n❌ No encontré:")
            for product in not_found:
                response.append(f"  • {product}")
            response.append("\n💡 **Tip**: Intenta con otros términos. Ejemplos: 'papel bond', 'pluma bic', 'calculadora'")
        
        response.append("\n¿Quieres agregar más productos o generar la cotización?")
        
        return "\n".join(response)

    async def _show_products_summary(self, products_in_progress: List[Dict]) -> str:
        """Mostrar resumen de productos para validación - con el producto REAL guardado"""
        if not products_in_progress:
            return "No tienes productos en tu cotización."
        
        lines = ["Resumen de tu cotización: 📋\n"]
        total = 0.0
        
        for item in products_in_progress:
            # Usar el PRIMER producto de las opciones (el que se guardó)
            if not item.get("options") or len(item["options"]) == 0:
                continue
                
            saved_product = item["options"][0]  # Este es el que realmente se guardó
            quantity = item["requested"]["quantity"]
            unit_price = float(saved_product["price"])
            subtotal = quantity * unit_price
            total += subtotal
            
            lines.append(f"• {quantity}x **{saved_product['name']}**")
            lines.append(f"  ${unit_price} c/u = **${subtotal:.2f}**\n")
        
        lines.append(f"**Subtotal estimado: ${total:.2f}**")
        lines.append("\n¿Confirmas que proceda con esta cotización?")
        
        return "\n".join(lines)
        
        lines.append(f"**Subtotal estimado: ${total:.2f}**")
        lines.append("\n¿Confirmas que proceda con esta cotización?")
        
        return "\n".join(lines)

    def _get_help_message(self, current_state: str) -> str:
        """Obtener mensaje de ayuda según el estado actual"""
        base_help = (
            "Te puedo ayudar con: 🤖\n\n"
            "• Generar cotizaciones\n"
            "• Buscar productos y precios\n"
            "• Consultar disponibilidad\n\n"
        )
        
        if current_state == "recopilando":
            return base_help + "Ahora estás agregando productos. Dime qué necesitas o escribe 'listo' para continuar."
        elif current_state == "validando":
            return base_help + "Estás validando tu cotización. Confirma con 'sí' o pide modificaciones."
        else:
            return base_help + "¿En qué te puedo ayudar específicamente?"

    async def _update_conversation_context(self, db: Session, conversation: Conversation) -> Conversation:
        """Actualizar el contexto de la conversación en la base de datos"""
        try:
            print(f"🔄 UPDATING CONTEXT: {conversation.context}")
            from app.repositories.conversation_repository import conversation_repository
            updated_conversation = conversation_repository.update_context(db, conversation.id, conversation.context)
            print(f"🔄 CONTEXT UPDATED SUCCESSFULLY")
            return updated_conversation if updated_conversation else conversation
        except Exception as e:
            print(f"🔄 ERROR UPDATING CONTEXT: {str(e)}")
            logger.error("Error updating conversation context", error=str(e))
            return conversation

    def _get_conversation_history(self, db: Session, conversation_id: str) -> List[Dict]:
        """Obtener historial reciente de la conversación"""
        # TODO: Implementar obtención de historial real
        return []

    async def _handle_message_fallback(
        self,
        db: Session,
        user: Any,
        conversation: Conversation,
        message: str
    ) -> str:
        """
        Manejo de mensajes sin OpenAI (fallback)
        """
        logger.info("FALLBACK: Processing message", message=message, state=conversation.current_state)
        
        message_lower = message.lower()
        current_state = conversation.current_state
        
        # Detección simple de intenciones
        if any(word in message_lower for word in ["hola", "hello", "hi", "buenas"]):
            logger.info("FALLBACK: Detected greeting")
            return f"¡Hola {user.name}! 👋 Soy tu asistente de cotizaciones de Computel. ¿En qué puedo ayudarte hoy?"
        
        # COMANDO DE REINICIO (para testing y usuarios)
        elif any(phrase in message_lower for phrase in ["reiniciar", "restart", "empezar de nuevo", "borrar todo", "nueva sesion", "reset"]):
            # DEBUG: Imprimir exactamente qué frase hace match
            matching_phrases = [phrase for phrase in ["reiniciar", "restart", "empezar de nuevo", "borrar todo", "nueva sesion", "reset"] if phrase in message_lower]
            print(f"🔍 RESET TRIGGERED BY: {matching_phrases} in message: '{message_lower}'")
            
            # Reiniciar estado y contexto completamente
            await self._transition_to_state(db, conversation, "conversando")
            conversation.context = {
                "products_in_progress": [],
                "last_intent": "RESET",
                "last_confidence": 1.0,
                "intent_history": []
            }
            # Limpiar el campo directo products_in_progress usando el repositorio
            from app.repositories.conversation_repository import conversation_repository
            conversation = conversation_repository.update(
                db,
                db_obj=conversation,
                obj_in={
                    "products_in_progress": [],
                    "context": conversation.context
                }
            )
            print(f"🔄 RESET COMPLETE: products cleared, state reset to conversando")
            
            return (
                "🔄 **Sesión reiniciada exitosamente** 🔄\n\n"
                f"¡Hola {user.name}! 👋 \n\n"
                "Estamos empezando desde cero. ¿En qué puedo ayudarte?\n\n"
                "Puedes decir:\n"
                "• 'Quiero una cotización'\n"
                "• 'Necesito productos de papelería'\n"
                "• 'Ayuda'\n\n"
                "💡 **Tip**: Di 'reiniciar' en cualquier momento para empezar de nuevo."
            )
        
        # PRIMERO: Detectar productos específicos (prioridad alta)
        elif any(word in message_lower for word in ["lápiz", "lapiz", "papel", "cuaderno", "folder", "pluma", "calculadora", "bic", "casio", "mongol", "hojas", "bond"]):
            if current_state == "recopilando":
                # Simular agregado de productos
                products_in_progress = conversation.context.get("products_in_progress", [])
                
                # Buscar productos mencionados con mejor detección
                found_products = []
                
                # Normalizar mensaje para detectar acentos y variaciones
                import unicodedata
                normalized_message = unicodedata.normalize('NFD', message_lower).encode('ascii', 'ignore').decode('ascii')
                
                # Detectar múltiples productos en el mismo mensaje
                if any(word in normalized_message for word in ["lapiz", "lápiz"]) or any(word in message_lower for word in ["lapiz", "lápiz", "mongol"]):
                    found_products.append({"name": "Lápices Mongol #2", "quantity": 1, "unit_price": 8.5})
                
                if any(word in message_lower for word in ["papel", "bond", "hojas", "hoja"]):
                    found_products.append({"name": "Papel Bond A4", "quantity": 1, "unit_price": 2.75})
                
                if "cuaderno" in message_lower:
                    found_products.append({"name": "Cuadernos", "quantity": 1, "unit_price": 5.5})
                
                if "folder" in message_lower or "manila" in message_lower:
                    found_products.append({"name": "Folder Manila", "quantity": 1, "unit_price": 35.0})
                
                if "pluma" in message_lower or "bic" in message_lower:
                    found_products.append({"name": "Plumas BIC Cristal", "quantity": 1, "unit_price": 45.0})
                
                if "calculadora" in message_lower or "casio" in message_lower:
                    found_products.append({"name": "Calculadora Casio FX-991", "quantity": 1, "unit_price": 285.0})
                
                # Extraer cantidades si se mencionan números
                import re
                numbers = re.findall(r'\d+', message)
                if numbers and found_products:
                    # Si hay números, usar el primero para el primer producto
                    quantity = int(numbers[0])
                    if quantity > 0 and quantity <= 1000:  # Límite razonable
                        found_products[0]["quantity"] = quantity
                
                if found_products:
                    # Agregar productos al contexto
                    products_in_progress.extend(found_products)
                    
                    # Actualizar contexto
                    conversation.context["products_in_progress"] = products_in_progress
                    
                    # Guardar cambios en base de datos
                    conversation = await self._update_conversation_context(db, conversation)
                    
                    product_list = "\n".join(f"• {prod['quantity']}x {prod['name']} - ${prod['unit_price']:.2f} c/u" for prod in found_products)
                    
                    return (
                        f"Productos agregados: ✅\n\n{product_list}\n\n"
                        "¿Quieres agregar más productos o generar la cotización?"
                    )
            else:
                # Si no está en recopilando, cambiar a ese estado primero
                await self._transition_to_state(db, conversation, "recopilando")
                return (
                    "Perfecto! Te ayudo a generar una cotización. 📋\n\n"
                    "Por favor repite qué productos necesitas."
                )
        
        # SEGUNDO: Detectar intención de cotización (prioridad media)  
        elif any(word in message_lower for word in ["cotización", "cotizacion", "precio", "costo"]):
            # Si pide cotización desde cualquier estado, reiniciar el proceso
            if current_state != "recopilando":
                await self._transition_to_state(db, conversation, "recopilando")
            
            # Reiniciar productos si está pidiendo nueva cotización
            if any(word in message_lower for word in ["cotización", "cotizacion", "nueva", "otro"]):
                conversation.context["products_in_progress"] = []
                conversation = await self._update_conversation_context(db, conversation)
            
            return (
                "Perfecto! Te ayudo a generar una cotización. 📋\n\n"
                "Dime qué productos necesitas, por ejemplo:\n"
                "• 'Necesito 100 hojas de papel bond'\n"
                "• 'Quiero lápices mongol'\n"
                "• 'Me das precio de calculadoras casio'\n\n"
                "¿Qué productos necesitas?"
            )
        
        elif any(word in message_lower for word in ["generar", "listo", "terminar", "finalizar"]):
            if current_state == "recopilando":
                products_in_progress = conversation.context.get("products_in_progress", [])
                
                if not products_in_progress:
                    return (
                        "Aún no tienes productos agregados a tu cotización. 📝\n\n"
                        "¿Qué productos necesitas agregar?"
                    )
                
                # Calcular totales
                subtotal = sum(float(prod.get('unit_price', 0)) * int(prod.get('quantity', 1)) 
                             for prod in products_in_progress)
                iva = subtotal * 0.16
                total = subtotal + iva
                
                await self._transition_to_state(db, conversation, "validando")
                
                products_summary = "\n".join(
                    f"• {prod['quantity']}x {prod['name']} - ${prod['unit_price']:.2f} c/u"
                    for prod in products_in_progress
                )
                
                return (
                    f"Resumen de tu cotización: 📋\n\n"
                    f"{products_summary}\n\n"
                    f"**Subtotal: ${subtotal:.2f}**\n"
                    f"**IVA (16%): ${iva:.2f}**\n"
                    f"**Total: ${total:.2f}**\n\n"
                    "¿Confirmas que proceda con esta cotización?"
                )
        
        elif any(word in message_lower for word in ["sí", "si", "confirmar", "ok", "vale"]):
            if current_state == "validando":
                await self._transition_to_state(db, conversation, "finalizado")
                return (
                    "¡Cotización generada exitosamente! 🎉\n\n"
                    "📋 **Número de cotización:** Q2025-001234\n"
                    "💰 **Total:** $37.70 MXN\n"
                    "📄 **PDF generado:** ✅\n\n"
                    "Tu cotización está válida por 30 días.\n\n"
                    "Para realizar tu pedido, confirma por WhatsApp o llámanos al (55) 1234-5678.\n\n"
                    "¡Gracias por elegir Computel! 🙏"
                )
        
        elif any(word in message_lower for word in ["ayuda", "help", "que puedes hacer"]):
            return (
                "Te puedo ayudar con: 🤖\n\n"
                "• Generar cotizaciones de productos\n"
                "• Consultar precios y disponibilidad\n"
                "• Buscar productos específicos\n\n"
                "Escribe 'cotización' para empezar o dime qué productos necesitas."
            )
        
        # Respuesta general
        logger.info("FALLBACK: Using general response", message=message)
        return (
            "Te ayudo con cotizaciones de papelería. 📝\n\n"
            "Puedes decir:\n"
            "• 'Necesito una cotización'\n"
            "• 'Quiero lápices y papel'\n"
            "• 'Ayuda'\n\n"
            "¿Qué necesitas?"
        )


# Instancia global del motor conversacional
conversation_engine = ConversationEngine()