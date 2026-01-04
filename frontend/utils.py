import pandas as pd
import json
from typing import List, Dict, Any

def format_table_data(data: List[Dict]) -> pd.DataFrame:
    """Convert query results to pandas DataFrame"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def format_sql_for_display(sql: str) -> str:
    """Format SQL query for better display"""
    # Add syntax highlighting-friendly formatting
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'GROUP BY', 'ORDER BY', 'LIMIT']
    formatted = sql
    for keyword in keywords:
        formatted = formatted.replace(keyword, f"\n{keyword}")
    return formatted.strip()

def get_sample_questions() -> List[str]:
    """Return sample questions users can ask"""
    return [
        "How many users are in the database?",
        "Show me customers and their total number of rentals",
        "What's the revenue breakdown by film category?",
        "What's the average rental duration"
    ]

def export_to_csv(df: pd.DataFrame, filename: str = "query_results.csv"):
    """Export DataFrame to CSV"""
    return df.to_csv(index=False).encode('utf-8')