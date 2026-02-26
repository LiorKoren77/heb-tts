import json
import os
import logging
import tempfile

logger = logging.getLogger(__name__)

PREFS_FILE = "user_prefs.json"

def load_prefs(
    default_voice="Puck",
    default_auto_nakdan=False,
    default_auto_numbers=True,
    default_static_lexicon=True,
    default_dynamic_llm=False,
):
    """
    Loads all preferences from a local JSON file.
    """
    prefs = {
        "tts_engine": "gemini",
        "last_voice": default_voice,
        "gemini_voice": default_voice,
        "edge_voice": "he-IL-AvriNeural",
        "gemini_prompt": "",
        "auto_nakdan": default_auto_nakdan,
        "auto_numbers": default_auto_numbers,
        "static_lexicon": default_static_lexicon,
        "dynamic_llm": default_dynamic_llm,
    }

    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()

            # raw_decode extracts the first valid JSON object and ignores any
            # trailing data (e.g. from two concurrent writes concatenating two
            # JSON objects into the same file).
            decoder = json.JSONDecoder()
            data, end_idx = decoder.raw_decode(raw)

            prefs["tts_engine"] = data.get("tts_engine", "gemini")
            prefs["last_voice"] = data.get("last_voice", default_voice)
            prefs["gemini_voice"] = data.get("gemini_voice", prefs["last_voice"])
            prefs["edge_voice"] = data.get("edge_voice", "he-IL-AvriNeural")
            prefs["gemini_prompt"] = data.get("gemini_prompt", "")
            prefs["auto_nakdan"] = data.get("auto_nakdan", default_auto_nakdan)
            prefs["auto_numbers"] = data.get("auto_numbers", default_auto_numbers)
            prefs["static_lexicon"] = data.get("static_lexicon", default_static_lexicon)
            prefs["dynamic_llm"] = data.get("dynamic_llm", default_dynamic_llm)

            # If there was trailing garbage, rewrite the file clean (atomically)
            # so the corruption does not persist across restarts.
            if end_idx < len(raw):
                logger.debug(
                    "Preferences file had trailing data (chars %d-%d); "
                    "rewriting clean copy.",
                    end_idx, len(raw),
                )
                try:
                    prefs_dir = os.path.dirname(os.path.abspath(PREFS_FILE)) or "."
                    with tempfile.NamedTemporaryFile(
                        "w", encoding="utf-8", dir=prefs_dir, delete=False, suffix=".tmp"
                    ) as tmp:
                        json.dump(data, tmp)
                        tmp_path = tmp.name
                    os.replace(tmp_path, PREFS_FILE)
                except (IOError, OSError) as write_err:
                    logger.warning("Could not rewrite prefs file: %s", write_err)

        except json.JSONDecodeError as e:
            logger.debug("Preferences file is empty or invalid, using defaults: %s", e)
        except (IOError, OSError) as e:
            logger.warning("Failed to read preferences file: %s", e)
            
    # Backward-compat: ensure last_voice matches current engine voice
    if prefs["tts_engine"] == "edge":
        prefs["last_voice"] = prefs.get("edge_voice", "he-IL-AvriNeural")
    else:
        prefs["last_voice"] = prefs.get("gemini_voice", default_voice)

    return prefs

def save_prefs(preferences: dict):
    """
    Saves all preferences to a local JSON file.
    """
    try:
        tts_engine = preferences.get("tts_engine", "gemini")
        gemini_voice = preferences.get("gemini_voice", "Puck")
        edge_voice = preferences.get("edge_voice", "he-IL-AvriNeural")

        prefs = {
            "tts_engine": tts_engine,
            "last_voice": edge_voice if tts_engine == "edge" else gemini_voice,
            "gemini_voice": gemini_voice,
            "edge_voice": edge_voice,
            "gemini_prompt": preferences.get("gemini_prompt", ""),
            "auto_nakdan": preferences.get("auto_nakdan", False),
            "auto_numbers": preferences.get("auto_numbers", True),
            "static_lexicon": preferences.get("static_lexicon", True),
            "dynamic_llm": preferences.get("dynamic_llm", False),
        }

        # Write atomically: write to a sibling temp file, then rename it over
        # the target.  On Linux, os.replace() is a single rename() syscall, so
        # readers never see an empty or partially-written file.
        prefs_dir = os.path.dirname(os.path.abspath(PREFS_FILE)) or "."
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=prefs_dir, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump(prefs, tmp)
            tmp_path = tmp.name
        os.replace(tmp_path, PREFS_FILE)
    except (IOError, OSError, TypeError) as e:
        logger.warning("Failed to save preferences: %s", e)
