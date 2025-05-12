import os
import json
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

        # JWT Authentication
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

        # OpenAI Configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

        # AI Provider Selection - Only OpenAI is supported
        # If AI_PROVIDER is set to anything other than "openai" in the environment,
        # it will be ignored and "openai" will be used
        self.AI_PROVIDER = "openai"

        # Application Settings
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "POCA Service")
        self.API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")

        # Parse ALLOWED_ORIGINS from environment or use default
        allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
        if allowed_origins_env:
            try:
                self.ALLOWED_ORIGINS = json.loads(allowed_origins_env)
            except json.JSONDecodeError:
                self.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
        else:
            self.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

# Create settings instance
settings = Settings()
