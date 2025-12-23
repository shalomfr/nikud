import pandas as pd
import json

# קריאת קובץ האקסל
file_path = r'C:\Users\שלום\Downloads\ניקוד\רשימה לסינון.xlsx'
df = pd.read_excel(file_path)

# הצגת מידע על הקובץ
print("=== מבנה הקובץ ===")
print(f"מספר שורות: {len(df)}")
print(f"מספר עמודות: {len(df.columns)}")
print(f"\nשמות העמודות: {list(df.columns)}")

# הצגת 20 השורות הראשונות
print("\n=== 20 השורות הראשונות ===")
print(df.head(20).to_string())

# הצגת סוגי הנתונים
print("\n=== סוגי הנתונים בכל עמודה ===")
print(df.dtypes)

# בדיקה אם יש ערכים ריקים
print("\n=== ערכים ריקים בכל עמודה ===")
print(df.isnull().sum())

# שמירת הנתונים כ-JSON לצורך ניתוח
df_json = df.to_dict(orient='records')
with open(r'C:\Users\שלום\Downloads\ניקוד\nikud_rules.json', 'w', encoding='utf-8') as f:
    json.dump(df_json[:50], f, ensure_ascii=False, indent=2)

print("\n=== נשמר קובץ JSON עם 50 הרשומות הראשונות ===")