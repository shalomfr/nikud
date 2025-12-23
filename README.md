# מערכת ניתוח וחיפוש ניקוד - Web Application

מערכת מתקדמת לניתוח טקסטים עבריים עם ניקוד, חיפוש וסינון לפי כללי ניקוד מורכבים, וייצוא תוצאות לאקסל.

## ✨ תכונות עיקריות

- 📝 **טעינת טקסטים** - תמיכה בקבצי TXT, DOCX והזנה ישירה
- 🔍 **חיפוש מתקדם** - סינון לפי 46 כללי ניקוד מורכבים
- 📊 **ניתוח מעמיק** - זיהוי הברות, שווא, דגש ומקרים מיוחדים
- 📈 **סטטיסטיקות** - נתונים מלאים על המסד
- 📁 **ייצוא לאקסל** - עם עיצוב, פילטרים וטבלאות Pivot
- 🌐 **ממשק ווב מודרני** - עיצוב מותאם לעברית עם תמיכה ב-RTL

## 🛠️ טכנולוגיות

- **Backend**: FastAPI, SQLAlchemy, Python 3.11+
- **Database**: PostgreSQL (ייצור) / SQLite (פיתוח)
- **Frontend**: HTML, Tailwind CSS, Alpine.js
- **Deploy**: Docker, Render

## 🚀 התקנה מקומית

### דרישות מקדימות
- Python 3.11 ומעלה
- pip או pipenv

### שלבים

1. **שכפול הפרויקט**
```bash
git clone https://github.com/YOUR_USERNAME/nikud.git
cd nikud
```

2. **יצירת סביבה וירטואלית**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **התקנת תלויות**
```bash
pip install -r requirements.txt
```

4. **הגדרת משתני סביבה**
```bash
# העתק את קובץ הדוגמה
copy env.example .env
# ערוך את הקובץ לפי הצורך
```

5. **הפעלת השרת**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **פתח את הדפדפן**
```
http://localhost:8000
```

## 🌍 פריסה ל-Render

### שלב 1: העלאה ל-GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/nikud.git
git push -u origin main
```

### שלב 2: יצירת שירות ב-Render

1. היכנס ל-[Render Dashboard](https://dashboard.render.com/)
2. לחץ על **New > Blueprint**
3. חבר את ה-repository שלך
4. Render יזהה אוטומטית את `render.yaml`
5. לחץ **Apply**

### שלב 3: המתן לפריסה
- Render יבנה את ה-Docker image
- יקים מסד נתונים PostgreSQL
- יפרוס את האפליקציה

## 📁 מבנה הפרויקט

```
nikud/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── words.py         # Word search endpoints
│   │   ├── sources.py       # Text sources endpoints
│   │   └── analysis.py      # Analysis endpoints
│   ├── services/
│   │   ├── nikud_analyzer.py  # Nikud analysis engine
│   │   ├── search_engine.py   # Search functionality
│   │   └── excel_exporter.py  # Excel export
│   └── static/              # Static files
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Search page
│   ├── upload.html          # Upload page
│   └── stats.html           # Statistics page
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

## 🔌 API Endpoints

### חיפוש מילים
```
GET /api/words/search
Parameters:
  - word: מילה עם ניקוד
  - word_plain: מילה ללא ניקוד
  - syllable_type: סוג הברה (פתוחה/סגורה)
  - has_shva: יש שווא (true/false)
  - has_dagesh: יש דגש (true/false)
  - page: מספר עמוד
  - per_page: תוצאות לעמוד
```

### ייצוא לאקסל
```
GET /api/words/export
```

### טעינת טקסט
```
POST /api/sources/
Body: { name, content, category }
```

### העלאת קובץ
```
POST /api/sources/upload
Form: file, source_name, category
```

### סטטיסטיקות
```
GET /api/analysis/stats
```

## 📖 מדריך שימוש

### טעינת טקסט
1. עבור לעמוד **טעינה**
2. הזן טקסט עברי עם ניקוד או העלה קובץ
3. ציין שם מקור וקטגוריה
4. לחץ **טען**

### חיפוש וסינון
1. בעמוד הראשי, הזן פרמטרי חיפוש
2. סמן סינונים נוספים (שווא, דגש, וכו')
3. לחץ **חפש**
4. לחץ על שורה לצפייה בפרטים

### ייצוא
1. בצע חיפוש
2. לחץ **ייצא לאקסל**
3. הקובץ יורד אוטומטית

## 🤝 תרומה לפרויקט

תרומות מתקבלות בברכה! אנא:
1. Fork את הפרויקט
2. צור branch חדש
3. בצע את השינויים
4. פתח Pull Request

## 📄 רישיון

פותח לשימוש חופשי למטרות חינוך ומחקר.

---

פותח בשנת 2024 | גרסה 2.0 | FastAPI + Tailwind CSS
