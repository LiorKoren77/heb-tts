import re

def clean_markdown(text: str) -> str:
    """
    Handles markdown symbols. 
    Instead of removing them entirely, we can convert headings to a format 
    that the TTS model might understand as a cue for a pause or emphasis.
    """
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            # נוריד את הסולמיות, נוסיף פסיק (פאוזה קלה)
            clean_line = re.sub(r'^#+\s*', '', stripped_line)
            # נוסיף שתי נקודות בסוף השורה כדי שהקריין יעשה פאוזה ארוכה ומשמעותית יותר אחרי כותרת
            if clean_line:
                # מורידים סימני פיסוק קיימים בסוף ומוסיפים סימן של פאוזה ארוכה (שלוש נקודות)
                clean_line = re.sub(r'[.:!?]+$', '', clean_line)
                clean_line += '...'
            processed_lines.append(clean_line)
        else:
            processed_lines.append(line)
            
    text_with_headings_handled = '\n'.join(processed_lines)
    
    # עכשיו נסיר את שאר סימני המארקדאון (הדגשות, נטוי וכו') אבל נשמור על פיסוק חוקי
    return re.sub(r'[*_`~]', '', text_with_headings_handled)
