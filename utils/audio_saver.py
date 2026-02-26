"""
Audio file naming utility.
Generates unique, human-readable paths for saved audio files.
"""
import os
import re
from pathlib import Path


_AUDIO_DIR = Path(__file__).parent.parent / "audio"


def _sanitize(name: str) -> str:
    """Replaces characters that are awkward in filenames with underscores."""
    # Allow Hebrew letters, ASCII word chars, digits, dots; collapse runs of bad chars
    cleaned = re.sub(r'[^\w\u05B0-\u05FF.]', '_', name)
    # Collapse multiple consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned.strip('_') or "untitled"


def make_audio_filepath(notebook_name: str, block_name: str, ext: str) -> str:
    """
    Returns a unique audio file path in the audio/ directory.

    Format:
      audio/<notebook>_<block>.<ext>           (first conversion)
      audio/<notebook>_<block>_1.<ext>         (second conversion, same names)
      audio/<notebook>_<block>_2.<ext>         (third, etc.)

    Args:
        notebook_name: Current notebook name from session_state.
        block_name:    Current block name.
        ext:           File extension without dot, e.g. "mp3" or "wav".

    Returns:
        Full relative path string ready to pass to the TTS API.
    """
    _AUDIO_DIR.mkdir(exist_ok=True)

    safe_notebook = _sanitize(notebook_name)
    safe_block = _sanitize(block_name)
    base = _AUDIO_DIR / f"{safe_notebook}_{safe_block}"

    candidate = base.with_suffix(f".{ext}")
    if not candidate.exists():
        return str(candidate)

    counter = 1
    while True:
        candidate = Path(f"{base}_{counter}.{ext}")
        if not candidate.exists():
            return str(candidate)
        counter += 1
