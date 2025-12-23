"""
Pydantic schemas for API request/response validation
סכמות Pydantic לאימות בקשות ותגובות API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Set
from datetime import datetime
from enum import Enum


# Enums
class SyllableTypeEnum(str, Enum):
    OPEN = "פתוחה"
    CLOSED = "סגורה"
    UNKNOWN = "לא ידוע"


class ShvaTypeEnum(str, Enum):
    NA = "נע"
    NAH = "נח"
    NONE = "אין"
    DOUBLE_NA = "שני שווא נע"
    DOUBLE_NAH = "שני שווא נח"
    NA_AND_NAH = "נע ונח"


# Source schemas
class SourceBase(BaseModel):
    name: str
    file_path: Optional[str] = None


class SourceCreate(SourceBase):
    content: str
    category: Optional[str] = None


class SourceResponse(SourceBase):
    id: int
    created_at: datetime
    word_count: int = 0
    
    class Config:
        from_attributes = True


# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True


# Word schemas
class WordBase(BaseModel):
    word: str
    word_plain: str


class WordAnalysisResult(WordBase):
    nikud_pattern: Optional[str] = None
    syllable_type: Optional[str] = None
    has_shva: bool = False
    shva_types: List[str] = []
    nikud_marks: List[str] = []
    has_dagesh: bool = False
    has_open_syllable: bool = False
    has_closed_syllable: bool = False
    special_cases: List[str] = []


class WordResponse(WordAnalysisResult):
    id: int
    position: Optional[int] = None
    context: Optional[str] = None
    source_name: Optional[str] = None
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Search schemas
class SearchFilters(BaseModel):
    word: Optional[str] = Field(None, description="חיפוש מילה עם ניקוד")
    word_plain: Optional[str] = Field(None, description="חיפוש מילה ללא ניקוד")
    syllable_type: Optional[str] = Field(None, description="סוג הברה")
    has_shva: Optional[bool] = Field(None, description="יש שווא")
    shva_type: Optional[str] = Field(None, description="סוג שווא")
    has_dagesh: Optional[bool] = Field(None, description="יש דגש")
    has_open_syllable: Optional[bool] = Field(None, description="יש הברה פתוחה")
    has_closed_syllable: Optional[bool] = Field(None, description="יש הברה סגורה")
    source_id: Optional[int] = Field(None, description="מזהה מקור")
    category_id: Optional[int] = Field(None, description="מזהה קטגוריה")
    min_length: Optional[int] = Field(None, description="אורך מילה מינימלי")
    max_length: Optional[int] = Field(None, description="אורך מילה מקסימלי")


class SearchResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    results: List[WordResponse]


# Statistics schemas
class SyllableDistribution(BaseModel):
    type: str
    count: int


class StatisticsResponse(BaseModel):
    total_words: int
    unique_words: int
    words_with_shva: int
    words_with_dagesh: int
    total_sources: int
    total_categories: int
    syllable_distribution: List[SyllableDistribution]


# Text analysis schemas
class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="טקסט לניתוח")
    source_name: Optional[str] = Field("טקסט ללא שם", description="שם המקור")
    category: Optional[str] = Field(None, description="קטגוריה")
    save_to_db: bool = Field(True, description="לשמור במסד נתונים")


class TextAnalysisResponse(BaseModel):
    source_id: Optional[int] = None
    total_words: int
    words: List[WordAnalysisResult]
    message: str


# Export schemas  
class ExportRequest(BaseModel):
    filters: Optional[SearchFilters] = None
    format: str = Field("xlsx", description="פורמט הייצוא")

