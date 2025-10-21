"""
Simulador de chat para probar el bot localmente
"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.user_service import user_service
from app.services.conversation_engine import conversation_engine
from app.repositories.conversation_repository import conversation_repository

router = APIRouter(prefix="/chat", tags=["Chat Simulator"])


@router.get("/", response_class=HTMLResponse)
async def chat_simulator():
    """Interfaz web simple para probar el bot"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simulador Bot Computel</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .chat-container { border: 1px solid #ddd; border-radius: 10px; height: 400px; overflow-y: auto; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9; }
            .message { margin-bottom: 10px; padding: 10px; border-radius: 8px; }
            .user-message { background-color: #007bff; color: white; text-align: right; margin-left: 100px; }
            .bot-message { background-color: #e9ecef; color: #333; margin-right: 100px; }
            .input-group { display: flex; gap: 10px; }
            .input-group input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .input-group button { padding: 10px 20px; background-color: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .input-group button:hover { background-color: #218838; }
            .user-info { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 10px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>🤖 Simulador Bot Computel</h1>
        
        <div class="user-info">
            <h3>👤 Usuario de Prueba:</h3>
            <p><strong>Teléfono:</strong> 5215559876543</p>
            <p><strong>Nombre:</strong> Manager Test</p>
            <p><strong>Estado:</strong> <span id="conversation-state">conversando</span></p>
        </div>
        
        <div class="chat-container" id="chat-container">
            <div class="bot-message">
                <strong>Bot:</strong> ¡Hola! Soy el asistente de cotizaciones de Computel. ¿En qué puedo ayudarte? 😊
            </div>
        </div>
        
        <div class="input-group">
            <input type="text" id="message-input" placeholder="Escribe tu mensaje aquí..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Enviar</button>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>💡 Mensajes de Ejemplo:</h3>
            <button onclick="sendExampleMessage('Hola')" style="margin: 5px; padding: 5px 10px; background: #4CAF50; color: white; border: none; border-radius: 3px;">Hola</button>
            <button onclick="sendExampleMessage('Necesito una cotización')" style="margin: 5px; padding: 5px 10px; background: #2196F3; color: white; border: none; border-radius: 3px;">Necesito una cotización</button>
            <button onclick="sendExampleMessage('Necesito 10 lápices y 5 cuadernos')" style="margin: 5px; padding: 5px 10px; background: #FF9800; color: white; border: none; border-radius: 3px;">Agregar productos</button>
            <button onclick="sendExampleMessage('Generar cotización')" style="margin: 5px; padding: 5px 10px; background: #9C27B0; color: white; border: none; border-radius: 3px;">Generar cotización</button>
            <button onclick="sendExampleMessage('reiniciar')" style="margin: 5px; padding: 5px 10px; background: #f44336; color: white; border: none; border-radius: 3px;">🔄 Reiniciar</button>
        </div>

        <script>
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            function sendExampleMessage(message) {
                document.getElementById('message-input').value = message;
                sendMessage();
            }
            
            async function sendMessage() {
                const messageInput = document.getElementById('message-input');
                const message = messageInput.value.trim();
                
                if (!message) return;
                
                // Mostrar mensaje del usuario
                addMessage(message, 'user');
                messageInput.value = '';
                
                // Mostrar "escribiendo..."
                const typingId = addMessage('Bot está escribiendo...', 'bot');
                
                try {
                    const response = await fetch('/test/test-conversation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `user_phone=5215559876543&message=${encodeURIComponent(message)}`
                    });
                    
                    const data = await response.json();
                    
                    // Remover mensaje de "escribiendo..."
                    document.getElementById(typingId).remove();
                    
                    if (data.error) {
                        addMessage(`Error: ${data.error}`, 'bot');
                    } else {
                        addMessage(data.response || 'Sin respuesta', 'bot');
                        if (data.current_state) {
                            document.getElementById('conversation-state').textContent = data.current_state;
                        }
                    }
                    
                } catch (error) {
                    document.getElementById(typingId).remove();
                    addMessage(`Error: ${error.message}`, 'bot');
                }
            }
            
            function addMessage(message, sender) {
                const chatContainer = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                const messageId = 'msg-' + Date.now();
                messageDiv.id = messageId;
                messageDiv.className = `message ${sender}-message`;
                
                // No agregar "Bot:" si el mensaje ya lo incluye
                let displayMessage = message.startsWith('Bot:') ? message : 
                    (sender === 'user' ? `Tú: ${message}` : `Bot: ${message}`);
                
                // Convertir URLs en enlaces clicables
                displayMessage = displayMessage.replace(
                    /(https?:\/\/[^\s]+)/g,
                    '<a href="$1" target="_blank" style="color: #fff; text-decoration: underline;">📄 Descargar PDF</a>'
                );
                
                // Convertir rutas relativas en enlaces clicables
                displayMessage = displayMessage.replace(
                    /(?:📄 \*\*PDF:\*\* )(\/[^\s]+)/g,
                    '📄 **PDF:** <a href="$1" target="_blank" style="color: ' + 
                    (sender === 'user' ? '#fff' : '#007bff') + 
                    '; text-decoration: underline; font-weight: bold;">📥 Descargar Cotización</a>'
                );
                
                messageDiv.innerHTML = displayMessage;
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                return messageId;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/send")
async def send_message(
    user_phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Endpoint para enviar mensajes desde el simulador"""
    try:
        # Autenticar usuario
        user = user_service.authenticate_user(db, user_phone)
        if not user:
            return {"error": "Usuario no encontrado", "user_phone": user_phone}
        
        # Obtener o crear conversación
        conversation = conversation_repository.get_active_by_user(db, user.id)
        if not conversation:
            conversation = conversation_repository.create_conversation(
                db, user.id, f"chat_simulator_{user.id}"
            )
        
        # Procesar mensaje
        response = await conversation_engine.process_message(
            db, user, conversation, message
        )
        
        return {
            "success": True,
            "user": {"name": user.name, "phone": user.phone_number},
            "conversation_id": conversation.id,
            "current_state": conversation.current_state,
            "message": message,
            "response": response
        }
        
    except Exception as e:
        return {"error": str(e)}