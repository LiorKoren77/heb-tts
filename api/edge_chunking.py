"""
Chunking helpers for Edge TTS requests.
"""

MAX_WORDS_PER_CHUNK = 200


def _count_words(text: str) -> int:
    return len(text.split())


def chunk_text_by_lines(text: str, max_words_per_chunk: int = MAX_WORDS_PER_CHUNK) -> list[str]:
    """
    Build chunks by adding full lines until crossing a word threshold.
    This preserves line boundaries and avoids splitting mid-line.
    """
    lines = text.splitlines()
    chunks: list[str] = []
    current_lines: list[str] = []
    current_words = 0

    for line in lines:
        stripped = line.strip()

        # Preserve paragraph spacing when we already started a chunk.
        if not stripped:
            if current_lines:
                current_lines.append("")
            continue

        line_words = _count_words(stripped)

        # If adding this full line crosses threshold, flush current chunk first.
        if current_lines and (current_words + line_words > max_words_per_chunk):
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                chunks.append(chunk_text)
            current_lines = [stripped]
            current_words = line_words
            continue

        current_lines.append(stripped)
        current_words += line_words

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append(chunk_text)

    # Fallback: no newline content but non-empty text.
    if not chunks and text.strip():
        chunks.append(text.strip())

    return chunks
