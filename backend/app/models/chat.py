from pydantic import BaseModel, Field
from typing import Optional, List, Any

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: user, assistant, or system")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(default=None, description="Previous messages")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant's response")
    sql_executed: Optional[str] = Field(None, description="SQL query that was executed")
    sql_explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    data_preview: Optional[List[Any]] = Field(None, description="Preview of returned data")
    total_data: Optional[List[Any]] = Field(None, description="All returned data")
    error: Optional[str] = Field(None, description="Error message if any")