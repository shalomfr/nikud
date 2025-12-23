"""
Text analysis endpoints
נקודות קצה לניתוח טקסט
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    TextAnalysisRequest, TextAnalysisResponse,
    WordAnalysisResult, StatisticsResponse
)
from app.services.nikud_analyzer import nikud_analyzer
from app.services.search_engine import search_engine

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/text", response_model=TextAnalysisResponse)
async def analyze_text(
    request: TextAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    ניתוח טקסט
    Analyze text
    """
    source_id = None
    
    if request.save_to_db:
        # Save to database
        source_id, analyses = search_engine.load_text(
            db=db,
            text=request.text,
            source_name=request.source_name,
            category_name=request.category
        )
        words = [WordAnalysisResult(**a.to_dict()) for a in analyses]
    else:
        # Just analyze without saving
        analyses = nikud_analyzer.analyze_text(request.text)
        words = [WordAnalysisResult(**a.to_dict()) for a in analyses]

    return TextAnalysisResponse(
        source_id=source_id,
        total_words=len(words),
        words=words,
        message=f"נותחו {len(words)} מילים בהצלחה"
    )


@router.post("/word")
async def analyze_word(word: str):
    """
    ניתוח מילה בודדת
    Analyze single word
    """
    analysis = nikud_analyzer.analyze_word(word)
    return analysis.to_dict()


@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """
    קבלת סטטיסטיקות
    Get statistics
    """
    stats = search_engine.get_statistics(db)
    return StatisticsResponse(**stats)

