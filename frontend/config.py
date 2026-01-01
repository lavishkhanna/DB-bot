import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_VERSION = "v1"

# API Endpoints
CHAT_ENDPOINT = f"{API_BASE_URL}/{API_VERSION}/chat/"
SCHEMA_ENDPOINT = f"{API_BASE_URL}/{API_VERSION}/chat/schema"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# UI Configuration
APP_TITLE = "🤖 Database Chatbot"
APP_ICON = "🗄️"
PAGE_TITLE = "DB Chatbot"