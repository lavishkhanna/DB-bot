from app.database.connection import execute_query
import logging
import re
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger(__name__)

class DatabaseService:
    
    @staticmethod
    def get_schema():
        """Get comprehensive database schema information including relationships"""
        sql = """
            WITH table_info AS (
                SELECT
                    t.table_name,
                    array_agg(
                        json_build_object(
                            'column_name', c.column_name,
                            'data_type', c.data_type,
                            'is_nullable', c.is_nullable,
                            'is_primary_key', COALESCE(
                                (SELECT true
                                 FROM information_schema.table_constraints tc
                                 JOIN information_schema.key_column_usage kcu
                                   ON tc.constraint_name = kcu.constraint_name
                                   AND tc.table_schema = kcu.table_schema
                                 WHERE tc.constraint_type = 'PRIMARY KEY'
                                   AND tc.table_schema = 'public'
                                   AND tc.table_name = t.table_name
                                   AND kcu.column_name = c.column_name
                                 LIMIT 1
                                ), false
                            )
                        ) ORDER BY c.ordinal_position
                    ) as columns
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                    AND t.table_type = 'BASE TABLE'
                GROUP BY t.table_name
            ),
            foreign_keys AS (
                SELECT
                    tc.table_name,
                    array_agg(
                        json_build_object(
                            'column_name', kcu.column_name,
                            'foreign_table', ccu.table_name,
                            'foreign_column', ccu.column_name
                        )
                    ) as foreign_keys
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                GROUP BY tc.table_name
            )
            SELECT
                ti.table_name,
                ti.columns,
                COALESCE(fk.foreign_keys, ARRAY[]::json[]) as foreign_keys
            FROM table_info ti
            LEFT JOIN foreign_keys fk ON ti.table_name = fk.table_name
            ORDER BY ti.table_name
        """
        try:
            results = execute_query(sql)
            return results
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            raise
    
    @staticmethod
    def validate_sql(sql: str) -> tuple[bool, str]:
        """Validate SQL query for safety"""
        sql_lower = sql.lower().strip()
        
        # Only allow SELECT queries
        if not sql_lower.startswith('select'):
            return False, "Only SELECT queries are allowed"
        
        # Block dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'truncate', 'insert', 
            'update', 'alter', 'create', 'grant', 'revoke'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_lower):
                return False, f"Dangerous keyword '{keyword}' not allowed"
        
        return True, "Valid"
    
    @staticmethod
    def serialize_value(value):
        """Convert non-JSON-serializable types to JSON-serializable ones"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return value
    
    @staticmethod
    def serialize_row(row):
        """Serialize a database row to JSON-compatible dict"""
        if isinstance(row, dict):
            return {key: DatabaseService.serialize_value(value) for key, value in row.items()}
        return row

    @staticmethod
    def get_sample_data(table_name: str, limit: int = 3):
        """Get sample data from a table to help LLM understand data structure"""
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        try:
            is_valid, message = DatabaseService.validate_sql(sql)
            if not is_valid:
                raise ValueError(message)

            results = execute_query(sql)
            if results:
                return [DatabaseService.serialize_row(row) for row in results]
            return []
        except Exception as e:
            logger.error(f"Error getting sample data from {table_name}: {e}")
            return []
    
    @staticmethod
    def execute_user_query(sql: str):
        """Execute user-provided SQL query with validation"""
        # Validate
        is_valid, message = DatabaseService.validate_sql(sql)
        if not is_valid:
            raise ValueError(message)
        
        try:
            results = execute_query(sql)
            
            # Serialize results to make them JSON-compatible
            if results:
                serialized_results = [
                    DatabaseService.serialize_row(row) 
                    for row in results
                ]
            else:
                serialized_results = []
            
            return {
                "success": True,
                "data": serialized_results,
                "row_count": len(serialized_results) if serialized_results else 0
            }
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }