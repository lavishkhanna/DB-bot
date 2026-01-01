from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService
import logging
import json

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.db_service = DatabaseService()
        self.schema = None
    
    def initialize(self):
        """Load database schema"""
        self.schema = self.db_service.get_schema()
        logger.info("Chat service initialized with database schema")
    
    def process_message(self, user_message: str, conversation_history: list = None):
        """Process user message and return response"""
        
        if not self.schema:
            self.initialize()
        
        # Build messages - ONLY user and assistant roles
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                # Ensure only valid roles
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Get LLM response (SQL as text)
        try:
            response = self.llm_service.chat(messages, self.schema)
            sql_text = response.choices[0].message.content
            
            # Extract SQL
            sql = self.llm_service.extract_sql(sql_text)
            
            logger.info(f"Generated SQL: {sql}")
            
            # Execute query
            query_result = self.db_service.execute_user_query(sql)
            
            # Build response
            if query_result["success"]:
                data_preview = query_result["data"][:5] if query_result["data"] else []
                
                # Create a natural language response
                if query_result["row_count"] == 0:
                    response_text = "The query returned no results."
                elif query_result["row_count"] == 1:
                    response_text = f"Found 1 result: {json.dumps(data_preview[0], indent=2)}"
                else:
                    response_text = f"Found {query_result['row_count']} results. Here are the first few:\n{json.dumps(data_preview, indent=2)}"
                
                return {
                    "response": response_text,
                    "sql_executed": sql,
                    "row_count": query_result["row_count"],
                    "data_preview": data_preview
                }
            else:
                return {
                    "response": f"Error executing query: {query_result['error']}",
                    "sql_executed": sql,
                    "error": query_result["error"]
                }
                
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "sql_executed": None,
                "error": str(e)
            }