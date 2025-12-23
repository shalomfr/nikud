@echo off
echo ========================================
echo   מערכת ניתוח וחיפוש ניקוד
echo ========================================
echo.

REM בדיקה אם Python מותקן
python --version >nul 2>&1
if errorlevel 1 (
    echo שגיאה: Python לא מותקן במערכת
    echo אנא התקן Python 3.10 ומעלה
    pause
    exit /b 1
)

REM התקנת דרישות אם צריך
echo בודק והתקנת חבילות נדרשות...
pip install -q -r requirements.txt

REM הפעלת האפליקציה
echo.
echo מפעיל את המערכת...
python nikud_app.py

pause