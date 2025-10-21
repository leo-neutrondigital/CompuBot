"""
Repositorio para gestión de conversaciones
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.repository import BaseRepository
from app.models.conversation import Conversation, ConversationMessage


class ConversationRepository(BaseRepository[Conversation, dict, dict]):
    def __init__(self):
        super().__init__(Conversation)

    def get_active_by_user(self, db: Session, user_id: str) -> Optional[Conversation]:
        """Obtener conversación activa de un usuario"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == "active"
        ).first()

    def get_by_whatsapp_chat(self, db: Session, whatsapp_chat_id: str) -> Optional[Conversation]:
        """Obtener conversación por ID de chat de WhatsApp"""
        return db.query(Conversation).filter(
            Conversation.whatsapp_chat_id == whatsapp_chat_id,
            Conversation.status == "active"
        ).first()

    def create_conversation(
        self, 
        db: Session, 
        user_id: str, 
        whatsapp_chat_id: str
    ) -> Conversation:
        """Crear nueva conversación"""
        # Cerrar cualquier conversación activa previa
        existing = self.get_active_by_user(db, user_id)
        if existing:
            self.update(db, db_obj=existing, obj_in={"status": "completed"})

        conversation_data = {
            "user_id": user_id,
            "whatsapp_chat_id": whatsapp_chat_id,
            "status": "active",
            "current_state": "conversando",
            "context": {},
            "products_in_progress": [],
            "total_messages": 0
        }
        return self.create(db, obj_in=conversation_data)

    def update_state(
        self, 
        db: Session, 
        conversation_id: str, 
        new_state: str, 
        context: dict = None
    ) -> Optional[Conversation]:
        """Actualizar estado de la conversación"""
        conversation = self.get(db, conversation_id)
        if conversation:
            update_data = {"current_state": new_state}
            if context:
                update_data["context"] = context
            return self.update(db, db_obj=conversation, obj_in=update_data)
        return None

    def add_message(
        self,
        db: Session,
        conversation_id: str,
        message_type: str,
        content: str,
        intent_detected: str = None,
        metadata: dict = None
    ) -> ConversationMessage:
        """Agregar mensaje a la conversación"""
        message_data = {
            "conversation_id": conversation_id,
            "message_type": message_type,
            "content": content,
            "intent_detected": intent_detected,
            "message_metadata": metadata or {}
        }
        
        message = ConversationMessage(**message_data)
        db.add(message)
        
        # Actualizar contador de mensajes
        conversation = self.get(db, conversation_id)
        if conversation:
            self.update(db, db_obj=conversation, obj_in={
                "total_messages": conversation.total_messages + 1,
                "last_activity": datetime.now()
            })
        
        db.commit()
        db.refresh(message)
        return message

    def get_expired_conversations(self, db: Session) -> List[Conversation]:
        """Obtener conversaciones que han expirado"""
        timeout_threshold = datetime.now() - timedelta(hours=2)
        return db.query(Conversation).filter(
            Conversation.status == "active",
            Conversation.last_activity < timeout_threshold
        ).all()

    def complete_conversation(self, db: Session, conversation_id: str, summary: str = None) -> Optional[Conversation]:
        """Completar una conversación"""
        conversation = self.get(db, conversation_id)
        if conversation:
            return self.update(db, db_obj=conversation, obj_in={
                "status": "completed",
                "completed_at": datetime.now(),
                "conversation_summary": summary
            })
        return None

    def update_context(self, db: Session, conversation_id: str, context: dict) -> Optional[Conversation]:
        """Actualizar el contexto de una conversación"""
        conversation = self.get(db, conversation_id)
        if conversation:
            return self.update(db, db_obj=conversation, obj_in={
                "context": context,
                "last_activity": datetime.now()
            })
        return None


class ConversationMessageRepository(BaseRepository[ConversationMessage, dict, dict]):
    def __init__(self):
        super().__init__(ConversationMessage)

    def get_by_conversation(self, db: Session, conversation_id: str, limit: int = 50) -> List[ConversationMessage]:
        """Obtener mensajes de una conversación"""
        return db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()


# Instancias globales
conversation_repository = ConversationRepository()
conversation_message_repository = ConversationMessageRepository()