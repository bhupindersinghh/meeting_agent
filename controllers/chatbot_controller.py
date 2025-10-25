from fastapi import APIRouter, HTTPException
from services.conversation_engine import ConversationEngine
from models.chatbot_models import MessageRequest, MessageResponse

chatbot_router = APIRouter(prefix="/message", tags=["message"])

# Initialize conversation engine
conversation_engine = ConversationEngine()

@chatbot_router.post("/")
async def send_message(request: MessageRequest) -> MessageResponse:
    """Process a message from the user and return a response"""
    try:
        response = await conversation_engine.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@chatbot_router.get("/context/{session_id}")
async def get_conversation_context(session_id: str):
    """Get the current conversation context for a session"""
    context = conversation_engine.get_conversation_context(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    return context

@chatbot_router.delete("/context/{session_id}")
async def clear_conversation_context(session_id: str):
    """Clear the conversation context for a session"""
    success = conversation_engine.clear_conversation_context(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Conversation context cleared successfully"}