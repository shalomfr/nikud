"""
Database connection and session management
חיבור למסד נתונים וניהול סשנים
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database URL based on settings
if settings.use_sqlite:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.sqlite_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    SQLALCHEMY_DATABASE_URL = settings.database_url
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session
    תלות המספקת סשן למסד נתונים
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    אתחול טבלאות מסד הנתונים
    """
    from app import models  # Import models to register them
    Base.metadata.create_all(bind=engine)

