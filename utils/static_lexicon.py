import json
import os
import logging

logger = logging.getLogger(__name__)

# Load the static lexicon once when the module is imported
LEXICON_PATH = os.path.join(os.path.dirname(__file__), "lexicon.json")
STATIC_LEXICON = {}
try:
    if os.path.exists(LEXICON_PATH):
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            STATIC_LEXICON = json.load(f)
except (json.JSONDecodeError, IOError, OSError) as e:
    logger.warning(f"Failed to load lexicon: {e}")


def load_lexicon_from_file() -> dict:
    """
    Loads the lexicon from the JSON file.
    
    Returns:
        Dictionary with lexicon entries, or empty dict if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(LEXICON_PATH):
            with open(LEXICON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {}
    except (json.JSONDecodeError, IOError, OSError) as e:
        logger.warning(f"Failed to load lexicon from file: {e}")
        return {}


def save_lexicon_to_file(lexicon: dict) -> bool:
    """
    Saves the lexicon dictionary to the JSON file.
    
    Args:
        lexicon: Dictionary with lexicon entries to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(LEXICON_PATH), exist_ok=True)
        
        with open(LEXICON_PATH, "w", encoding="utf-8") as f:
            json.dump(lexicon, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Lexicon saved successfully. {len(lexicon)} entries saved.")
        return True
    except (IOError, OSError) as e:
        logger.error(f"Failed to save lexicon to file: {e}")
        return False


def reload_lexicon():
    """
    Reloads the lexicon from the JSON file.
    Updates the STATIC_LEXICON global variable.
    """
    global STATIC_LEXICON
    STATIC_LEXICON = load_lexicon_from_file()
    logger.info(f"Lexicon reloaded successfully. {len(STATIC_LEXICON)} entries loaded.")

def apply_static_lexicon(text: str) -> str:
    """
    Applies simple word-for-word string replacements based on a static dictionary.
    """
    if not STATIC_LEXICON:
        return text
        
    processed = text
    for old_word, new_word in STATIC_LEXICON.items():
        # Using word boundaries to avoid replacing parts of a larger word
        # Note: \b in python regex doesn't always work perfectly with Hebrew 
        # punctuation like quotes (דו"ח), so we might need a simpler replace for now.
        processed = processed.replace(old_word, new_word)
        
    return processed
