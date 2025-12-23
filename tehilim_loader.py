"""
טוען מילים מתהילים למסד הנתונים
Tehilim Words Loader for Database
"""

import pandas as pd
from typing import List, Dict, Optional
import json
from nikud_analyzer import NikudAnalyzer
from search_engine import DatabaseManager, SearchEngine
from progress_dialog import ProgressDialog


class TehilimLoader:
    """טוען מילים מתהילים עם ניתוח ניקוד למסד נתונים"""

    def __init__(self, db_manager: DatabaseManager, analyzer: NikudAnalyzer):
        self.db = db_manager
        self.analyzer = analyzer
        self.engine = SearchEngine(db_manager, analyzer)

    def load_tehilim_file(self, file_path: str, progress: Optional[ProgressDialog] = None) -> Dict:
        """טעינת קובץ תהילים למסד נתונים"""
        results = {
            'total_words': 0,
            'loaded_words': 0,
            'errors': 0,
            'skipped': 0,
            'new_rules': []
        }

        try:
            # קריאת הקובץ
            df = pd.read_excel(file_path, sheet_name='סימן מילה')

            # סינון מילים ריקות
            df = df[df['מילים'].notna()]
            total_words = len(df)
            results['total_words'] = total_words

            if progress:
                progress.set_max(total_words + 10)
                progress.update(5, "מכין את מסד הנתונים...")

            # יצירת מקור במסד נתונים
            source_id = self.db.add_source(
                "ספר תהילים - מילים מנותחות",
                f"מילים מתהילים עם ניתוח ניקוד ({total_words} מילים)",
                file_path
            )

            # הוספת קטגוריה
            category_id = self.db.add_category("תהילים", "מילים מספר תהילים")

            # עיבוד המילים
            for index, row in df.iterrows():
                if progress and progress.is_cancelled:
                    break

                try:
                    word = str(row['מילים']).strip()

                    if not word or word == 'nan':
                        results['skipped'] += 1
                        continue

                    if progress:
                        current = index + 10
                        progress.update(
                            current,
                            f"מעבד מילה {index + 1} מתוך {total_words}",
                            word
                        )

                    # ניתוח המילה
                    analysis = self.analyzer.analyze_word(word)

                    # הוספת מידע נוסף מהקובץ
                    extra_info = self.extract_extra_info(row)

                    # בניית הקשר
                    context = self.build_context(row)

                    # שמירה במסד
                    self.db.add_word(
                        analysis=analysis,
                        source_id=source_id,
                        position=index,
                        context=context,
                        category_id=category_id
                    )

                    results['loaded_words'] += 1

                    # למידת כללים חדשים
                    new_rules = self.learn_rules_from_row(row, analysis)
                    if new_rules:
                        results['new_rules'].extend(new_rules)

                except Exception as e:
                    print(f"שגיאה במילה {index}: {word} - {e}")
                    results['errors'] += 1

            # שמירת השינויים
            self.db.conn.commit()

            if progress:
                progress.update(
                    total_words + 10,
                    "הטעינה הושלמה!",
                    f"נטענו {results['loaded_words']} מילים"
                )

        except Exception as e:
            self.db.conn.rollback()
            raise e

        return results

    def extract_extra_info(self, row) -> Dict:
        """חילוץ מידע נוסף מהשורה"""
        info = {}

        # מידע על הברות
        if 'סוג הברה' in row and pd.notna(row['סוג הברה']):
            info['syllable_type'] = row['סוג הברה']

        # מידע על שווא
        if 'שווא' in row and pd.notna(row['שווא']):
            info['shva_info'] = row['שווא']

        # מידע על דגש
        if 'דגש' in row and pd.notna(row['דגש']):
            info['dagesh_info'] = row['דגש']

        # סוג מילה
        if 'סוג' in row and pd.notna(row['סוג']):
            info['word_type'] = row['סוג']

        # פרק ופסוק
        if 'פרק' in row and pd.notna(row['פרק']):
            info['chapter'] = row['פרק']

        if 'פסוק' in row and pd.notna(row['פסוק']):
            info['verse'] = row['פסוק']

        return info

    def build_context(self, row) -> str:
        """בניית הקשר למילה"""
        context_parts = []

        # מיקום בתהילים
        if 'פרק' in row and pd.notna(row['פרק']):
            context_parts.append(f"פרק {row['פרק']}")

        if 'פסוק' in row and pd.notna(row['פסוק']):
            context_parts.append(f"פסוק {row['פסוק']}")

        # סוג ההברה
        if 'סוג הברה' in row and pd.notna(row['סוג הברה']):
            context_parts.append(f"הברה {row['סוג הברה']}")

        # מידע נוסף
        if 'הערות' in row and pd.notna(row['הערות']):
            context_parts.append(str(row['הערות']))

        return " | ".join(context_parts) if context_parts else ""

    def learn_rules_from_row(self, row, analysis) -> List[Dict]:
        """למידת כללים חדשים מהשורה"""
        new_rules = []

        # כלל על סיומת והברה פתוחה
        if 'הברה א' in row and row['הברה א'] == 'פ':  # פתוחה
            if analysis.word.endswith('א') or analysis.word.endswith('ה'):
                new_rules.append({
                    'category': 'מסתיים ב',
                    'filter': analysis.word[-1],
                    'result': 'פתוחה',
                    'source': 'תהילים'
                })

        # כלל על שווא נע ונח
        if 'שווא נע' in row and row['שווא נע'] == 1:
            if analysis.has_shva:
                new_rules.append({
                    'category': 'שווא',
                    'filter': 'יש',
                    'result': 'שווא נע',
                    'notes': f"דוגמה: {analysis.word}"
                })

        # כלל על דגש
        if 'דגש חזק' in row and row['דגש חזק'] == 1:
            if analysis.has_dagesh:
                new_rules.append({
                    'category': 'מכיל',
                    'filter': 'דגש',
                    'result': 'דגש חזק',
                    'notes': f"דוגמה: {analysis.word}"
                })

        return new_rules

    def load_additional_rules(self, file_path: str) -> int:
        """טעינת כללי ניקוד נוספים מהקובץ"""
        try:
            # קריאת גיליון הכללים
            df_rules = pd.read_excel(file_path, sheet_name='כללי ניק')

            count = 0
            for _, row in df_rules.iterrows():
                if pd.notna(row.get('סוג כלל')) and pd.notna(row.get('תוצאה')):
                    self.db.conn.execute("""
                        INSERT OR IGNORE INTO nikud_rules
                        (category, filter, result, notes)
                        VALUES (?, ?, ?, ?)
                    """, (
                        row.get('סוג כלל'),
                        row.get('תנאי', ''),
                        row.get('תוצאה'),
                        f"מקור: תהילים - {row.get('הערות', '')}"
                    ))
                    count += 1

            self.db.conn.commit()
            return count

        except Exception as e:
            print(f"לא נמצא גיליון כללים או שגיאה: {e}")
            return 0


def load_tehilim_to_db():
    """פונקציה ראשית לטעינת תהילים"""
    db = DatabaseManager("nikud_database.db")
    analyzer = NikudAnalyzer()
    loader = TehilimLoader(db, analyzer)

    file_path = r'C:\Users\שלום\Downloads\ניקוד\מילים מתהילים.xlsx'

    print("טוען מילים מתהילים...")
    results = loader.load_tehilim_file(file_path)

    print(f"\n=== סיכום טעינה ===")
    print(f"סך הכל מילים: {results['total_words']}")
    print(f"נטענו בהצלחה: {results['loaded_words']}")
    print(f"דילגנו על: {results['skipped']}")
    print(f"שגיאות: {results['errors']}")

    if results['new_rules']:
        print(f"\nנלמדו {len(results['new_rules'])} כללים חדשים")

    # טעינת כללים נוספים
    rules_count = loader.load_additional_rules(file_path)
    if rules_count > 0:
        print(f"נטענו {rules_count} כללי ניקוד")

    db.close()
    print("\nהטעינה הושלמה!")


if __name__ == "__main__":
    load_tehilim_to_db()