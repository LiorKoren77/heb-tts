import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

# Validate API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)
logger = logging.getLogger(__name__)

# We use the fast flash model for text processing, not the TTS model.
LLM_PROCESSOR_MODEL = "gemini-2.5-flash"

def dynamic_preprocess(text: str) -> str:
    """
    Sends the text to Gemini to dynamically expand acronyms, 
    fix transliterated english words back to english, and prepare it for TTS.
    Returns the improved text.
    
    Args:
        text: Text to preprocess
        
    Returns:
        Preprocessed text, or original text if processing fails
    """
    if not text or not text.strip():
        return text
    
    # Limit text length to prevent API issues and costs
    MAX_TEXT_LENGTH = 5000
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning(f"Text too long ({len(text)} chars), truncating to {MAX_TEXT_LENGTH}")
        text = text[:MAX_TEXT_LENGTH]
        
    prompt = f"""
אתה מומחה ללשון העברית ולהכנת טקסטים להקראה (TTS).
קרא את הטקסט הבא והחזר אותו בדיוק כפי שהוא, אבל בצע עליו *רק* את השינויים הבאים כדי שהקריין יהגה אותו נכון:
1. פתח ראשי תיבות או צורות מקוצרות (למשל: 'דו"ח' ישתנה ל-'דוח', 'מנכ"ל' ישתנה ל-'מנכל', 'וכו'' ישתנה ל-'וכולי').
2. מילים לועזיות או טכנולוגיות שנכתבו בעברית (למשל 'ווטסאפ', 'אינטרנט', 'פייסבוק') - שנה אותן לאנגלית תקנית (WhatsApp, Internet, Facebook) כדי שהקריין יעבור להגות אותן במבטא אנגלי במקום בעברית שבורה.
3. אל תשנה, אל תסכם ואל תשכתב אף מילה עברית תקינה. אל תוסיף הקדמות או הערות משלך. החזר אך ורק את הטקסט המטופל.

הטקסט:
{text}
"""
    
    try:
        response = client.models.generate_content(
            model=LLM_PROCESSOR_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1, # Keep it deterministic
            )
        )
        if response.text:
            return response.text.strip()
        return text
    except Exception as e:
        logger.error(f"Error in dynamic LLM preprocessor: {e}")
        return text
