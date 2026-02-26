"""
Character counter utility for text length calculation.
Counts characters in memory (including diacritics/niqqud).
"""


def count_characters(text: str) -> int:
    """
    Counts the number of characters in a text string.
    This counts actual characters in memory, including diacritics/niqqud marks.
    
    Args:
        text: The text string to count
        
    Returns:
        The number of characters in the text
    """
    return len(text)


def get_char_count_message(char_count: int) -> str:
    """
    Generates a formatted message for character count display.
    
    Args:
        char_count: The number of characters
        
    Returns:
        Formatted message string
    """
    return f"📊 מספר תווים בזיכרון: {char_count}"
