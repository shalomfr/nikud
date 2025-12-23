"""
Configuration settings for the Nikud Analyzer application
הגדרות תצורה לאפליקציית ניתוח הניקוד
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "מערכת ניתוח ניקוד"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://localhost/nikud_db"
    
    # For local development with SQLite fallback
    use_sqlite: bool = False
    sqlite_path: str = "nikud_database.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    # File upload settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {".txt", ".docx", ".xlsx"}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()

