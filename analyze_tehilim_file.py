"""
ניתוח קובץ מילים מתהילים
Analyze Tehilim Words File
"""

import pandas as pd
import json

# קריאת הקובץ
file_path = r'C:\Users\שלום\Downloads\ניקוד\מילים מתהילים.xlsx'

try:
    # קריאת כל הגיליונות
    xl_file = pd.ExcelFile(file_path)
    print(f"=== גיליונות בקובץ ===")
    print(f"מספר גיליונות: {len(xl_file.sheet_names)}")
    print(f"שמות הגיליונות: {xl_file.sheet_names}")
    print()

    # קריאת כל גיליון
    for sheet_name in xl_file.sheet_names[:3]:  # רק 3 הראשונים לדוגמה
        print(f"\n=== גיליון: {sheet_name} ===")
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        print(f"מספר שורות: {len(df)}")
        print(f"מספר עמודות: {len(df.columns)}")
        print(f"שמות עמודות: {list(df.columns)}")

        # הצגת דוגמאות
        print(f"\n10 השורות הראשונות:")
        print(df.head(10).to_string())

        # בדיקה אם יש עמודת מילים
        word_columns = [col for col in df.columns if 'מיל' in str(col) or 'word' in str(col).lower()]
        if word_columns:
            print(f"\nעמודות מילים שנמצאו: {word_columns}")
            for col in word_columns:
                print(f"\nדוגמאות מעמודה '{col}':")
                words = df[col].dropna().head(10)
                for i, word in enumerate(words, 1):
                    print(f"  {i}. {word}")

        # ניתוח סוגי נתונים
        print(f"\n=== סוגי נתונים ===")
        print(df.dtypes)

        # בדיקת ערכים ריקים
        print(f"\n=== ערכים ריקים ===")
        print(df.isnull().sum())

        print("\n" + "="*50)

    # סיכום
    print("\n=== סיכום ===")
    print(f"הקובץ מכיל {len(xl_file.sheet_names)} גיליונות")

    # שמירת מידע על המבנה
    file_structure = {
        'sheets': xl_file.sheet_names,
        'structure': {}
    }

    for sheet_name in xl_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        file_structure['structure'][sheet_name] = {
            'rows': len(df),
            'columns': list(df.columns),
            'has_words': any('מיל' in str(col) for col in df.columns)
        }

    with open('tehilim_file_structure.json', 'w', encoding='utf-8') as f:
        json.dump(file_structure, f, ensure_ascii=False, indent=2)

    print("מבנה הקובץ נשמר ב-tehilim_file_structure.json")

except Exception as e:
    print(f"שגיאה בקריאת הקובץ: {e}")
    import traceback
    traceback.print_exc()