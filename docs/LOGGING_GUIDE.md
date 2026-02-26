# מדריך שימוש בלוגינג

## סקירה כללית

הפרויקט משתמש במערכת לוגינג מקצועית של Python (`logging`). הלוגינג מאפשר לך לעקוב אחרי מה שקורה באפליקציה, לזהות בעיות ולנתח ביצועים.

## הגדרת לוגינג

הלוגינג מוגדר בקובץ `app.py` בתחילת התוכנית:

```python
from utils.logging_config import setup_logging
import logging

# הגדרת לוגינג ברמת INFO (ברירת מחדל)
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)
```

### רמות לוגינג

הרמות הזמינות (מהנמוכה לגבוהה):
- **DEBUG** - מידע מפורט לניפוי באגים
- **INFO** - מידע כללי על פעולות רגילות
- **WARNING** - אזהרות על בעיות פוטנציאליות
- **ERROR** - שגיאות שצריך לטפל בהן
- **CRITICAL** - שגיאות קריטיות שמונעות מהאפליקציה לעבוד

## שימוש בלוגינג בקבצים שלך

### 1. ייבוא והגדרת logger

בכל קובץ שבו תרצה להשתמש בלוגינג:

```python
import logging

logger = logging.getLogger(__name__)
```

**חשוב:** השתמש ב-`__name__` כדי שהלוגים יציגו את שם המודול המדויק.

### 2. כתיבת לוגים

#### DEBUG - מידע מפורט
```python
logger.debug("מתחיל עיבוד טקסט: %s", text)
logger.debug(f"מספר בקשות API: {len(requests)}")
```

#### INFO - מידע כללי
```python
logger.info("טקסט עובד בהצלחה")
logger.info("אודיו נוצר: %s", audio_path)
```

#### WARNING - אזהרות
```python
logger.warning("טקסט ארוך מדי, קוצץ ל-%d תווים", MAX_LENGTH)
logger.warning("לא הצלחתי לטעון העדפות, משתמש בברירת מחדל")
```

#### ERROR - שגיאות
```python
logger.error("שגיאה ב-API: %s", str(e))
logger.error("לא הצלחתי ליצור אודיו")
```

#### CRITICAL - שגיאות קריטיות
```python
logger.critical("מפתח API חסר! האפליקציה לא תעבוד")
```

### 3. לוגינג עם exception

כשאתה בתוך `except` block, השתמש ב-`logger.exception()` כדי לרשום גם את ה-traceback:

```python
try:
    result = some_function()
except Exception as e:
    logger.exception("שגיאה בלתי צפויה בעיבוד טקסט")
    # זה ירשום גם את ה-traceback המלא
```

או:

```python
try:
    result = some_function()
except Exception as e:
    logger.error("שגיאה בעיבוד טקסט: %s", str(e), exc_info=True)
    # exc_info=True מוסיף את ה-traceback
```

## דוגמאות מהפרויקט

### דוגמה 1: לוגינג שגיאות
```python
# api/gemini_tts.py
try:
    response = client.models.generate_content(...)
except Exception as e:
    logger.error(f"TTS generation failed: {e}")
    raise RuntimeError(f"Failed to generate audio: {e}") from e
```

### דוגמה 2: לוגינג אזהרות
```python
# api/dicta_nakdan.py
if len(text) > MAX_TEXT_LENGTH:
    logger.warning(f"Text too long ({len(text)} chars), truncating to {MAX_TEXT_LENGTH}")
    text = text[:MAX_TEXT_LENGTH]
```

### דוגמה 3: לוגינג בעת טעינת קבצים
```python
# utils/prefs.py
try:
    with open(PREFS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except (json.JSONDecodeError, IOError, OSError) as e:
    logger.warning(f"Failed to load preferences: {e}")
    # ממשיך עם ברירת מחדל
```

## הגדרת לוגינג לקובץ

אם תרצה לשמור את הלוגים גם לקובץ:

```python
from utils.logging_config import setup_logging

# שמירה לקובץ logs/app.log
setup_logging(log_level="INFO", log_file="logs/app.log")
```

הקובץ ייווצר אוטומטית בתיקייה `logs/`.

## שינוי רמת לוגינג

### דרך 1: בקוד
```python
setup_logging(log_level="DEBUG")  # לראות הכל
setup_logging(log_level="WARNING")  # רק אזהרות ושגיאות
```

### דרך 2: משתנה סביבה
```python
import os
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level=log_level)
```

ואז הרץ:
```bash
LOG_LEVEL=DEBUG streamlit run app.py
```

## פורמט הלוגים

הפורמט הנוכחי:
```
2026-02-22 14:30:45 - api.gemini_tts - ERROR - TTS generation failed: ...
```

הפורמט כולל:
- תאריך ושעה
- שם המודול
- רמת הלוג
- ההודעה

## טיפים

1. **אל תשתמש ב-print()** - השתמש בלוגינג במקום
2. **השתמש ברמה הנכונה** - DEBUG לניפוי באגים, INFO לפעולות רגילות, ERROR לשגיאות
3. **הוסף context** - כלול מידע רלוונטי בלוג (משתנים, ערכים)
4. **לא יותר מדי** - אל תרשום כל דבר, רק מה שחשוב
5. **בייצור** - השתמש ב-INFO או WARNING, לא DEBUG

## דוגמה מלאה

```python
import logging
from utils.logging_config import setup_logging

# הגדרה
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

def process_text(text: str) -> str:
    logger.info("מתחיל עיבוד טקסט באורך %d תווים", len(text))
    
    if not text:
        logger.warning("קיבלתי טקסט ריק")
        return ""
    
    try:
        # עיבוד הטקסט
        result = text.upper()
        logger.debug("תוצאה: %s", result)  # רק ב-DEBUG mode
        logger.info("עיבוד הושלם בהצלחה")
        return result
        
    except Exception as e:
        logger.error("שגיאה בעיבוד טקסט: %s", str(e))
        logger.exception("פרטי השגיאה:")  # כולל traceback
        raise
```

## בדיקת הלוגים

כשאתה מריץ את האפליקציה, הלוגים יופיעו בקונסול (טרמינל) שבו הרצת את `streamlit run app.py`.

אם הגדרת שמירה לקובץ, תוכל לראות אותם גם שם:
```bash
tail -f logs/app.log  # לראות לוגים בזמן אמת
```
