from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import logging

from app.config import settings
from app.db.database import engine, Base
from app.api import (
    auth,
    users,
    hospitals,
    ai
)
from app.websockets import ai_assistant
from app.errors import http_exception_handler, validation_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A comprehensive service for doctor-patient communication with AI assistance",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(hospitals.router, prefix=f"{settings.API_V1_PREFIX}/hospitals", tags=["Hospitals"])
app.include_router(ai.router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["AI Assistant"])
app.include_router(ai_assistant.router, prefix=f"{settings.API_V1_PREFIX}/ai-assistant", tags=["AI Assistant WebSocket"])

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "description": "A comprehensive service for doctor-patient communication with AI assistance",
        "version": "1.0.0",
        "documentation": f"{settings.API_V1_PREFIX}/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
