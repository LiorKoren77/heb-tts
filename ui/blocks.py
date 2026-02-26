"""
Text blocks component for notebook-style interface.
"""
import json
import logging
import os
import time

import streamlit as st

from utils.char_counter import count_characters, get_char_count_message
from utils.rate_limiter import RateLimiter
from utils.text_pipeline import run_pipeline
from ui.tts_job_manager import (
    any_generating_block_needs_rerun,
    finalize_tts_job,
    get_edge_progress,
    make_block,
    start_tts_job,
)

logger = logging.getLogger(__name__)

# Re-export so app.py can import from this module without knowing about
# tts_job_manager (preserves the existing app.py import line).
__all__ = [
    "render_text_block",
    "render_add_block_button",
    "any_generating_block_needs_rerun",
]


@st.fragment(run_every=0.5)
def _render_edge_progress_fragment(block_id: int) -> None:
    """
    Renders the Edge TTS progress bar as a self-updating fragment.
    Fragment reruns are scoped and do not trigger a full-page rerun, so the
    page never darkens while generation is in progress.
    """
    is_generating = st.session_state.get(f"block_{block_id}_generating", False)
    if not is_generating:
        return
    converted_chars, total_chars = get_edge_progress(block_id)
    progress_value = (
        min(1.0, converted_chars / total_chars) if total_chars > 0 else 0.0
    )
    pct = int(progress_value * 100)
    st.progress(progress_value, text=f"🔄 Edge TTS: מייצר אודיו... {pct}%")


def render_text_block(
    block: dict, block_index: int, preferences: dict, rate_limiter: RateLimiter
) -> None:
    """
    Renders a single text block with input, processing, and audio output.

    Args:
        block: Block dict with id, state, original, processed, audio_path,
               voice, engine, name.
        block_index: Index of the block in the blocks list.
        preferences: Dict of processing preferences from the sidebar.
        rate_limiter: RateLimiter instance.
    """
    with st.container():
        if "name" not in block or block["name"] is None:
            block["name"] = f"בלוק {block_index + 1}"

        block_name_key = f"block_name_{block['id']}"

        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            st.markdown("### 📝")
        with col2:
            block_name = st.text_input(
                "Block Name",
                value=block["name"],
                key=block_name_key,
                label_visibility="collapsed",
            )
            if block_name != block["name"]:
                block["name"] = block_name

        # 1. Original text input
        new_orig = st.text_area(
            "טקסט מקורי:",
            value=block["original"],
            height=450,
            key=f"orig_{block['id']}",
        )
        block["original"] = new_orig

        # Process button
        if st.button("עבד טקסט", key=f"process_{block['id']}"):
            if block["original"].strip():
                with st.spinner("מעבד טקסט..."):
                    if preferences.get("dynamic_llm_enabled"):
                        st.toast("מפעיל סוכן Gemini לעיבוד שפה...", icon="🤖")
                    block["processed"] = run_pipeline(block["original"], preferences)
                    if block["state"] == "input":
                        block["state"] = "edit"
                    st.rerun()

        # 2. Processed text editor (shown after processing)
        if block["state"] in ["edit", "audio"] and block["processed"]:
            new_proc = st.text_area(
                "עריכה סופית לפני הקראה (ניתן לנקד ידנית):",
                value=block["processed"],
                height=450,
                key=f"proc_{block['id']}",
            )
            block["processed"] = new_proc

            char_count = count_characters(new_proc)
            st.info(get_char_count_message(char_count))

            engine_label = "Gemini" if preferences["tts_engine"] == "gemini" else "Edge"
            active_voice = (
                preferences["gemini_voice"]
                if preferences["tts_engine"] == "gemini"
                else preferences["edge_voice"]
            )
            st.caption(f"מנוע פעיל: {engine_label} | קול פעיל: {active_voice}")

            if preferences["tts_engine"] == "gemini" and preferences["wait_time"] > 0:
                st.button(
                    "🎙️ הפוך לדיבור (שלח ל-Gemini)",
                    disabled=True,
                    key=f"tts_disabled_{block['id']}",
                )
            else:
                button_label = (
                    "🎙️ הפוך לדיבור (שלח ל-Gemini)"
                    if preferences["tts_engine"] == "gemini"
                    else "🎙️ הפוך לדיבור (שלח ל-Edge)"
                )
                if st.button(button_label, key=f"tts_{block['id']}"):
                    if block["processed"].strip():
                        # Snapshot preferences at click time so in-flight jobs
                        # are unaffected by sidebar changes.
                        st.session_state[f"block_{block['id']}_preferences"] = (
                            preferences.copy()
                        )
                        started = start_tts_job(block, preferences)
                        if started:
                            st.info(
                                "ההמרה מתחילה ברקע. "
                                "ניתן לשנות הגדרות בסיידבר - ההמרה לא תיעצר."
                            )

        # Apply finished background result on the main thread.
        finalize_tts_job(block, block_index, rate_limiter)

        # Generation status / progress
        is_generating = st.session_state.get(f"block_{block['id']}_generating", False)
        if is_generating:
            saved_preferences = st.session_state.get(
                f"block_{block['id']}_preferences", {}
            )
            inflight_engine = saved_preferences.get(
                "tts_engine", preferences.get("tts_engine", "gemini")
            )
            if inflight_engine == "edge":
                _render_edge_progress_fragment(block["id"])
            else:
                st.info(
                    "🔄 Gemini TTS: מייצר אודיו ברקע... "
                    "(ללא התקדמות אחוזית זמינה מה-API)"
                )
        elif st.session_state.get(f"block_{block['id']}_error"):
            st.error(st.session_state[f"block_{block['id']}_error"])

        # 3. Audio output — only shown when the audio belongs to the currently
        # selected engine. Switching engines hides the stale result so the user
        # can re-convert without seeing outdated output.
        engine_matches = block.get("engine") == preferences.get("tts_engine")
        if block["state"] == "audio" and block["audio_path"] and engine_matches:
            engine_used = block.get("engine", "gemini")
            engine_label = "Gemini" if engine_used == "gemini" else "Edge"
            st.success(
                f"השמע מוכן! (מנוע: {engine_label}, קול: {block['voice']})"
            )
            st.audio(block["audio_path"])

            audio_ext = os.path.splitext(block["audio_path"])[1].lower()
            mime_type = "audio/wav" if audio_ext == ".wav" else "audio/mpeg"
            download_ext = "wav" if audio_ext == ".wav" else "mp3"
            with open(block["audio_path"], "rb") as file:
                st.download_button(
                    label=f"📥 הורד קובץ שמע ({download_ext.upper()})",
                    data=file,
                    file_name=f"tts_hebrew_block_{block_index + 1}.{download_ext}",
                    mime=mime_type,
                    key=f"dl_{block['id']}",
                )

        st.markdown("---")


def render_add_block_button() -> None:
    """Renders the button to add a new block."""
    if st.button("➕ הוסף בלוק חדש", key="add_block_btn"):
        st.session_state.blocks.append(make_block(len(st.session_state.blocks)))
        st.rerun()
