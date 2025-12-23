"""
Text source management endpoints
נקודות קצה לניהול מקורות טקסט
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import SourceCreate, SourceResponse
from app.services.search_engine import search_engine
from app.models import Source

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/", response_model=List[SourceResponse])
async def list_sources(db: Session = Depends(get_db)):
    """
    קבלת רשימת כל המקורות
    Get list of all sources
    """
    sources = search_engine.get_sources(db)
    return sources


@router.post("/", response_model=SourceResponse)
async def create_source(
    source: SourceCreate,
    db: Session = Depends(get_db)
):
    """
    טעינת מקור טקסט חדש
    Load new text source
    """
    source_id, analyses = search_engine.load_text(
        db=db,
        text=source.content,
        source_name=source.name,
        category_name=source.category
    )

    # Get the created source
    db_source = db.query(Source).filter(Source.id == source_id).first()

    return {
        "id": db_source.id,
        "name": db_source.name,
        "file_path": db_source.file_path,
        "created_at": db_source.created_at,
        "word_count": len(analyses)
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    העלאת קובץ טקסט
    Upload text file
    """
    # Read file content
    content = await file.read()

    # Try to decode as UTF-8
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = content.decode('cp1255')  # Hebrew Windows encoding

    # Use filename as source name if not provided
    name = source_name or file.filename or "קובץ ללא שם"

    source_id, analyses = search_engine.load_text(
        db=db,
        text=text,
        source_name=name,
        category_name=category
    )

    return {
        "message": "הקובץ נטען בהצלחה",
        "source_id": source_id,
        "word_count": len(analyses),
        "filename": file.filename
    }


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """
    מחיקת מקור טקסט
    Delete text source
    """
    success = search_engine.delete_source(db, source_id)
    if not success:
        raise HTTPException(status_code=404, detail="מקור לא נמצא")

    return {"message": "המקור נמחק בהצלחה"}


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """
    קבלת רשימת קטגוריות
    Get list of categories
    """
    return search_engine.get_categories(db)

