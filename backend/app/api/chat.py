from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize chat service
chat_service = ChatService()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot
    """
    try:
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [msg.model_dump() for msg in request.conversation_history]
        
        # Process message
        result = chat_service.process_message(
            user_message=request.message,
            conversation_history=history
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema")
async def get_schema():
    """
    Get database schema information
    """
    try:
        schema = chat_service.db_service.get_schema()
        return {"schema": schema}
    except Exception as e:
        logger.error(f"Schema error: {e}")
        raise HTTPException(status_code=500, detail=str(e))