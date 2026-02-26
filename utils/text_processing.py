from utils.markdown_cleaner import clean_markdown
from utils.numbers_converter import fix_numbers
from utils.static_lexicon import apply_static_lexicon

def preprocess_text(text: str, convert_numbers: bool = True, apply_lexicon: bool = True) -> str:
    """
    Full preprocessing pipeline: 
    1. Cleans markdown (always first)
    2. Optionally converts numbers to words (first after markdown)
    3. Optionally applies static lexicon replacements (second after markdown)
    
    Note: This function is used for basic preprocessing. For full pipeline
    with LLM and Nakdan, see ui/blocks.py render_text_block function.
    """
    clean_text = clean_markdown(text)
    
    # המר מספרים למילים - ראשון אחרי markdown
    if convert_numbers:
        clean_text = fix_numbers(clean_text)
        
    # מילון חריגים סטטי - שני אחרי markdown
    if apply_lexicon:
        clean_text = apply_static_lexicon(clean_text)
        
    return clean_text
