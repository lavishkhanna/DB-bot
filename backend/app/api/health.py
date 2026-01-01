from fastapi import APIRouter
from app.database.connection import execute_query

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        execute_query("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }