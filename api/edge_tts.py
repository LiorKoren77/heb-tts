import asyncio
import os
import logging
from typing import Callable, Optional
import json
import time
import edge_tts
from api.edge_chunking import chunk_text_by_lines, MAX_WORDS_PER_CHUNK

logger = logging.getLogger(__name__)

# Common Hebrew voices for Microsoft Edge TTS.
VALID_EDGE_VOICES = {
    "he-IL-AvriNeural",
    "he-IL-HilaNeural",
    "he-IL-AvriMultilingualNeural",
    "he-IL-HilaMultilingualNeural",
}
CHUNK_TIMEOUT_SECONDS = 180


async def _synthesize_chunk_audio(chunk_text: str, voice_name: str) -> bytes:
    communicate = edge_tts.Communicate(text=chunk_text, voice=voice_name)
    audio_parts: list[bytes] = []

    async for event in communicate.stream():
        if event["type"] == "audio":
            audio_parts.append(event["data"])

    return b"".join(audio_parts)


async def _save_edge_tts_audio(
    text: str,
    voice_name: str,
    output_file: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    chunks = chunk_text_by_lines(text, max_words_per_chunk=MAX_WORDS_PER_CHUNK)
    if not chunks:
        raise RuntimeError("No chunks were produced for Edge TTS")

    total_chars = len(text)
    cumulative_chars = 0

    # Publish 0% immediately so the UI can render a progress bar before any chunk completes.
    if progress_callback:
        progress_callback(0, total_chars)

    with open(output_file, "wb") as output_fp:
        for index, chunk in enumerate(chunks, start=1):
            try:
                audio_bytes = await asyncio.wait_for(
                    _synthesize_chunk_audio(chunk, voice_name),
                    timeout=CHUNK_TIMEOUT_SECONDS,
                )
            except (asyncio.TimeoutError, TimeoutError) as e:
                raise RuntimeError(f"Edge chunk timed out at part {index}/{len(chunks)}") from e

            if not audio_bytes:
                raise RuntimeError(f"Empty audio bytes for Edge chunk {index}/{len(chunks)}")

            # Writing chunk bytes sequentially produces a single playable MP3 file.
            output_fp.write(audio_bytes)
            cumulative_chars += len(chunk)
            if progress_callback:
                progress_callback(cumulative_chars, total_chars)

    logger.info("Edge TTS finished with %s chunk(s)", len(chunks))
    return output_file


def generate_edge_tts_audio(
    text: str,
    voice_name: str,
    output_file: str = "temp_output.mp3",
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    Generates speech audio with Microsoft Edge TTS and saves it to an audio file.

    Args:
        text: The text to convert to speech.
        voice_name: Edge voice name (e.g. he-IL-AvriNeural).
        output_file: Path where the audio file will be saved.

    Returns:
        Path to the saved audio file.
    """
    # Strip Nakdan/Dicta separator marks before any further processing.
    text = text.replace("|", "")

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if voice_name not in VALID_EDGE_VOICES:
        raise ValueError(f"Invalid Edge voice: {voice_name}")

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        return asyncio.run(_save_edge_tts_audio(text, voice_name, output_file, progress_callback))
    except Exception as e:
        logger.error(f"Edge TTS generation failed: {e}")
        raise RuntimeError(f"Failed to generate Edge TTS audio: {e}") from e
