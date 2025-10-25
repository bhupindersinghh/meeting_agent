import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter
from services.conversation_engine import ConversationEngine
from services.voice_service import VoiceService
from models.chatbot_models import MessageRequest, VoiceConfig

websocket_router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.conversation_engine = ConversationEngine()
        self.voice_service = VoiceService()
        self.voice_config = VoiceConfig()
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"Client {session_id} connected")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"Client {session_id} disconnected")
    
    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)
    
    async def send_audio_message(self, audio_data: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps({
                "type": "audio",
                "data": audio_data
            }))
    
    async def handle_voice_message(self, websocket: WebSocket, session_id: str, audio_data: str):
        """Handle incoming voice message"""
        try:
            # Convert audio to text
            user_input = await self.voice_service.speech_to_text(audio_data)
            
            if not user_input:
                await self.send_personal_message("I didn't catch that. Could you please try again?", session_id)
                return
            
            # Process the message
            request = MessageRequest(
                user_query=user_input,
                session_id=session_id,
                audio_data=audio_data,
                is_voice=True
            )
            
            response = await self.conversation_engine.process_message(request)
            
            # Send text response
            await self.send_personal_message(response.response, session_id)
            
            # Generate and send audio response
            if response.audio_response:
                await self.send_audio_message(response.audio_response, session_id)
            else:
                # Generate audio response
                audio_response = await self.voice_service.text_to_speech(
                    response.response, 
                    self.voice_config
                )
                if audio_response:
                    await self.send_audio_message(audio_response, session_id)
            
        except Exception as e:
            print(f"Error handling voice message: {e}")
            await self.send_personal_message("I encountered an error processing your message. Please try again.", session_id)
    
    async def handle_text_message(self, websocket: WebSocket, session_id: str, message: str):
        """Handle incoming text message"""
        try:
            request = MessageRequest(
                user_query=message,
                session_id=session_id,
                is_voice=False
            )
            
            response = await self.conversation_engine.process_message(request)
            
            # Send text response
            await self.send_personal_message(response.response, session_id)
            
            # Generate and send audio response if requested
            if response.conversation_state.value in ["collecting_duration", "collecting_time_preference", "confirming_slot"]:
                audio_response = await self.voice_service.text_to_speech(
                    response.response, 
                    self.voice_config
                )
                if audio_response:
                    await self.send_audio_message(audio_response, session_id)
            
        except Exception as e:
            print(f"Error handling text message: {e}")
            await self.send_personal_message("I encountered an error processing your message. Please try again.", session_id)

manager = ConnectionManager()

@websocket_router.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "text")
            
            if message_type == "text":
                message = message_data.get("message", "")
                await manager.handle_text_message(websocket, session_id, message)
            
            elif message_type == "audio":
                audio_data = message_data.get("data", "")
                await manager.handle_voice_message(websocket, session_id, audio_data)
            
            elif message_type == "ping":
                await manager.send_personal_message("pong", session_id)
            
            else:
                await manager.send_personal_message("Unknown message type", session_id)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)

@websocket_router.websocket("/voice/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    """Dedicated WebSocket endpoint for voice-only conversations"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            
            # Convert bytes to base64
            import base64
            audio_data = base64.b64encode(data).decode('utf-8')
            
            await manager.handle_voice_message(websocket, session_id, audio_data)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"Voice WebSocket error: {e}")
        manager.disconnect(session_id)
