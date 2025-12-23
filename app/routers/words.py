"""
Word search and filter endpoints
נקודות קצה לחיפוש וסינון מילים
"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database import get_db
from app.schemas import SearchFilters, SearchResponse, WordResponse
from app.services.search_engine import search_engine
from app.services.excel_exporter import excel_exporter

router = APIRouter(prefix="/api/words", tags=["words"])


@router.get("/search", response_model=SearchResponse)
async def search_words(
    word: Optional[str] = Query(None, description="חיפוש מילה עם ניקוד"),
    word_plain: Optional[str] = Query(None, description="חיפוש מילה ללא ניקוד"),
    syllable_type: Optional[str] = Query(None, description="סוג הברה"),
    has_shva: Optional[bool] = Query(None, description="יש שווא"),
    shva_type: Optional[str] = Query(None, description="סוג שווא"),
    has_dagesh: Optional[bool] = Query(None, description="יש דגש"),
    has_open_syllable: Optional[bool] = Query(None, description="יש הברה פתוחה"),
    has_closed_syllable: Optional[bool] = Query(None, description="יש הברה סגורה"),
    source_id: Optional[int] = Query(None, description="מזהה מקור"),
    category_id: Optional[int] = Query(None, description="מזהה קטגוריה"),
    min_length: Optional[int] = Query(None, description="אורך מילה מינימלי"),
    max_length: Optional[int] = Query(None, description="אורך מילה מקסימלי"),
    page: int = Query(1, ge=1, description="מספר עמוד"),
    per_page: int = Query(50, ge=1, le=200, description="תוצאות לעמוד"),
    db: Session = Depends(get_db)
):
    """
    חיפוש מילים לפי סינונים
    Search words by filters
    """
    filters = SearchFilters(
        word=word,
        word_plain=word_plain,
        syllable_type=syllable_type,
        has_shva=has_shva,
        shva_type=shva_type,
        has_dagesh=has_dagesh,
        has_open_syllable=has_open_syllable,
        has_closed_syllable=has_closed_syllable,
        source_id=source_id,
        category_id=category_id,
        min_length=min_length,
        max_length=max_length
    )

    results, total = search_engine.search(db, filters, page, per_page)
    pages = math.ceil(total / per_page) if total > 0 else 1

    return SearchResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        results=results
    )


@router.get("/export")
async def export_words(
    word: Optional[str] = Query(None),
    word_plain: Optional[str] = Query(None),
    syllable_type: Optional[str] = Query(None),
    has_shva: Optional[bool] = Query(None),
    has_dagesh: Optional[bool] = Query(None),
    source_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    ייצוא תוצאות חיפוש לאקסל
    Export search results to Excel
    """
    filters = SearchFilters(
        word=word,
        word_plain=word_plain,
        syllable_type=syllable_type,
        has_shva=has_shva,
        has_dagesh=has_dagesh,
        source_id=source_id,
        category_id=category_id
    )

    # Get all results (no pagination for export)
    results, _ = search_engine.search(db, filters, page=1, per_page=10000)

    # Export to Excel
    excel_bytes = excel_exporter.export_to_bytes(results)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=nikud_results.xlsx"
        }
    )

