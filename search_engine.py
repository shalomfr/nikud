"""
מנוע חיפוש וסינון לטקסטים עם ניקוד
Search and Filter Engine for Hebrew Texts with Nikud
"""

import sqlite3
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import asdict
from datetime import datetime
import pandas as pd
from pathlib import Path

from nikud_analyzer import NikudAnalyzer, WordAnalysis, SyllableType, ShvaType

class DatabaseManager:
    """מנהל מסד נתונים SQLite"""

    def __init__(self, db_path: str = "nikud_database.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """אתחול מסד הנתונים"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")

        # יצירת טבלאות
        self.conn.executescript("""
            -- טבלת מקורות טקסט
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                file_path TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- טבלת קטגוריות
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );

            -- טבלת מילים
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                word_plain TEXT NOT NULL,
                nikud_pattern TEXT,
                syllable_type TEXT,
                has_shva BOOLEAN,
                shva_types TEXT,  -- JSON
                nikud_marks TEXT,  -- JSON
                has_dagesh BOOLEAN,
                has_open_syllable BOOLEAN,
                has_closed_syllable BOOLEAN,
                special_cases TEXT,  -- JSON
                source_id INTEGER,
                position INTEGER,
                context TEXT,
                category_id INTEGER,
                FOREIGN KEY (source_id) REFERENCES sources(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            -- טבלת כללי ניקוד (מהאקסל)
            CREATE TABLE IF NOT EXISTS nikud_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                filter TEXT NOT NULL,
                result TEXT,
                category2 TEXT,
                filter2 TEXT,
                category3 TEXT,
                filter3 TEXT,
                category4 TEXT,
                filter4 TEXT,
                final_result TEXT,
                notes TEXT
            );

            -- אינדקסים לשיפור ביצועים
            CREATE INDEX IF NOT EXISTS idx_word ON words(word);
            CREATE INDEX IF NOT EXISTS idx_word_plain ON words(word_plain);
            CREATE INDEX IF NOT EXISTS idx_syllable_type ON words(syllable_type);
            CREATE INDEX IF NOT EXISTS idx_has_shva ON words(has_shva);
            CREATE INDEX IF NOT EXISTS idx_source ON words(source_id);
            CREATE INDEX IF NOT EXISTS idx_category ON words(category_id);
        """)
        self.conn.commit()

    def load_rules_from_excel(self, excel_path: str):
        """טעינת כללי ניקוד מקובץ אקסל"""
        df = pd.read_excel(excel_path)

        # ניקוי הנתונים
        df = df.dropna(how='all')  # הסרת שורות ריקות לחלוטין

        for _, row in df.iterrows():
            if pd.notna(row.get('קטגוריה')) and pd.notna(row.get('מסנן')):
                self.conn.execute("""
                    INSERT OR REPLACE INTO nikud_rules
                    (category, filter, result, category2, filter2,
                     category3, filter3, category4, filter4, final_result, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('קטגוריה'),
                    row.get('מסנן'),
                    row.get('תוצאה'),
                    row.get('Unnamed: 3'),  # category2
                    row.get('Unnamed: 4'),  # filter2
                    row.get('Unnamed: 5'),  # category3
                    row.get('Unnamed: 6'),  # filter3
                    row.get('Unnamed: 7'),  # category4
                    row.get('Unnamed: 8'),  # filter4
                    row.get('Unnamed: 9'),  # final_result
                    None  # notes
                ))

        self.conn.commit()

    def add_source(self, name: str, content: str, file_path: Optional[str] = None) -> int:
        """הוספת מקור טקסט חדש"""
        cursor = self.conn.execute(
            "INSERT INTO sources (name, content, file_path) VALUES (?, ?, ?)",
            (name, content, file_path)
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_category(self, name: str, description: str = "") -> int:
        """הוספת קטגוריה חדשה"""
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_word(self, analysis: WordAnalysis, source_id: int,
                 position: int, context: str = "", category_id: Optional[int] = None):
        """הוספת מילה מנותחת למסד הנתונים"""
        self.conn.execute("""
            INSERT INTO words
            (word, word_plain, nikud_pattern, syllable_type, has_shva,
             shva_types, nikud_marks, has_dagesh, has_open_syllable,
             has_closed_syllable, special_cases, source_id, position,
             context, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.word,
            analysis.word_plain,
            analysis.nikud_pattern,
            analysis.syllable_type.value,
            analysis.has_shva,
            json.dumps([s.value for s in analysis.shva_types], ensure_ascii=False),
            json.dumps(list(analysis.nikud_marks), ensure_ascii=False),
            analysis.has_dagesh,
            analysis.has_open_syllable,
            analysis.has_closed_syllable,
            json.dumps(analysis.special_cases, ensure_ascii=False),
            source_id,
            position,
            context,
            category_id
        ))

    def close(self):
        """סגירת החיבור למסד הנתונים"""
        if self.conn:
            self.conn.close()


class SearchEngine:
    """מנוע חיפוש וסינון"""

    def __init__(self, db_manager: DatabaseManager, analyzer: NikudAnalyzer):
        self.db = db_manager
        self.analyzer = analyzer

    def load_text(self, text: str, source_name: str,
                  category: Optional[str] = None) -> int:
        """טעינת טקסט למערכת"""
        # הוספת המקור
        source_id = self.db.add_source(source_name, text)

        # הוספת קטגוריה אם צוינה
        category_id = None
        if category:
            category_id = self.db.add_category(category)

        # ניתוח הטקסט
        analyses = self.analyzer.analyze_text(text)

        # שמירת המילים המנותחות
        sentences = text.split('.')  # פיצול למשפטים לצורך הקשר
        current_position = 0

        for i, analysis in enumerate(analyses):
            # מציאת ההקשר (המשפט שבו המילה נמצאת)
            context = ""
            for sentence in sentences:
                if analysis.word in sentence:
                    context = sentence.strip()
                    break

            self.db.add_word(
                analysis=analysis,
                source_id=source_id,
                position=i,
                context=context,
                category_id=category_id
            )

        self.db.conn.commit()
        return source_id

    def build_query(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """בניית שאילתת SQL מסינונים"""
        conditions = []
        params = []

        # סינון לפי מילה
        if filters.get('word'):
            conditions.append("word LIKE ?")
            params.append(f"%{filters['word']}%")

        if filters.get('word_plain'):
            conditions.append("word_plain LIKE ?")
            params.append(f"%{filters['word_plain']}%")

        # סינון לפי סוג הברה
        if filters.get('syllable_type'):
            conditions.append("syllable_type = ?")
            params.append(filters['syllable_type'])

        # סינון לפי שווא
        if filters.get('has_shva') is not None:
            conditions.append("has_shva = ?")
            params.append(int(filters['has_shva']))

        if filters.get('shva_type'):
            conditions.append("shva_types LIKE ?")
            params.append(f'%"{filters["shva_type"]}"%')

        # סינון לפי דגש
        if filters.get('has_dagesh') is not None:
            conditions.append("has_dagesh = ?")
            params.append(int(filters['has_dagesh']))

        # סינון לפי הברה פתוחה/סגורה
        if filters.get('has_open_syllable') is not None:
            conditions.append("has_open_syllable = ?")
            params.append(int(filters['has_open_syllable']))

        if filters.get('has_closed_syllable') is not None:
            conditions.append("has_closed_syllable = ?")
            params.append(int(filters['has_closed_syllable']))

        # סינון לפי קטגוריה
        if filters.get('category_id'):
            conditions.append("category_id = ?")
            params.append(filters['category_id'])

        # סינון לפי מקור
        if filters.get('source_id'):
            conditions.append("source_id = ?")
            params.append(filters['source_id'])

        # סינון לפי אורך מילה
        if filters.get('min_length'):
            conditions.append("LENGTH(word_plain) >= ?")
            params.append(filters['min_length'])

        if filters.get('max_length'):
            conditions.append("LENGTH(word_plain) <= ?")
            params.append(filters['max_length'])

        # בניית השאילתה
        query = """
            SELECT w.*, s.name as source_name, c.name as category_name
            FROM words w
            LEFT JOIN sources s ON w.source_id = s.id
            LEFT JOIN categories c ON w.category_id = c.id
        """

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY w.word"

        return query, params

    def search(self, filters: Dict[str, Any]) -> List[Dict]:
        """חיפוש לפי סינונים"""
        query, params = self.build_query(filters)
        cursor = self.db.conn.execute(query, params)

        columns = [description[0] for description in cursor.description]
        results = []

        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            # פענוח JSON
            if result.get('shva_types'):
                result['shva_types'] = json.loads(result['shva_types'])
            if result.get('nikud_marks'):
                result['nikud_marks'] = json.loads(result['nikud_marks'])
            if result.get('special_cases'):
                result['special_cases'] = json.loads(result['special_cases'])
            results.append(result)

        return results

    def apply_nikud_rule(self, rule_id: int) -> List[Dict]:
        """הפעלת כלל ניקוד מהטבלה"""
        cursor = self.db.conn.execute(
            "SELECT * FROM nikud_rules WHERE id = ?", (rule_id,)
        )
        rule = cursor.fetchone()

        if not rule:
            return []

        filters = {}

        # המרת הכלל לסינונים
        category = rule[1]  # category
        filter_type = rule[2]  # filter

        if category == "מסתיים ב":
            # צריך לבדוק סיומת
            # TODO: להוסיף תמיכה בסיומות מורכבות
            pass
        elif category == "מכיל":
            # בדיקת הכלה של ניקוד
            if filter_type == "שווא":
                filters['has_shva'] = True
            # TODO: להוסיף ניקודים נוספים
        elif category == "לא מכיל":
            # בדיקת אי-הכלה
            if filter_type == "שווא":
                filters['has_shva'] = False
        elif category == "פתוח/סגור":
            if filter_type == "סגורה":
                filters['syllable_type'] = "סגורה"

        return self.search(filters)

    def search_by_complex_rules(self, rules: List[Dict[str, str]]) -> List[Dict]:
        """חיפוש לפי שילוב של כללים מורכבים"""
        results = None

        for rule in rules:
            filters = {}

            # המרת כלל לסינון
            if rule['type'] == 'ends_with':
                # צריך לממש חיפוש לפי סיומת
                temp_results = []
                all_words = self.search({})  # קבלת כל המילים
                for word_data in all_words:
                    if self.analyzer.check_ends_with(word_data['word'], rule['value']):
                        temp_results.append(word_data)

            elif rule['type'] == 'contains':
                # חיפוש לפי הכלה
                temp_results = []
                all_words = self.search({})
                for word_data in all_words:
                    if self.analyzer.check_contains(word_data['word'], rule['value']):
                        temp_results.append(word_data)

            elif rule['type'] == 'syllable':
                filters['syllable_type'] = rule['value']
                temp_results = self.search(filters)

            elif rule['type'] == 'shva':
                if rule['value'] == 'יש':
                    filters['has_shva'] = True
                elif rule['value'] == 'אין':
                    filters['has_shva'] = False
                else:
                    filters['shva_type'] = rule['value']
                temp_results = self.search(filters)

            else:
                temp_results = self.search(filters)

            # שילוב תוצאות
            if results is None:
                results = temp_results
            else:
                # AND logic - רק מילים שמופיעות בשני הסטים
                if rule.get('operator') == 'AND' or not rule.get('operator'):
                    result_words = {r['word'] for r in temp_results}
                    results = [r for r in results if r['word'] in result_words]
                # OR logic - איחוד הסטים
                elif rule.get('operator') == 'OR':
                    existing_words = {r['word'] for r in results}
                    for r in temp_results:
                        if r['word'] not in existing_words:
                            results.append(r)

        return results if results else []

    def get_statistics(self) -> Dict:
        """קבלת סטטיסטיקות על המסד"""
        stats = {}

        # סך הכל מילים
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM words")
        stats['total_words'] = cursor.fetchone()[0]

        # סך הכל מילים ייחודיות
        cursor = self.db.conn.execute("SELECT COUNT(DISTINCT word) FROM words")
        stats['unique_words'] = cursor.fetchone()[0]

        # התפלגות סוגי הברות
        cursor = self.db.conn.execute("""
            SELECT syllable_type, COUNT(*) as count
            FROM words
            GROUP BY syllable_type
        """)
        stats['syllable_distribution'] = dict(cursor.fetchall())

        # מילים עם שווא
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM words WHERE has_shva = 1")
        stats['words_with_shva'] = cursor.fetchone()[0]

        # מילים עם דגש
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM words WHERE has_dagesh = 1")
        stats['words_with_dagesh'] = cursor.fetchone()[0]

        # מספר מקורות
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM sources")
        stats['total_sources'] = cursor.fetchone()[0]

        # מספר קטגוריות
        cursor = self.db.conn.execute("SELECT COUNT(*) FROM categories")
        stats['total_categories'] = cursor.fetchone()[0]

        return stats


# בדיקות בסיסיות
if __name__ == "__main__":
    # יצירת מופעים
    db = DatabaseManager("test_nikud.db")
    analyzer = NikudAnalyzer()
    engine = SearchEngine(db, analyzer)

    # טעינת טקסט לדוגמה
    sample_text = """
    בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ.
    וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ וְחֹשֶׁךְ עַל פְּנֵי תְהוֹם.
    וְרוּחַ אֱלֹהִים מְרַחֶפֶת עַל פְּנֵי הַמָּיִם.
    """

    print("טוען טקסט לדוגמה...")
    source_id = engine.load_text(sample_text, "בראשית פרק א", "תנ\"ך")

    # חיפושים לדוגמה
    print("\n=== חיפוש מילים עם שווא ===")
    results = engine.search({'has_shva': True})
    for r in results[:5]:
        print(f"  {r['word']} - {r['shva_types']}")

    print("\n=== חיפוש הברות פתוחות ===")
    results = engine.search({'syllable_type': 'פתוחה'})
    for r in results[:5]:
        print(f"  {r['word']}")

    print("\n=== סטטיסטיקות ===")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    db.close()