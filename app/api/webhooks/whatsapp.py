from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import structlog
from typing import Dict, Any, Optional
import json

from app.core.config import settings
from app.core.database import get_db
from app.services.user_service import user_service
from app.repositories.conversation_repository import conversation_repository

logger = structlog.get_logger()
router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """
    Verificación del webhook de WhatsApp Business API
    Meta envía esta solicitud para verificar que el endpoint es válido
    """
    logger.info(
        "Webhook verification attempt",
        mode=hub_mode,
        verify_token=hub_verify_token
    )
    
    # Verificar que el token coincida
    if hub_verify_token != settings.WHATSAPP_VERIFY_TOKEN:
        logger.warning("Invalid verify token", provided_token=hub_verify_token)
        raise HTTPException(status_code=403, detail="Invalid verify token")
    
    if hub_mode == "subscribe":
        logger.info("Webhook verified successfully", challenge=hub_challenge)
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning("Invalid hub mode", mode=hub_mode)
    raise HTTPException(status_code=400, detail="Invalid hub mode")


@router.post("/whatsapp")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibir webhooks de WhatsApp Business API.
    Este endpoint procesará todos los mensajes entrantes con autenticación
    """
    try:
        # Obtener datos del webhook
        data = await request.json()
        
        logger.info("Webhook received", data=data)
        
        # Verificar que sea un mensaje válido
        if not _is_valid_message(data):
            logger.warning("Invalid webhook data", data=data)
            return {"status": "ignored"}
        
        # Extraer información del mensaje
        message_info = _extract_message_info(data)
        
        if message_info:
            logger.info("Message extracted", message_info=message_info)
            
            # Autenticar usuario
            user = await _authenticate_user(db, message_info["from"])
            
            if not user:
                # Usuario no autorizado
                await _send_unauthorized_response(message_info["from"])
                return {"status": "unauthorized"}
            
            # Obtener o crear conversación
            conversation = await _get_or_create_conversation(
                db, user.id, message_info["from"]
            )
            
            # Agregar mensaje a la conversación
            await _log_message(db, conversation.id, "user", message_info["body"])
            
            # Procesar mensaje con el motor conversacional
            response = await _process_authenticated_message(
                db, user, conversation, message_info
            )
            
            # Enviar respuesta a WhatsApp
            if response:
                await _send_whatsapp_response(message_info["from"], response)
                await _log_message(db, conversation.id, "bot", response)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error("Error processing webhook", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


def _is_valid_message(data: Dict[str, Any]) -> bool:
    """
    Verificar si el webhook contiene un mensaje válido
    """
    try:
        entry = data.get("entry", [])
        if not entry:
            return False
            
        changes = entry[0].get("changes", [])
        if not changes:
            return False
            
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        return len(messages) > 0
    except (IndexError, KeyError):
        return False


def _extract_message_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraer información útil del mensaje de WhatsApp
    """
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        message = value["messages"][0]
        
        return {
            "message_id": message.get("id"),
            "from": message.get("from"),
            "timestamp": message.get("timestamp"),
            "type": message.get("type"),
            "body": message.get("text", {}).get("body", "") if message.get("type") == "text" else "",
            "phone_number_id": value.get("metadata", {}).get("phone_number_id")
        }
    except (IndexError, KeyError) as e:
        logger.error("Error extracting message info", error=str(e))
        return None


async def _authenticate_user(db: Session, phone_number: str) -> Optional[Any]:
    """Autenticar usuario por número de teléfono"""
    try:
        user = user_service.authenticate_user(db, phone_number)
        if user and user.active:
            logger.info("User authenticated", user_id=user.id, phone=phone_number)
            return user
        else:
            logger.warning("User not found or inactive", phone=phone_number)
            return None
    except Exception as e:
        logger.error("Error authenticating user", phone=phone_number, error=str(e))
        return None


async def _send_unauthorized_response(phone_number: str):
    """Enviar respuesta a usuario no autorizado"""
    message = (
        "Lo siento, no tienes autorización para usar este servicio. "
        "Por favor contacta a tu administrador para obtener acceso."
    )
    await _send_whatsapp_response(phone_number, message)


async def _get_or_create_conversation(db: Session, user_id: str, whatsapp_chat_id: str):
    """Obtener conversación existente o crear una nueva"""
    try:
        # Buscar conversación activa
        conversation = conversation_repository.get_active_by_user(db, user_id)
        
        if not conversation:
            # Crear nueva conversación
            conversation = conversation_repository.create_conversation(
                db, user_id, whatsapp_chat_id
            )
            logger.info("New conversation created", conversation_id=conversation.id)
        else:
            logger.info("Using existing conversation", conversation_id=conversation.id)
            
        return conversation
    except Exception as e:
        logger.error("Error managing conversation", error=str(e))
        raise


async def _log_message(db: Session, conversation_id: str, message_type: str, content: str):
    """Registrar mensaje en la conversación"""
    try:
        conversation_repository.add_message(
            db, conversation_id, message_type, content
        )
    except Exception as e:
        logger.error("Error logging message", error=str(e))


async def _process_authenticated_message(db: Session, user, conversation, message_info: Dict[str, Any]) -> str:
    """
    Procesar mensaje de usuario autenticado usando el motor conversacional
    """
    from app.services.conversation_engine import conversation_engine
    
    user_message = message_info.get("body", "")
    
    logger.info(
        "Processing authenticated message with conversation engine", 
        user_id=user.id,
        conversation_id=conversation.id,
        message_preview=user_message[:50]
    )
    
    try:
        # Usar el motor conversacional para procesar el mensaje
        response = await conversation_engine.process_message(
            db, user, conversation, user_message
        )
        return response
        
    except Exception as e:
        logger.error("Error in conversation engine", error=str(e))
        # Fallback a respuesta básica
        return f"🔴 WEBHOOK FALLBACK ACTIVADO 🔴 Hola {user.name}, soy tu asistente de Computel. ¿En qué puedo ayudarte hoy?"


async def _send_whatsapp_response(to: str, message: str):
    """
    Enviar respuesta a WhatsApp (placeholder para MVP)
    TODO: Implementar envío real con WhatsApp API
    """
    logger.info("Would send WhatsApp message", to=to, message=message)
    # Por ahora solo logueamos, implementaremos el envío real después
    pass