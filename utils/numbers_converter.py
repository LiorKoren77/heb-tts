import re
from num2words import num2words

def fix_numbers(text: str) -> str:
    """
    Finds digits in the text and converts them to Hebrew words.
    Defaults to feminine form currently.
    """
    def replace_num(match):
        try:
            return num2words(int(match.group()), lang='he')
        except (ValueError, TypeError, OverflowError):
            # If conversion fails, return the original number
            return match.group()
            
    return re.sub(r'\d+', replace_num, text)
