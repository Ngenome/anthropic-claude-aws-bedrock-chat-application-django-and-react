from typing import Optional, List, Any, Union
from pydantic import field_validator, AnyHttpUrl, Field
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Mantice AI Assistant API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS - Compatible with Django naming
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = Field(
        default="", 
        alias="CORS_ALLOWED_ORIGINS"
    )
    FRONTEND_URL: str = "http://localhost:3000"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if not v:  # Handle empty string
                return []
            if v.startswith("["):
                # Handle JSON array format
                import json
                return json.loads(v)
            else:
                # Handle comma-separated format
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_EXPIRE_SECONDS: int = 300  # 5 minutes
    
    # Email Configuration - Compatible with Django naming
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = Field(default=587, alias="EMAIL_PORT")
    SMTP_HOST: str = Field(default="smtp.zoho.com", alias="EMAIL_HOST")
    SMTP_USER: str = Field(alias="EMAIL_USER")
    SMTP_PASSWORD: str = Field(alias="EMAIL_PASSWORD")
    DEFAULT_FROM_EMAIL: str = Field(alias="EMAIL_USER")  # Use same as SMTP_USER
    SUPPORT_EMAIL: str = Field(alias="EMAIL_USER")  # Use same as SMTP_USER
    
    # AWS Configuration - Compatible with existing naming
    AWS_ACCESS_KEY_ID: str = Field(alias="AWS_S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(alias="AWS_S3_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET_NAME: str
    AWS_S3_REGION: str = Field(default="us-west-2", alias="AWS_S3_BUCKET_REGION")
    
    # AWS Bedrock (for Claude AI) - Use existing Anthropic key for now
    AWS_BEDROCK_ACCESS_KEY_ID: str = Field(alias="AWS_BEDROCK_ACCESS_KEY_ID")
    AWS_BEDROCK_SECRET_ACCESS_KEY: str = Field(alias="AWS_BEDROCK_SECRET_ACCESS_KEY") 
    AWS_BEDROCK_REGION: str = "us-west-2"
    AWS_BEDROCK_REGION_FALLBACK: str = "us-east-1"
    
    @property
    def AWS_STORAGE_BUCKET_NAME(self) -> str:
        """Alias for S3 bucket name for compatibility."""
        return self.AWS_S3_BUCKET_NAME
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Additional API Keys (optional to avoid validation errors)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AZURE_OPENAI_KEY: Optional[str] = None
    BAZURE_OPENAI_KEY: Optional[str] = None
    PIXABAY_API_KEY: Optional[str] = None
    
    # Additional fields from Django (optional)
    HOST: Optional[str] = None
    ALLOWED_HOSTS: Optional[str] = None
    CSRF_TRUSTED_ORIGINS: Optional[str] = None
    AWS_S3_BUCKET_URL: Optional[str] = None
    
    # Paystack (if needed)
    PAYSTACK_SECRET_KEY: Optional[str] = None
    TOKEN_PRICE: float = 0.01
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf", 
        "text/plain", 
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # 1 hour
    LOGIN_RATE_LIMIT: int = 5  # attempts per period
    REGISTRATION_RATE_LIMIT: int = 3
    PASSWORD_RESET_RATE_LIMIT: int = 3
    
    # Security
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION: int = 30 * 60  # 30 minutes
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # Claude AI Configuration
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7
    CLAUDE_DEFAULT_MODEL: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_FALLBACK_MODEL: str = "anthropic.claude-3-5-haiku-20241022-v1:0"
    
    # Default System Prompt
    DEFAULT_SYSTEM_PROMPT: str = """You are Claude, an AI assistant created by Anthropic. You are helpful, harmless, and honest. You should be conversational and engaging while providing accurate, thoughtful responses. If you're not sure about something, say so rather than guessing."""
    
    # Memory & Context
    MAX_MEMORY_ITEMS: int = 10
    MAX_PROJECT_KNOWLEDGE_TOKENS: int = 160000  # 80% of context window
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields to prevent validation errors
    }


# Create settings instance
settings = Settings()

# Derived configurations
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# AWS S3 URLs
AWS_S3_CUSTOM_DOMAIN = f"{settings.AWS_S3_BUCKET_NAME}.s3.amazonaws.com"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent 