"""
מודול לניתוח ניקוד בטקסט עברי
Nikud Analyzer Module for Hebrew Text
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum

# הגדרת קבועים לסימני הניקוד
class NikudMarks:
    """סימני ניקוד בעברית"""
    # ניקודים בסיסיים
    SHVA = '\u05B0'  # שווא
    HATAF_SEGOL = '\u05B1'  # חטף סגול
    HATAF_PATAH = '\u05B2'  # חטף פתח
    HATAF_KAMATZ = '\u05B3'  # חטף קמץ
    HIRIQ = '\u05B4'  # חיריק
    TZERE = '\u05B5'  # צירה
    SEGOL = '\u05B6'  # סגול
    PATAH = '\u05B7'  # פתח
    KAMATZ = '\u05B8'  # קמץ
    HOLAM = '\u05B9'  # חולם
    HOLAM_MALE = '\u05BA'  # חולם מלא (ואו חולם)
    KUBUTZ = '\u05BB'  # קובוץ
    DAGESH = '\u05BC'  # דגש/מפיק/שורוק
    METEG = '\u05BD'  # מתג
    RAFE = '\u05BF'  # רפה
    SHIN_DOT = '\u05C1'  # שין ימנית
    SIN_DOT = '\u05C2'  # שין שמאלית

    # קבוצות ניקוד
    ALL_NIKUD = {SHVA, HATAF_SEGOL, HATAF_PATAH, HATAF_KAMATZ,
                 HIRIQ, TZERE, SEGOL, PATAH, KAMATZ, HOLAM,
                 HOLAM_MALE, KUBUTZ, DAGESH, METEG, RAFE,
                 SHIN_DOT, SIN_DOT}

    VOWELS = {HIRIQ, TZERE, SEGOL, PATAH, KAMATZ, HOLAM, HOLAM_MALE, KUBUTZ}
    HATAF_VOWELS = {HATAF_SEGOL, HATAF_PATAH, HATAF_KAMATZ}

    # אותיות עבריות
    HEBREW_LETTERS = set('אבגדהוזחטיכךלמםנןסעפףצץקרשת')
    SOFIT_LETTERS = set('ךםןףץ')  # אותיות סופיות
    GUTTURALS = set('אהחער')  # אותיות גרוניות

class SyllableType(Enum):
    """סוג הברה"""
    OPEN = "פתוחה"
    CLOSED = "סגורה"
    UNKNOWN = "לא ידוע"

class ShvaType(Enum):
    """סוג שווא"""
    NA = "נע"
    NAH = "נח"
    NONE = "אין"
    DOUBLE_NA = "שני שווא נע"
    DOUBLE_NAH = "שני שווא נח"
    NA_AND_NAH = "נע ונח"

@dataclass
class WordAnalysis:
    """תוצאת ניתוח מילה"""
    word: str
    word_plain: str  # ללא ניקוד
    nikud_pattern: str
    syllable_type: SyllableType
    has_shva: bool
    shva_types: List[ShvaType]
    nikud_marks: Set[str]
    has_dagesh: bool
    has_open_syllable: bool
    has_closed_syllable: bool
    special_cases: List[str]  # מקרים מיוחדים

class NikudAnalyzer:
    """מנתח ניקוד לטקסט עברי"""

    def __init__(self):
        self.marks = NikudMarks()

    def remove_nikud(self, text: str) -> str:
        """הסרת ניקוד מטקסט"""
        result = ""
        for char in text:
            if char not in self.marks.ALL_NIKUD:
                result += char
        return result

    def extract_nikud_pattern(self, word: str) -> str:
        """חילוץ תבנית הניקוד מהמילה"""
        pattern = []
        for i, char in enumerate(word):
            if char in self.marks.HEBREW_LETTERS:
                pattern.append('ל')  # לציון אות
            elif char in self.marks.ALL_NIKUD:
                if char == self.marks.SHVA:
                    pattern.append('ש')  # שווא
                elif char == self.marks.DAGESH:
                    pattern.append('ד')  # דגש
                elif char in self.marks.VOWELS:
                    pattern.append('ת')  # תנועה
                elif char in self.marks.HATAF_VOWELS:
                    pattern.append('ח')  # חטף
                else:
                    pattern.append('נ')  # ניקוד אחר
        return ''.join(pattern)

    def check_ends_with(self, word: str, pattern: str) -> bool:
        """בדיקה אם המילה מסתיימת בתבנית מסוימת"""
        word = word.strip()
        if not word:
            return False

        if pattern == "א" or pattern == "ה" or pattern == "ע":
            return word[-1] == pattern

        elif pattern == "ה דגושה":
            if len(word) >= 2 and word[-1] == 'ה':
                # בדיקה אם יש דגש באות האחרונה
                for i in range(len(word)-1, max(0, len(word)-3), -1):
                    if word[i] == self.marks.DAGESH:
                        return True
            return False

        elif pattern == "קמץ":
            for i in range(len(word)-1, max(0, len(word)-3), -1):
                if word[i] == self.marks.KAMATZ:
                    return True
            return False

        elif pattern == "צירה י":
            if len(word) >= 2 and word[-1] == 'י':
                for i in range(len(word)-2, max(0, len(word)-4), -1):
                    if word[i] == self.marks.TZERE:
                        return True
            return False

        elif pattern == "חיריק י":
            if len(word) >= 2 and word[-1] == 'י':
                for i in range(len(word)-2, max(0, len(word)-4), -1):
                    if word[i] == self.marks.HIRIQ:
                        return True
            return False

        elif pattern == "מלאופום":
            # חולם מלא (ואו עם חולם)
            if len(word) >= 2 and word[-1] == 'ו':
                for i in range(len(word)-2, max(0, len(word)-4), -1):
                    if word[i] == self.marks.HOLAM or word[i] == self.marks.HOLAM_MALE:
                        return True
            return False

        elif pattern == "חולם":
            for i in range(len(word)-1, max(0, len(word)-3), -1):
                if word[i] == self.marks.HOLAM or word[i] == self.marks.HOLAM_MALE:
                    return True
            return False

        elif pattern == "ח ופתח":
            # פתח גנובה
            if len(word) >= 2 and word[-1] == 'ח':
                for i in range(len(word)-2, max(0, len(word)-4), -1):
                    if word[i] == self.marks.PATAH:
                        return True
            return False

        elif pattern == "שווא אות שווא":
            # שני שוואים בסוף מילה
            if len(word) >= 4:
                shva_count = 0
                for i in range(len(word)-1, max(0, len(word)-5), -1):
                    if word[i] == self.marks.SHVA:
                        shva_count += 1
                return shva_count >= 2
            return False

        return False

    def check_contains(self, word: str, nikud_type: str) -> bool:
        """בדיקה אם המילה מכילה ניקוד מסוים"""
        if nikud_type == "שווא":
            return self.marks.SHVA in word
        elif nikud_type == "קמץ":
            return self.marks.KAMATZ in word or self.marks.HATAF_KAMATZ in word
        elif nikud_type == "חטף קמץ":
            return self.marks.HATAF_KAMATZ in word
        elif nikud_type == "פתח":
            return self.marks.PATAH in word or self.marks.HATAF_PATAH in word
        elif nikud_type == "חטף פתח":
            return self.marks.HATAF_PATAH in word
        elif nikud_type == "צירה":
            return self.marks.TZERE in word
        elif nikud_type == "סגול":
            return self.marks.SEGOL in word or self.marks.HATAF_SEGOL in word
        elif nikud_type == "חטף סגול":
            return self.marks.HATAF_SEGOL in word
        elif nikud_type == "חיריק":
            return self.marks.HIRIQ in word
        elif nikud_type == "שורוק":
            # ואו עם דגש (שורוק)
            for i in range(len(word)-1):
                if word[i] == 'ו' and i+1 < len(word) and word[i+1] == self.marks.DAGESH:
                    return True
            return False
        elif nikud_type == "מלאופום" or nikud_type == "חולם":
            return self.marks.HOLAM in word or self.marks.HOLAM_MALE in word
        return False

    def analyze_shva(self, word: str) -> List[ShvaType]:
        """ניתוח סוגי שווא במילה"""
        shva_types = []
        word_clean = self.remove_nikud(word)

        if self.marks.SHVA not in word:
            return [ShvaType.NONE]

        # מציאת כל המופעים של שווא
        shva_positions = []
        for i, char in enumerate(word):
            if char == self.marks.SHVA:
                shva_positions.append(i)

        for pos in shva_positions:
            # שווא בתחילת מילה - שווא נע
            if pos <= 2:  # בתחילת המילה (כולל דגש אפשרי)
                shva_types.append(ShvaType.NA)
            # שווא אחרי תנועה גדולה - שווא נח
            elif pos > 0 and word[pos-1] in self.marks.VOWELS:
                shva_types.append(ShvaType.NAH)
            # שני שוואים ברצף
            elif pos > 0 and word[pos-1] == self.marks.SHVA:
                shva_types.append(ShvaType.DOUBLE_NAH)
            else:
                # ברירת מחדל - שווא נח
                shva_types.append(ShvaType.NAH)

        # בדיקת מקרים מיוחדים
        if len(shva_positions) >= 2:
            # בדיקה אם יש שווא נע ונח
            if ShvaType.NA in shva_types and ShvaType.NAH in shva_types:
                shva_types = [ShvaType.NA_AND_NAH]
            # בדיקה אם יש שני שווא נח
            elif shva_types.count(ShvaType.NAH) >= 2:
                shva_types = [ShvaType.DOUBLE_NAH]

        return shva_types if shva_types else [ShvaType.NONE]

    def check_syllable_type(self, word: str) -> SyllableType:
        """קביעת סוג ההברה של המילה"""
        # כללים לקביעת הברה פתוחה
        open_endings = ["א", "ה", "ע", "קמץ", "צירה י", "חיריק י", "מלאופום", "חולם"]
        for ending in open_endings:
            if self.check_ends_with(word, ending):
                return SyllableType.OPEN

        # בדיקת הברה סגורה - אם לא מסתיימת בתנועה או אות פתוחה
        if word and word[-1] in self.marks.HEBREW_LETTERS and word[-1] not in 'אהע':
            # בדיקה שאין תנועה אחרי האות האחרונה
            has_final_vowel = False
            for i in range(len(word)-1, max(0, len(word)-3), -1):
                if word[i] in self.marks.VOWELS:
                    has_final_vowel = True
                    break
            if not has_final_vowel:
                return SyllableType.CLOSED

        return SyllableType.UNKNOWN

    def check_kamatz_katan(self, word: str) -> bool:
        """בדיקת קמץ קטן/המשתנה"""
        # קמץ + ה דגושה
        if self.check_ends_with(word, "ה דגושה"):
            for i in range(len(word)-3, max(0, len(word)-5), -1):
                if word[i] == self.marks.KAMATZ:
                    return True

        # קמץ + אות + שווא
        for i in range(len(word)-3):
            if (word[i] == self.marks.KAMATZ and
                i+1 < len(word) and word[i+1] in self.marks.HEBREW_LETTERS and
                i+2 < len(word) and word[i+2] == self.marks.SHVA):
                return True

        # קמץ + שתי אותיות + שווא
        for i in range(len(word)-4):
            if (word[i] == self.marks.KAMATZ and
                i+1 < len(word) and word[i+1] in self.marks.HEBREW_LETTERS and
                i+2 < len(word) and word[i+2] in self.marks.HEBREW_LETTERS and
                i+3 < len(word) and word[i+3] == self.marks.SHVA):
                return True

        # קמץ + י
        for i in range(len(word)-1):
            if word[i] == self.marks.KAMATZ and i+1 < len(word) and word[i+1] == 'י':
                return True

        return False

    def analyze_word(self, word: str) -> WordAnalysis:
        """ניתוח מלא של מילה"""
        word = word.strip()
        word_plain = self.remove_nikud(word)
        nikud_pattern = self.extract_nikud_pattern(word)

        # איסוף סימני ניקוד
        nikud_marks = set()
        for char in word:
            if char in self.marks.ALL_NIKUD:
                nikud_marks.add(char)

        # ניתוחים נוספים
        has_shva = self.marks.SHVA in word
        shva_types = self.analyze_shva(word)
        syllable_type = self.check_syllable_type(word)
        has_dagesh = self.marks.DAGESH in word

        # בדיקת מקרים מיוחדים
        special_cases = []
        if self.check_kamatz_katan(word):
            special_cases.append("קמץ קטן")
        if self.check_ends_with(word, "ח ופתח"):
            special_cases.append("פתח גנובה")
        if len([c for c in word if c == self.marks.SHVA]) >= 2:
            special_cases.append("שני שוואים")

        return WordAnalysis(
            word=word,
            word_plain=word_plain,
            nikud_pattern=nikud_pattern,
            syllable_type=syllable_type,
            has_shva=has_shva,
            shva_types=shva_types,
            nikud_marks=nikud_marks,
            has_dagesh=has_dagesh,
            has_open_syllable=(syllable_type == SyllableType.OPEN),
            has_closed_syllable=(syllable_type == SyllableType.CLOSED),
            special_cases=special_cases
        )

    def analyze_text(self, text: str) -> List[WordAnalysis]:
        """ניתוח טקסט שלם"""
        # פיצול הטקסט למילים - תחילה פיצול לפי רווחים ותווי פיסוק
        import string

        # הסרת תווי פיסוק מיותרים אך שמירה על ניקוד
        words = []

        # פיצול לפי רווחים, פסיקים, נקודות וכו'
        separators = ' \t\n\r,.;:!?()[]{}"\'\u05C3\u05BE\u2013\u2014\u2022\u00B7\u05F4\u05F3'
        current_word = []

        for char in text:
            if char in separators:
                if current_word:
                    word = ''.join(current_word)
                    # בדיקה שיש לפחות אות עברית אחת (לא רק ניקוד)
                    if any(c in self.marks.HEBREW_LETTERS for c in word):
                        words.append(word)
                    current_word = []
            else:
                # שמירה על אותיות עבריות וניקוד בלבד
                if char in self.marks.HEBREW_LETTERS or char in self.marks.ALL_NIKUD:
                    current_word.append(char)

        # אל תשכח את המילה האחרונה
        if current_word:
            word = ''.join(current_word)
            if any(c in self.marks.HEBREW_LETTERS for c in word):
                words.append(word)

        # ניתוח המילים
        results = []
        for word in words:
            if word and len(word) > 1:  # רק מילים עם יותר מאות אחת
                analysis = self.analyze_word(word)
                results.append(analysis)

        return results


# בדיקות בסיסיות
if __name__ == "__main__":
    analyzer = NikudAnalyzer()

    # דוגמאות לבדיקה
    test_words = [
        "שָׁלוֹם",
        "יְלָדִים",
        "מִשְׁפָּחָה",
        "תּוֹרָה",
        "יִשְׂרָאֵל",
        "בְּרֵאשִׁית",
        "הַמֶּלֶךְ",
        "וַיֹּאמֶר"
    ]

    print("=== בדיקת ניתוח ניקוד ===\n")
    for word in test_words:
        analysis = analyzer.analyze_word(word)
        print(f"מילה: {word}")
        print(f"  ללא ניקוד: {analysis.word_plain}")
        print(f"  תבנית: {analysis.nikud_pattern}")
        print(f"  סוג הברה: {analysis.syllable_type.value}")
        print(f"  יש שווא: {analysis.has_shva}")
        if analysis.has_shva:
            print(f"  סוגי שווא: {[s.value for s in analysis.shva_types]}")
        print(f"  סימני ניקוד: {len(analysis.nikud_marks)}")
        if analysis.special_cases:
            print(f"  מקרים מיוחדים: {', '.join(analysis.special_cases)}")
        print()