from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.database.connection import init_db_pool, close_db_pool
from app.api import chat
from app.api.health import router as health_router
from app.utils.logger import setup_logging

# Get settings first
settings = get_settings()

# Setup logging with configured level
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    init_db_pool()
    yield
    # Shutdown
    logger.info("Shutting down...")
    close_db_pool()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(chat.router, prefix=f"/{settings.API_VERSION}")

@app.get("/")
async def root():
    return {
        "message": "DB Chatbot API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }