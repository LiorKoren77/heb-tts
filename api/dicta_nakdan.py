import requests
import logging

logger = logging.getLogger(__name__)

DICTA_NAKDAN_API_URL = "https://nakdan-u1-0.loadbalancer.dicta.org.il/api"

def auto_vocalize(text: str) -> str:
    """
    Sends Hebrew text to Dicta's Nakdan API to get the fully vocalized (Niqqud) version.
    Returns the vocalized text, or the original text if the API fails.
    
    Args:
        text: Hebrew text to vocalize
        
    Returns:
        Vocalized text with niqqud, or original text if API fails
    """
    if not text or not text.strip():
        return text
    
    # Limit text length to prevent API issues
    MAX_TEXT_LENGTH = 10000
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning(f"Text too long ({len(text)} chars), truncating to {MAX_TEXT_LENGTH}")
        text = text[:MAX_TEXT_LENGTH]
        
    try:
        payload = {
            "addmorph": True,
            "keepmetagim": True,
            "keepqq": False,
            "nodageshdefmem": False,
            "patachma": False,
            "task": "nakdan",
            "data": text,
            "useTokenization": True,
            "genre": "modern"
        }
        
        headers = {
            "Content-Type": "application/json;charset=utf-8"
        }
        
        response = requests.post(DICTA_NAKDAN_API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # The API returns a list of objects representing words/tokens
            result_data = response.json()
            
            # Reconstruct the vocalized text from the response
            # Each item has a 'word' property containing the original word or punctuation
            # And an 'options' array. If options exist, options[0] is the top prediction.
            vocalized_words = []
            
            # The structure is: response -> "data" -> list of items.
            # Each item has either "nakdan" dict (with "options") or just "str" / "pStr"
            for item in result_data.get("data", []):
                if "nakdan" in item and "options" in item["nakdan"] and len(item["nakdan"]["options"]) > 0:
                    vocalized_words.append(item["nakdan"]["options"][0]["w"]) 
                elif "str" in item:
                    vocalized_words.append(item["str"])
                    
            # Join the words (Dicta preserves spaces/newlines as separate tokens with "sep": true)
            return "".join(vocalized_words)
        else:
            print(f"Dicta API returned status code {response.status_code}")
            return text
            
    except requests.RequestException as e:
        # Log error but don't import streamlit here (decoupling)
        logger.error(f"Dicta API request failed: {e}")
        return text
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse Dicta API response: {e}")
        return text
