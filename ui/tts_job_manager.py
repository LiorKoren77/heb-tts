"""
TTS job manager: thread state, background worker, and job lifecycle.

Owns all mutable cross-thread state so that ui/blocks.py (the View) has
zero threading knowledge. Public API for blocks.py:
  - start_tts_job(block, preferences)       — launch background conversion
  - finalize_tts_job(block, block_index, rate_limiter) — apply result on main thread
  - any_generating_block_needs_rerun()      — used by global poller in app.py
  - make_block(block_id)                    — canonical block dict factory
"""
import json
import logging
import threading
import time

import streamlit as st

from utils.audio_saver import make_audio_filepath
from utils.error_handling import handle_rate_limit_error
from utils.rate_limiter import RateLimiter
from utils.text_saver import save_processed_text
from api.gemini_tts import generate_tts_audio
from api.edge_tts import generate_edge_tts_audio

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thread-safe state
# ---------------------------------------------------------------------------

_THREAD_LOCK = threading.Lock()
_TTS_THREADS: dict[int, threading.Thread] = {}
_TTS_RESULTS: dict[int, dict] = {}
_EDGE_PROGRESS: dict[int, tuple[int, int]] = {}


def _set_thread_reference(block_id: int, thread: threading.Thread) -> None:
    with _THREAD_LOCK:
        _TTS_THREADS[block_id] = thread


def _get_thread_reference(block_id: int) -> threading.Thread | None:
    with _THREAD_LOCK:
        return _TTS_THREADS.get(block_id)


def _set_thread_result(block_id: int, result: dict) -> None:
    with _THREAD_LOCK:
        _TTS_RESULTS[block_id] = result


def _pop_thread_result(block_id: int) -> dict | None:
    with _THREAD_LOCK:
        return _TTS_RESULTS.pop(block_id, None)


def _set_edge_progress(block_id: int, converted_chars: int, total_chars: int) -> None:
    with _THREAD_LOCK:
        _EDGE_PROGRESS[block_id] = (converted_chars, total_chars)


def get_edge_progress(block_id: int) -> tuple[int, int]:
    """Returns (converted_chars, total_chars) for the given block."""
    with _THREAD_LOCK:
        return _EDGE_PROGRESS.get(block_id, (0, 0))


def _clear_background_state(block_id: int) -> None:
    with _THREAD_LOCK:
        _TTS_THREADS.pop(block_id, None)
        _TTS_RESULTS.pop(block_id, None)
        _EDGE_PROGRESS.pop(block_id, None)


# ---------------------------------------------------------------------------
# Block factory
# ---------------------------------------------------------------------------

def make_block(block_id: int) -> dict:
    """Returns a fresh block dict with default values."""
    return {
        "id": block_id,
        "state": "input",
        "original": "",
        "processed": "",
        "audio_path": None,
        "voice": None,
        "engine": None,
        "name": None,
    }


# ---------------------------------------------------------------------------
# Poller predicate (used by app.py)
# ---------------------------------------------------------------------------

def any_generating_block_needs_rerun() -> bool:
    """
    Returns True when any generating block has a result ready or its thread
    has died. The global poller uses this to decide whether a full-page rerun
    is needed for finalization, avoiding unnecessary reruns during active
    generation.
    """
    for key, value in st.session_state.items():
        if not (key.startswith("block_") and key.endswith("_generating") and value):
            continue
        try:
            block_id = int(key.split("_")[1])
        except (ValueError, IndexError):
            continue
        with _THREAD_LOCK:
            if block_id in _TTS_RESULTS:
                return True
            thread = _TTS_THREADS.get(block_id)
            if thread is not None and not thread.is_alive():
                return True
    return False


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _generate_audio_thread(block_id: int, processed_text: str,
                            saved_preferences: dict) -> None:
    try:
        engine = saved_preferences.get("tts_engine", "gemini")

        notebook_name = saved_preferences.get("_notebook_name", "notebook")
        block_name = saved_preferences.get("_block_name", f"block_{block_id}")

        if engine == "edge":
            edge_voice = saved_preferences.get("edge_voice", "he-IL-AvriNeural")
            audio_file_name = make_audio_filepath(notebook_name, block_name, "mp3")

            def edge_progress_callback(converted_chars: int, total_chars: int) -> None:
                _set_edge_progress(block_id, converted_chars, total_chars)

            audio_path = generate_edge_tts_audio(
                processed_text,
                edge_voice,
                output_file=audio_file_name,
                progress_callback=edge_progress_callback,
            )
            selected_voice = edge_voice

        else:
            valid_voices = ["puck", "charon", "kore", "fenrir", "aoede"]
            gemini_voice = saved_preferences.get("gemini_voice", "Puck")
            voice_lower = gemini_voice.lower()
            if voice_lower not in valid_voices:
                voice_lower = "puck"

            audio_file_name = make_audio_filepath(notebook_name, block_name, "wav")
            audio_path = generate_tts_audio(
                processed_text,
                voice_lower,
                output_file=audio_file_name,
                style_prompt=saved_preferences.get("gemini_prompt", ""),
            )
            selected_voice = gemini_voice

        _set_thread_result(
            block_id,
            {
                "status": "ok",
                "audio_path": audio_path,
                "voice": selected_voice,
                "engine": engine,
                "processed_text": processed_text,
            },
        )

    except ValueError as e:
        _set_thread_result(block_id, {"status": "error", "error": f"שגיאת קלט: {e}"})
    except RuntimeError as e:
        is_handled = handle_rate_limit_error(str(e))
        if not is_handled:
            _set_thread_result(block_id, {"status": "error",
                                          "error": f"שגיאה ביצירת אודיו: {e}"})
        else:
            _set_thread_result(block_id, {"status": "error",
                                          "error": "שגיאת Rate Limit בזיהוי מערכת."})
    except Exception as e:
        is_handled = handle_rate_limit_error(str(e))
        if not is_handled:
            logger.exception("Unexpected error in TTS generation")
            _set_thread_result(block_id, {"status": "error",
                                          "error": f"שגיאה בלתי צפויה: {e}"})
        else:
            _set_thread_result(block_id, {"status": "error",
                                          "error": "שגיאת Rate Limit בזיהוי מערכת."})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_tts_job(block: dict, preferences: dict) -> bool:
    """
    Launches background TTS conversion for the given block.

    Preferences are snapshotted into session_state so sidebar changes mid-run
    do not affect the in-flight job.

    Returns True if the job was started, False if one was already running.
    """
    block_id = block["id"]

    if st.session_state.get(f"block_{block_id}_generating", False):
        return False

    # Snapshot preferences at click time (caller has already written this key,
    # but we guard here so the function is self-contained).
    if f"block_{block_id}_preferences" not in st.session_state:
        st.session_state[f"block_{block_id}_preferences"] = preferences.copy()

    saved_preferences = st.session_state[f"block_{block_id}_preferences"]

    # Embed notebook/block names for audio file naming inside the background thread
    # (session_state is not accessible from non-Streamlit threads).
    saved_preferences["_notebook_name"] = st.session_state.get(
        "notebook_name", "notebook"
    )
    saved_preferences["_block_name"] = block.get("name") or f"block_{block_id}"

    st.session_state[f"block_{block_id}_generating"] = True
    st.session_state[f"block_{block_id}_error"] = None

    # Pre-seed char progress so a 0 % bar renders on the very first rerun.
    if saved_preferences.get("tts_engine", "gemini") == "edge":
        _set_edge_progress(block_id, 0, max(1, len(block["processed"])))

    thread = threading.Thread(
        target=_generate_audio_thread,
        args=(block_id, block["processed"], saved_preferences),
        daemon=True,
    )
    thread.start()
    _set_thread_reference(block_id, thread)
    return True


def finalize_tts_job(block: dict, block_index: int,
                     rate_limiter: RateLimiter) -> None:
    """
    Applies a completed thread result to the block on the main Streamlit thread.
    Must be called during a full-page rerun (safe session_state access).
    """
    block_id = block["id"]
    is_generating = st.session_state.get(f"block_{block_id}_generating", False)
    if not is_generating:
        return

    thread = _get_thread_reference(block_id)
    result = _pop_thread_result(block_id)

    if result is None:
        if thread is not None and thread.is_alive():
            return
        st.session_state[f"block_{block_id}_error"] = (
            "שגיאה בלתי צפויה: תהליך ההמרה הסתיים ללא תוצאה."
        )
        st.session_state[f"block_{block_id}_generating"] = False
        _clear_background_state(block_id)
        return

    if result.get("status") == "ok":
        block["audio_path"] = result["audio_path"]
        block["voice"] = result["voice"]
        block["engine"] = result["engine"]
        block["state"] = "audio"

        try:
            notebook_name = st.session_state.get(
                "notebook_name", "Gemini Hebrew TTS Notebook"
            )
            block_name = block.get("name") or f"בלוק {block_index + 1}"
            text_file_path = save_processed_text(
                notebook_name, block_name, result["processed_text"]
            )
            logger.info("Saved processed text to %s", text_file_path)
        except Exception as e:
            logger.error("Failed to save processed text: %s", e)

        if result["engine"] == "gemini":
            st.session_state.api_requests = rate_limiter.add_request(
                st.session_state.api_requests
            )

        if block_index == len(st.session_state.blocks) - 1:
            st.session_state.blocks.append(
                make_block(len(st.session_state.blocks))
            )
    else:
        st.session_state[f"block_{block_id}_error"] = result.get(
            "error", "שגיאה בלתי צפויה בהמרה."
        )

    st.session_state[f"block_{block_id}_generating"] = False
    _clear_background_state(block_id)
