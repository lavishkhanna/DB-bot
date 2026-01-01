# from openai import OpenAI
# from app.config import get_settings
# import logging
# import json
# import re

# logger = logging.getLogger(__name__)
# settings = get_settings()

# class LLMService:
#     def __init__(self):
#         self.settings = settings
        
#         if settings.LLM_PROVIDER == "openrouter":
#             self.client = OpenAI(
#                 api_key=settings.OPENROUTER_API_KEY,
#                 base_url=settings.OPENROUTER_BASE_URL,
#                 default_headers={
#                     "HTTP-Referer": "http://localhost:8000",
#                     "X-Title": "DB Chatbot"
#                 }
#             )
#         else:
#             self.client = OpenAI(
#                 api_key="ollama",
#                 base_url=settings.OLLAMA_BASE_URL
#             )
        
#         self.model = settings.LLM_MODEL
#         logger.info(f"✅ LLM Service initialized with model: {self.model}")


#     def create_system_prompt(self, schema):
#         """Create system prompt with schema info"""
        
#         # Format schema in a clearer way
#         schema_text = "DATABASE SCHEMA:\n\n"
#         for table in schema:
#             table_name = table['table_name']
#             columns = table['columns']
            
#             schema_text += f"Table: {table_name}\n"
#             schema_text += "Columns:\n"
#             for col in columns:
#                 schema_text += f"  - {col['column_name']} ({col['data_type']})\n"
#             schema_text += "\n"
        
#         return f"""You are a SQL query generator. Generate ONLY valid PostgreSQL SELECT queries.

#     {schema_text}

#     CRITICAL RULES:
#     1. Use EXACT column names from the schema above - do not guess or modify them
#     2. Use EXACT table names from the schema above
#     3. Column names are case-sensitive - copy them exactly as shown
#     4. Only use columns that exist in the schema
#     5. Only write SELECT queries (no INSERT, UPDATE, DELETE, DROP)
#     6. Do not use markdown code blocks or explanations
#     7. Output ONLY the SQL query

#     EXAMPLES:
#     User: "How many users?"
#     You: SELECT COUNT(*) FROM users

#     User: "Show all course titles"
#     You: SELECT title FROM courses

#     User: "Users created this month"
#     You: SELECT * FROM users WHERE created_at >= date_trunc('month', CURRENT_DATE)

#     User: "Show user names and emails"
#     You: SELECT name, email FROM users

#     Remember: Copy column names EXACTLY as they appear in the schema!
#     REMEMBER: Column names must match the with their respective tables."""

#     def chat(self, messages: list, schema: list):
#         """Send chat to LLM - returns SQL query as text"""
#         try:
#             system_prompt = self.create_system_prompt(schema)
            
#             # Build messages with system prompt
#             full_messages = [{"role": "system", "content": system_prompt}]
            
#             # Add user messages (filter to only user/assistant roles)
#             for msg in messages:
#                 if msg.get("role") in ["user", "assistant"]:
#                     full_messages.append({
#                         "role": msg["role"],
#                         "content": msg["content"]
#                     })
            
#             logger.info(f"Sending {len(full_messages)} messages to LLM")
            
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=full_messages,
#                 temperature=settings.LLM_TEMPERATURE,
#                 max_tokens=settings.LLM_MAX_TOKENS
#             )
            
#             return response
            
#         except Exception as e:
#             logger.error(f"LLM error: {e}")
#             raise
    
#     def extract_sql(self, text: str) -> str:
#         """Extract SQL query from LLM response"""
#         # Remove markdown code blocks if present
#         text = re.sub(r'```sql\s*', '', text)
#         text = re.sub(r'```\s*', '', text)
        
#         # Remove common prefixes
#         text = re.sub(r'^(Here\'s the query:|Query:|SQL:)\s*', '', text, flags=re.IGNORECASE)
        
#         # Trim whitespace
#         sql = text.strip()
        
#         # Remove trailing periods or semicolons
#         sql = sql.rstrip('.;')
        
#         return sql




from openai import OpenAI
from app.config import get_settings
import logging
import json
import re

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMService:
    def __init__(self):
        self.settings = settings
        
        if settings.LLM_PROVIDER == "openrouter":
            self.client = OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "DB Chatbot"
                }
            )
        else:
            self.client = OpenAI(
                api_key="ollama",
                base_url=settings.OLLAMA_BASE_URL
            )
        
        self.model = settings.LLM_MODEL
        logger.info(f"✅ LLM Service initialized with model: {self.model}")
    
    def create_system_prompt(self, schema):
        """Create detailed system prompt with schema"""
        
        # Format schema very clearly
        schema_text = "DATABASE SCHEMA (use these EXACT names):\n\n"
        
        for table in schema:
            table_name = table['table_name']
            columns = table['columns']
            
            schema_text += f"📊 Table: {table_name}\n"
            schema_text += "   Columns:\n"
            for col in columns:
                schema_text += f"   • {col['column_name']} (type: {col['data_type']})\n"
            schema_text += "\n"
        
        return f"""You are a PostgreSQL query generator. Your job is to convert user questions into valid SQL SELECT queries.

{schema_text}

⚠️ CRITICAL RULES:
1. Use column names EXACTLY as shown above - copy them character-by-character
2. Do NOT guess, modify, or invent column names
3. If you're unsure about a column name, look at the schema again
4. Only SELECT queries allowed (no INSERT, UPDATE, DELETE, DROP)
5. Output ONLY the SQL query - no explanations or markdown

✅ CORRECT Examples:
User: "Show user names"
You: SELECT name FROM users

User: "Count all courses"  
You: SELECT COUNT(*) FROM courses

User: "Show course titles and descriptions"
You: SELECT title, description FROM courses

❌ WRONG Examples (DO NOT DO THIS):
User: "Show user names"
You: SELECT username FROM users  ← WRONG! Column is "name" not "username"

Remember: Copy column names EXACTLY from the schema above!"""

    def chat(self, messages: list, schema: list):
        """Send chat to LLM"""
        try:
            system_prompt = self.create_system_prompt(schema)
            
            full_messages = [{"role": "system", "content": system_prompt}]
            
            for msg in messages:
                if msg.get("role") in ["user", "assistant"]:
                    full_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            logger.info(f"Sending {len(full_messages)} messages to LLM")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise
    
    def extract_sql(self, text: str) -> str:
        """Extract SQL from LLM response"""
        # Remove markdown
        text = re.sub(r'```sql\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Remove common prefixes
        text = re.sub(r'^(Here\'s the query:|Query:|SQL:)\s*', '', text, flags=re.IGNORECASE)
        
        # Clean up
        sql = text.strip().rstrip('.;')
        
        return sql