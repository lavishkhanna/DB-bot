import requests
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def health_check(self) -> Dict:
        """Check if backend is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def get_schema(self) -> Optional[Dict]:
        """Get database schema"""
        try:
            response = self.session.get(f"{self.base_url}/v1/chat/schema", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return None
    
    def send_message(self, message: str, conversation_history: Optional[List] = None) -> Dict:
        """Send a chat message"""
        try:
            payload = {
                "message": message,
                "conversation_history": conversation_history
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {
                "response": "Request timed out. The query might be too complex or the server is slow.",
                "error": "Timeout"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            return {
                "response": f"Error communicating with backend: {str(e)}",
                "error": str(e)
            }