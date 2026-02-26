# Core Processing & Utils Team Documentation

This document provides focused context for the Core Processing & Utils team working on the Gemini Hebrew TTS project.

## Area of Responsibility
- Local text manipulation and preprocessing (`utils/` directory)
- Text processing pipeline orchestration (`utils/text_pipeline.py`)
- API Rate Limit state tracking logic
- File management (saving text and audio)
- General application logging logic

## Text Processing Pipeline

### Pipeline Orchestrator (`utils/text_pipeline.py`)
**Function**: `run_pipeline(text: str, preferences: dict) -> str`

This is the single entry point for all text preprocessing. The UI team calls this function directly; no pipeline logic lives in `ui/blocks.py`.

```python
from utils.text_pipeline import run_pipeline
processed = run_pipeline(block["original"], preferences)
```

**Pipeline order** (always applied in this sequence):
```
User Input Text
    ↓
[Markdown Cleaner]     → Remove markdown symbols (always first)
    ↓
[Number Converter]     → Convert digits to words (if auto_numbers_enabled)
    ↓
[Static Lexicon]       → Apply word replacements (if static_lexicon_enabled)
    ↓
[Dynamic LLM]          → Gemini LLM preprocessing (if dynamic_llm_enabled)
    ↓
[Nakdan Vocalization]  → Add Hebrew diacritics (if auto_nakdan_enabled)
    ↓
Processed Text (ready for TTS)
```

### 1. Markdown Cleaner (`utils/markdown_cleaner.py`)
**Function**: `clean_markdown(text: str) -> str`
- Removes markdown symbols (`*`, `_`, `` ` ``, `~`)
- Converts heading symbols to pause indicators (`...`)
- Runs **always** and is always **first** in the pipeline.

### 2. Numbers Converter (`utils/numbers_converter.py`)
**Function**: `fix_numbers(text: str) -> str`
- Converts digits to Hebrew words using the `num2words` library
- Handles conversion errors gracefully
- Runs **first** after markdown cleaning (when enabled)

### 3. Static Lexicon (`utils/static_lexicon.py`)
**Functions**:
- `apply_static_lexicon(text: str) -> str`
- `load_lexicon_from_file() -> dict`: Loads lexicon from `utils/lexicon.json`
- `save_lexicon_to_file(lexicon: dict) -> bool`
- `reload_lexicon() -> None`: Updates the `STATIC_LEXICON` global variable
- Operates using simple string replacement (no regex boundaries for Hebrew compatibility)
- Runs **second** after number conversion (when enabled)

### 4. Legacy Orchestrator (`utils/text_processing.py`)
**Function**: `preprocess_text(text, convert_numbers, apply_lexicon) -> str`

This module pre-dates `utils/text_pipeline.py`. It remains available but is **not used by the UI**. The canonical pipeline entry point is `run_pipeline` in `utils/text_pipeline.py`.

---

## Utility Modules

### Rate Limiter (`utils/rate_limiter.py`)
**Class**: `RateLimiter`

**Purpose**: Manages API rate limits (e.g., 3 requests per 60 seconds).

**Methods**:
- `add_request(request_times) -> List[float]`: Record new request timestamp.
- `clean_old_requests(request_times) -> List[float]`: Remove expired timestamps outside the time window. Called in `app.py` before the render loop (not in the View/sidebar).
- `can_make_request(request_times) -> bool`: Check if request is allowed.
- `get_wait_time(request_times) -> int`: Calculate wait time in seconds.

**Usage**:
```python
rate_limiter = RateLimiter(max_requests=3, time_window_seconds=60)
# In app.py, before rendering:
st.session_state.api_requests = rate_limiter.clean_old_requests(
    st.session_state.api_requests
)
```

### Error Handling (`utils/error_handling.py`)
**Functions**:
- `extract_wait_time_from_error(error_str) -> int`: Parses retry delay from error.
- `handle_rate_limit_error(error_str) -> bool`: Coordinates UI display for countdown timer.

### User Preferences (`utils/prefs.py`)
**Functions**:
- `load_prefs() -> dict`: Loads user preferences from `user_prefs.json`
- `save_prefs(prefs: dict) -> None`

### Character Counter (`utils/char_counter.py`)
**Functions**:
- `count_characters(text: str) -> int`: Counts characters including Hebrew diacritics/niqqud.
- `get_char_count_message(char_count: int) -> str`: Returns a formatted message for the UI.

---

## File Management & Saving

### Text Saver (`utils/text_saver.py`)
**Purpose**: Saves processed text blocks to Markdown files.

**Functions**:
- `get_unique_notebook_filename(notebook_name, directory) -> str`
- `save_processed_text(notebook_name, block_name, processed_text) -> str`

**Features**:
- Automatically creates `notebooks/` directory
- All blocks from the same notebook are saved to the same file in append mode
- Automatically renames files when the notebook name changes in the UI
- Resolves name collisions using numeric suffixes (`_1`, `_2`)
- Markdown format with block name as `# Heading`

**Thread safety**: Called from `ui/tts_job_manager.finalize_tts_job` on the main Streamlit thread (not from the background audio thread), so file I/O contention across blocks is minimal.

### Audio Storage Structure
- Temporary and generated audio files are stored in the `audio/` directory.
- Managed via `api/gemini_tts.py` and `api/edge_tts.py`; the folder is created by those modules.

---

## Logging System (`utils/logging_config.py`)
**Function**: `setup_logging(log_level, log_file) -> None`
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Allows switching between console stdout and file logging (e.g. `logs/app.log`)

---

## Interaction with Other Teams
- **UI Team**: Calls `run_pipeline()` (the new pipeline orchestrator) and `save_processed_text()`. The UI team's TTS job manager (`ui/tts_job_manager.py`) calls `save_processed_text` on the main Streamlit thread.
- **API Team**: Uses `RateLimiter` to ensure external API endpoints are not overloaded. Dynamic LLM and Nakdan API calls are dispatched from inside `run_pipeline`.
