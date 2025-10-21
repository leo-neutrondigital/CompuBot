# Models package
# Importar todos los modelos para que Alembic los detecte

from app.models.user import User, BaseModel
from app.models.conversation import Conversation, ConversationMessage
from app.models.quote import Quote, QuoteItem
from app.models.product import Product

# Hacer que todos los modelos estén disponibles cuando se importe el paquete
__all__ = [
    "BaseModel",
    "User", 
    "Conversation", 
    "ConversationMessage", 
    "Quote", 
    "QuoteItem",
    "Product"
]