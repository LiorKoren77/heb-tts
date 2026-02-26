"""
Text processing pipeline for block content.
Applies all configured preprocessing steps in the correct order.
"""
import logging

from utils.markdown_cleaner import clean_markdown
from utils.numbers_converter import fix_numbers
from utils.static_lexicon import apply_static_lexicon
from api.llm_preprocessor import dynamic_preprocess
from api.dicta_nakdan import auto_vocalize

logger = logging.getLogger(__name__)


def run_pipeline(text: str, preferences: dict) -> str:
    """
    Runs the full text processing pipeline on the given text.

    Steps (always in this order):
      1. Markdown cleaning  — always applied
      2. Numbers to words   — if auto_numbers_enabled
      3. Static lexicon     — if static_lexicon_enabled
      4. Dynamic LLM        — if dynamic_llm_enabled
      5. Nakdan vocalization — if auto_nakdan_enabled

    Args:
        text: Raw input text.
        preferences: Dict of processing flags from the sidebar.

    Returns:
        Processed text string.
    """
    processed = clean_markdown(text)

    if preferences.get("auto_numbers_enabled"):
        processed = fix_numbers(processed)

    if preferences.get("static_lexicon_enabled"):
        processed = apply_static_lexicon(processed)

    if preferences.get("dynamic_llm_enabled"):
        processed = dynamic_preprocess(processed)

    if preferences.get("auto_nakdan_enabled"):
        processed = auto_vocalize(processed)

    return processed
