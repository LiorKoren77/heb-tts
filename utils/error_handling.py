import re
import time
import logging
from typing import Optional

# Optional import to avoid tight coupling
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_wait_time_from_error(error_str: str, default_wait: int = 17) -> int:
    """
    Extracts the recommended wait time (retryDelay) from a Google API rate limit error.
    Adds a small buffer to ensure the next request succeeds.
    """
    if "429" not in error_str or "RESOURCE_EXHAUSTED" not in error_str:
        return 0
        
    wait_time = default_wait
    
    # Try to extract the retryDelay field
    match = re.search(r"retryDelay':\s*'(\d+)s'", error_str)
    if match:
        wait_time = int(match.group(1))
    else:
        # Try another common format
        match = re.search(r"retry in (\d+)(?:\.\d+)?s", error_str)
        if match:
            wait_time = int(match.group(1))
            
    # Add a 3-second buffer to be safe against server clock differences
    return wait_time + 3

def handle_rate_limit_error(error_str: str) -> bool:
    """
    Displays a countdown timer in Streamlit based on the wait time in the error.
    Returns True if it was a rate limit error and we handled it, False otherwise.
    
    Args:
        error_str: Error message string from the API
        
    Returns:
        True if rate limit error was handled, False otherwise
    """
    if "429" not in error_str or "RESOURCE_EXHAUSTED" not in error_str:
        return False
        
    if not STREAMLIT_AVAILABLE:
        wait_time = extract_wait_time_from_error(error_str)
        logger.warning(f"Rate limit exceeded. Wait {wait_time} seconds.")
        return True
        
    wait_time = extract_wait_time_from_error(error_str)
    
    timer_placeholder = st.empty()
    for i in range(wait_time, 0, -1):
        timer_placeholder.error(f"⏳ חריגה ממכסת הבקשות של Google. אנא המתן {i} שניות לפני לחיצה נוספת...")
        time.sleep(1)
        
    timer_placeholder.empty()
    # לא מרעננים! המשתמש יישאר עם הכפתור "הפוך לדיבור" כרגיל ויוכל ללחוץ עליו בעצמו
    return True
