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
    
    def process_message(self, user_message: str):
        """Process user message and return response"""

        if not self.schema:
            self.initialize()

        # Build messages - simple, no history complexity
        messages = [{"role": "user", "content": user_message}]
        
        # Get LLM response (SQL as text) with retry on error
        max_retries = 2
        last_error = None

        try:
            for attempt in range(max_retries):
                response = self.llm_service.chat(messages, self.schema)
                sql_text = response.choices[0].message.content
                logger.info(f"LLM response (attempt {attempt + 1}): {sql_text}")

                # Extract SQL
                sql = self.llm_service.extract_sql(sql_text)

                logger.info(f"Generated SQL (attempt {attempt + 1}): {sql}")

                # Execute query
                query_result = self.db_service.execute_user_query(sql)

                # Build response
                if query_result["success"]:
                    data_preview = query_result["data"][:5] if query_result["data"] else []
                    total_data= query_result["data"] if query_result["data"] else []

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
                        "data_preview": data_preview,
                        "total_data": total_data
                    }
                else:
                    # Query failed - provide error feedback to LLM for retry
                    last_error = query_result["error"]

                    if attempt < max_retries - 1:
                        # Add error feedback to help LLM correct itself
                        messages.append({
                            "role": "assistant",
                            "content": sql
                        })
                        messages.append({
                            "role": "user",
                            "content": f"That query failed with error: {last_error}\n\nPlease fix the query. Common issues:\n- Check column names match the schema EXACTLY\n- Verify table names are correct\n- Ensure JOIN conditions use the correct foreign key columns\n- Check for syntax errors\n\nGenerate a corrected query:"
                        })
                        logger.warning(f"Query failed (attempt {attempt + 1}), retrying with error feedback: {last_error}")
                        continue
                    else:
                        # Final attempt failed
                        return {
                            "response": f"Error executing query after {max_retries} attempts: {last_error}",
                            "sql_executed": sql,
                            "error": last_error
                        }
                
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "sql_executed": None,
                "error": str(e)
            }