# API Services Team Documentation

This document provides focused context for the API Services team working on the Gemini Hebrew TTS project.

## Area of Responsibility
- External API integrations (`api/` directory)
- API endpoint configurations and limits
- Network error handling
- Generation of the Text-to-Speech final result

## Key Components

### 1. External APIs (`api/`)

#### 1.1 Gemini TTS (`api/gemini_tts.py`)
**Function**: `generate_tts_audio(text, voice_name, output_file, style_prompt="") -> str`

**Purpose**: Text-to-speech conversion using Google's generative AI models.

**Model**: `gemini-2.5-flash-preview-tts`
**Method**: `client.models.generate_content()`
**Rate Limit**: 3 requests/minute (free tier limit)

**Parameters**:
- `text`: Hebrew text to convert (max 5000 chars)
- `voice_name`: One of `["puck", "charon", "kore", "fenrir", "aoede"]`
- `output_file`: Path for WAV file output (`audio/temp_output_{block_id}.wav`)
- `style_prompt`: Optional speaking-style instruction

**Audio Format Details**:
- Format: WAV
- Channels: 1 (mono)
- Sample width: 2 bytes (16-bit)
- Sample rate: 24000 Hz

**Error Handling**:
- Validates API key on import (raises `ValueError` if missing)
- Validates text and voice name
- Truncates text if too long
- Raises `RuntimeError` on API failure

**Caller**: `ui/tts_job_manager._generate_audio_thread` (background thread)

---

#### 1.2 Edge TTS (`api/edge_tts.py`)
**Function**: `generate_edge_tts_audio(text, voice_name, output_file, progress_callback=None) -> str`

**Purpose**: Free, offline-capable text-to-speech via Microsoft Edge TTS.
Used as a fast, cost-free alternative to Gemini TTS, particularly useful for proof-listening vocalized Hebrew before final Gemini rendering.

**Valid voices**:
```python
{
    "he-IL-AvriNeural",
    "he-IL-HilaNeural",
    "he-IL-AvriMultilingualNeural",
    "he-IL-HilaMultilingualNeural",
}
```

**Pre-processing step** (before chunking):
- Strips `|` characters added by the Dicta/Nakdan vocalization engine to mark word boundaries.
  These marks would be read aloud by the TTS engine if not removed.

**Chunking**:
- Long texts are split into word-count-bounded chunks via `api/edge_chunking.py`
  (`MAX_WORDS_PER_CHUNK = 200`)
- Each chunk is synthesized sequentially and the MP3 bytes are concatenated into a
  single output file

**Progress callback**:
- Signature: `progress_callback(converted_chars: int, total_chars: int) -> None`
- Called once with `(0, total_chars)` before the loop starts (0 % signal)
- Called after each chunk completes with the cumulative converted character count
- Used by `ui/tts_job_manager` to update `_EDGE_PROGRESS` for the UI fragment

**Output**: MP3 file (`audio/temp_output_{block_id}.mp3`)

**Caller**: `ui/tts_job_manager._generate_audio_thread` (background thread)

---

#### 1.3 Edge Chunking (`api/edge_chunking.py`)
**Function**: `chunk_text_by_lines(text, max_words_per_chunk=200) -> list[str]`

**Purpose**: Splits long Hebrew texts into chunks at line boundaries, respecting a maximum word count per chunk.

- Preserves line boundaries to avoid mid-sentence splits
- Falls back to the full text as a single chunk if no newlines are present
- `MAX_WORDS_PER_CHUNK = 200` is the module-level constant

---

#### 1.4 Dicta Nakdan (`api/dicta_nakdan.py`)
**Function**: `auto_vocalize(text) -> str`

**Purpose**: Adds Hebrew diacritics (niqqud) to input text via the Dicta Nakdan REST API.

**Endpoint**: `https://nakdan-u1-0.loadbalancer.dicta.org.il/api`
**Method**: POST
**Content-Type**: `application/json;charset=utf-8`
**Timeout**: 10 seconds

**Parameters**:
- `text`: Hebrew text (max 10000 chars)

**Request Configuration**:
```python
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
```

**Returns**: Vocalized text or the original text on network/API failure.

**Note**: Nakdan may insert `|` characters as word-boundary markers in its output.
These are stripped automatically by `generate_edge_tts_audio` before any processing.
They have no effect on Gemini TTS (which handles them gracefully).

---

#### 1.5 LLM Preprocessor (`api/llm_preprocessor.py`)
**Function**: `dynamic_preprocess(text) -> str`

**Purpose**: Uses Gemini LLM to improve text pronunciation:
- Expand acronyms (דו"ח → דוח)
- Convert transliterated words to English (ווטסאפ → WhatsApp)
- Prepares textual data for better TTS audio synthesis

**Model**: `gemini-2.5-flash`
**Temperature**: 0.1 (deterministic)
**Text Limit**: 5000 characters

**Caller**: `utils/text_pipeline.run_pipeline` (synchronous, main thread)

---

## Rate Limiting & Error Handling

### Rate Limit Errors (HTTP 429)
The Gemini API free tier is aggressively rate-limited (3 calls/minute).
- Rate limits are detected via error message parsing inside `utils/error_handling.py`
- Extracts the `retryDelay` parameter directly from the error response
- Exposes network errors to the UI via `RuntimeError`

### Generic Error Pattern Expected by UI
The API team must ensure failures bubble up properly for `ui/tts_job_manager` to catch:
```python
try:
    result = api_call()
except ValueError as e:
    # Handle validation (missing key, bad voices)
    raise
except RuntimeError as e:
    # Handle rate limits & network issues
    raise
```

---

## Environment Variable Setup
For the `api/` directory modules to function properly, the `.env` file must be configured with:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash-preview-tts
```

## Security & Privacy Considerations
1. **API Keys**: Excluded from source control via `.gitignore` (`.env` file).
2. **Input Validation**: Text bounds (5000 for Gemini, 10000 for Dicta) must be validated before transmitting payload externally.
3. **Data Loss on Failures**: Dicta API silently returns the original text on network timeouts to prevent total pipeline breakdown.

## Interaction with Other Teams
- **UI Team**: `ui/tts_job_manager._generate_audio_thread` calls `generate_tts_audio` and `generate_edge_tts_audio`. Exceptions (`ValueError`, `RuntimeError`) are caught by the job manager.
- **Core Processing Team**: `dynamic_preprocess` and `auto_vocalize` are called from `utils/text_pipeline.run_pipeline`. The `RateLimiter` class is used across API implementations for request tracking.
