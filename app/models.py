"""
SQLAlchemy database models
מודלי מסד נתונים SQLAlchemy
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Source(Base):
    """
    Text source model - מודל מקור טקסט
    """
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    words = relationship("Word", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}')>"


class Category(Base):
    """
    Category model - מודל קטגוריה
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    words = relationship("Word", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Word(Base):
    """
    Word model with nikud analysis - מודל מילה עם ניתוח ניקוד
    """
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic word data
    word = Column(String(100), nullable=False, index=True)  # עם ניקוד
    word_plain = Column(String(100), nullable=False, index=True)  # ללא ניקוד
    nikud_pattern = Column(String(200), nullable=True)
    
    # Syllable analysis
    syllable_type = Column(String(50), nullable=True, index=True)
    has_open_syllable = Column(Boolean, default=False)
    has_closed_syllable = Column(Boolean, default=False)
    
    # Shva analysis
    has_shva = Column(Boolean, default=False, index=True)
    shva_types = Column(JSON, nullable=True)  # List of shva types
    
    # Nikud marks
    nikud_marks = Column(JSON, nullable=True)  # List of nikud marks
    has_dagesh = Column(Boolean, default=False, index=True)
    
    # Special cases
    special_cases = Column(JSON, nullable=True)  # List of special cases
    
    # Context and position
    position = Column(Integer, nullable=True)
    context = Column(Text, nullable=True)
    
    # Foreign keys
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Relationships
    source = relationship("Source", back_populates="words")
    category = relationship("Category", back_populates="words")
    
    def __repr__(self):
        return f"<Word(id={self.id}, word='{self.word}')>"


class NikudRule(Base):
    """
    Nikud rule model - מודל כלל ניקוד
    """
    __tablename__ = "nikud_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Primary rule
    category = Column(String(100), nullable=False)
    filter = Column(String(100), nullable=False)
    result = Column(String(200), nullable=True)
    
    # Secondary rules (multi-level filtering)
    category2 = Column(String(100), nullable=True)
    filter2 = Column(String(100), nullable=True)
    category3 = Column(String(100), nullable=True)
    filter3 = Column(String(100), nullable=True)
    category4 = Column(String(100), nullable=True)
    filter4 = Column(String(100), nullable=True)
    
    # Final result and notes
    final_result = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<NikudRule(id={self.id}, category='{self.category}', filter='{self.filter}')>"

