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
        # Process message (no history - keep it simple)
        result = chat_service.process_message(user_message=request.message)
        logger.info(f"Chat response: {result}")
        
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