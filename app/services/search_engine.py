"""
מנוע חיפוש וסינון לטקסטים עם ניקוד - מותאם ל-SQLAlchemy
Search and Filter Engine for Hebrew Texts with Nikud - SQLAlchemy adapted
"""

from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import json

from app.models import Word, Source, Category, NikudRule
from app.services.nikud_analyzer import NikudAnalyzer, WordAnalysis
from app.schemas import SearchFilters


class SearchEngine:
    """מנוע חיפוש וסינון"""

    def __init__(self, analyzer: NikudAnalyzer = None):
        self.analyzer = analyzer or NikudAnalyzer()

    def load_text(
        self,
        db: Session,
        text: str,
        source_name: str,
        category_name: Optional[str] = None
    ) -> Tuple[int, List[WordAnalysis]]:
        """
        טעינת טקסט למערכת
        Load text into the system
        """
        # Create source
        source = Source(name=source_name, content=text)
        db.add(source)
        db.flush()  # Get the ID

        # Get or create category
        category = None
        if category_name:
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                db.add(category)
                db.flush()

        # Analyze text
        analyses = self.analyzer.analyze_text(text)

        # Split text into sentences for context
        sentences = text.split('.')

        # Save analyzed words
        for i, analysis in enumerate(analyses):
            # Find context
            context = ""
            for sentence in sentences:
                if analysis.word in sentence:
                    context = sentence.strip()
                    break

            word = Word(
                word=analysis.word,
                word_plain=analysis.word_plain,
                nikud_pattern=analysis.nikud_pattern,
                syllable_type=analysis.syllable_type.value,
                has_shva=analysis.has_shva,
                shva_types=[s.value for s in analysis.shva_types],
                nikud_marks=list(analysis.nikud_marks),
                has_dagesh=analysis.has_dagesh,
                has_open_syllable=analysis.has_open_syllable,
                has_closed_syllable=analysis.has_closed_syllable,
                special_cases=analysis.special_cases,
                source_id=source.id,
                position=i,
                context=context,
                category_id=category.id if category else None
            )
            db.add(word)

        db.commit()
        return source.id, analyses

    def search(
        self,
        db: Session,
        filters: SearchFilters,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[Dict], int]:
        """
        חיפוש לפי סינונים
        Search by filters
        """
        query = db.query(Word).outerjoin(Source).outerjoin(Category)

        # Apply filters
        if filters.word:
            query = query.filter(Word.word.ilike(f"%{filters.word}%"))

        if filters.word_plain:
            query = query.filter(Word.word_plain.ilike(f"%{filters.word_plain}%"))

        if filters.syllable_type:
            query = query.filter(Word.syllable_type == filters.syllable_type)

        if filters.has_shva is not None:
            query = query.filter(Word.has_shva == filters.has_shva)

        if filters.has_dagesh is not None:
            query = query.filter(Word.has_dagesh == filters.has_dagesh)

        if filters.has_open_syllable is not None:
            query = query.filter(Word.has_open_syllable == filters.has_open_syllable)

        if filters.has_closed_syllable is not None:
            query = query.filter(Word.has_closed_syllable == filters.has_closed_syllable)

        if filters.source_id:
            query = query.filter(Word.source_id == filters.source_id)

        if filters.category_id:
            query = query.filter(Word.category_id == filters.category_id)

        if filters.min_length:
            query = query.filter(func.length(Word.word_plain) >= filters.min_length)

        if filters.max_length:
            query = query.filter(func.length(Word.word_plain) <= filters.max_length)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        words = query.order_by(Word.word).offset(offset).limit(per_page).all()

        # Convert to dict
        results = []
        for word in words:
            result = {
                "id": word.id,
                "word": word.word,
                "word_plain": word.word_plain,
                "nikud_pattern": word.nikud_pattern,
                "syllable_type": word.syllable_type,
                "has_shva": word.has_shva,
                "shva_types": word.shva_types or [],
                "nikud_marks": word.nikud_marks or [],
                "has_dagesh": word.has_dagesh,
                "has_open_syllable": word.has_open_syllable,
                "has_closed_syllable": word.has_closed_syllable,
                "special_cases": word.special_cases or [],
                "position": word.position,
                "context": word.context,
                "source_name": word.source.name if word.source else None,
                "category_name": word.category.name if word.category else None
            }
            results.append(result)

        return results, total

    def get_statistics(self, db: Session) -> Dict:
        """
        קבלת סטטיסטיקות על המסד
        Get database statistics
        """
        stats = {}

        # Total words
        stats['total_words'] = db.query(Word).count()

        # Unique words
        stats['unique_words'] = db.query(func.count(func.distinct(Word.word))).scalar()

        # Syllable distribution
        syllable_dist = db.query(
            Word.syllable_type,
            func.count(Word.id)
        ).group_by(Word.syllable_type).all()
        
        stats['syllable_distribution'] = [
            {"type": s_type or "לא ידוע", "count": count}
            for s_type, count in syllable_dist
        ]

        # Words with shva
        stats['words_with_shva'] = db.query(Word).filter(Word.has_shva == True).count()

        # Words with dagesh
        stats['words_with_dagesh'] = db.query(Word).filter(Word.has_dagesh == True).count()

        # Total sources
        stats['total_sources'] = db.query(Source).count()

        # Total categories
        stats['total_categories'] = db.query(Category).count()

        return stats

    def get_sources(self, db: Session) -> List[Dict]:
        """Get all sources with word counts"""
        sources = db.query(
            Source,
            func.count(Word.id).label('word_count')
        ).outerjoin(Word).group_by(Source.id).all()

        return [
            {
                "id": source.id,
                "name": source.name,
                "created_at": source.created_at,
                "word_count": word_count
            }
            for source, word_count in sources
        ]

    def get_categories(self, db: Session) -> List[Dict]:
        """Get all categories with word counts"""
        categories = db.query(
            Category,
            func.count(Word.id).label('word_count')
        ).outerjoin(Word).group_by(Category.id).all()

        return [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "word_count": word_count
            }
            for cat, word_count in categories
        ]

    def delete_source(self, db: Session, source_id: int) -> bool:
        """Delete a source and its words"""
        source = db.query(Source).filter(Source.id == source_id).first()
        if source:
            db.delete(source)
            db.commit()
            return True
        return False


# Singleton instance
search_engine = SearchEngine()

