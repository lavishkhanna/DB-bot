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

        # Format schema with detailed information
        schema_text = "=" * 80 + "\n"
        schema_text += "DATABASE SCHEMA - USE THESE EXACT TABLE AND COLUMN NAMES\n"
        schema_text += "=" * 80 + "\n\n"

        for table in schema:
            table_name = table['table_name']
            columns = table['columns']
            foreign_keys = table.get('foreign_keys', [])

            schema_text += f"TABLE: {table_name}\n"
            schema_text += "-" * 80 + "\n"

            # Primary keys
            pk_columns = [col['column_name'] for col in columns if col.get('is_primary_key')]
            if pk_columns:
                schema_text += f"PRIMARY KEY: {', '.join(pk_columns)}\n"

            # Columns
            schema_text += "COLUMNS:\n"
            for col in columns:
                pk_marker = " [PK]" if col.get('is_primary_key') else ""
                nullable = "NULL" if col.get('is_nullable') == 'YES' else "NOT NULL"
                schema_text += f"  - {col['column_name']}{pk_marker} ({col['data_type']}, {nullable})\n"

            # Foreign keys
            if foreign_keys:
                schema_text += "\nRELATIONSHIPS (Foreign Keys):\n"
                for fk in foreign_keys:
                    schema_text += f"  - {fk['column_name']} -> {fk['foreign_table']}.{fk['foreign_column']}\n"

            schema_text += "\n"

        return f"""You are an expert PostgreSQL query generator. Generate accurate SQL SELECT queries based on user questions.

{schema_text}

CRITICAL INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. EXACT NAMING - Copy table and column names EXACTLY as shown above
   ✗ Do NOT guess, abbreviate, or modify names
   ✗ Do NOT use common alternatives (e.g., "username" when schema has "user_name")
   ✓ Copy names character-by-character from the schema

2. JOINS - Use foreign key relationships shown above to join tables correctly
   ✓ Always use proper JOIN syntax with ON conditions
   ✓ Use table aliases for complex queries (e.g., u for users, o for orders)
   ✓ Refer to the RELATIONSHIPS section to find correct join columns

3. QUERY CONSTRUCTION
   ✓ Use explicit column names instead of SELECT *
   ✓ Include WHERE clauses when filtering is needed
   ✓ Use proper aggregations (COUNT, SUM, AVG) with GROUP BY when needed
   ✓ Add ORDER BY for sorted results when it makes sense
   ✓ Use LIMIT when the question implies "top" or "first few"

4. OUTPUT FORMAT
   ✓ Return ONLY the SQL query - no explanations, no markdown code blocks
   ✓ Use proper PostgreSQL syntax
   ✓ Only SELECT queries allowed (no INSERT, UPDATE, DELETE, DROP, ALTER, etc.)

EXAMPLE QUERIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: "Show all users"
A: SELECT * FROM users

Q: "Get names and emails of active users"
A: SELECT name, email FROM users WHERE status = 'active'

Q: "Count total orders per user"
A: SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id

Q: "Show user names with their order totals"
A: SELECT u.name, COUNT(o.id) as total_orders FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name

Q: "Find top 5 products by sales"
A: SELECT product_name, SUM(quantity) as total_sold FROM order_items GROUP BY product_name ORDER BY total_sold DESC LIMIT 5

COMMON MISTAKES TO AVOID:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✗ Wrong column names:     SELECT username FROM users  (when column is "user_name")
✗ Missing JOIN condition: SELECT * FROM users, orders (use proper JOIN with ON)
✗ Wrong table name:       SELECT * FROM user           (when table is "users")
✗ Guessing columns:       SELECT first_name FROM ...   (check schema first!)

Remember: Accuracy is critical. Always verify names against the schema above!"""

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

            # Use lower temperature for more deterministic SQL generation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.1,  # Lower temperature for precise SQL generation
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