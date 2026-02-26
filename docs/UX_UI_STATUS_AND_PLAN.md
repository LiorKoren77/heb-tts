# UX/UI Status and Plan

## Scope

- UI and frontend architecture review based on:
  - `app.py`
  - `ui/`
  - `utils/text_pipeline.py`
  - `docs/TEAM_FRONTEND.md`
- UX quality analysis with runtime-oriented behavior checks.

## Current Status

### 1. Architecture mapping — Up to date

- Main orchestrator: `app.py`
- UI modules:
  - `ui/sidebar.py` — View: settings and preferences
  - `ui/blocks.py` — View: notebook text blocks, pure rendering
  - `ui/tts_job_manager.py` — Controller: TTS thread state, job lifecycle, block factory
  - `ui/niqqud_helper.py` — sidebar display tool
  - `ui/lexicon_editor.py` — sidebar lexicon dialog
  - `ui/styles.py` — single CSS source of truth
- Core state objects:
  - `st.session_state.blocks`
  - `st.session_state.preferences`
  - `st.session_state.api_requests`
  - `st.session_state.notebook_name`
  - `st.session_state[f"block_{id}_generating"]`
  - `st.session_state[f"block_{id}_preferences"]` — snapshot at TTS click time

### 2. Processing pipeline behavior — Centralized

- Pipeline now lives in `utils/text_pipeline.py: run_pipeline(text, preferences) -> str`
- `ui/blocks.py` calls `run_pipeline(block["original"], preferences)` — no pipeline code in the View
- Pipeline order:
  1. Markdown cleaning (always)
  2. Numbers conversion (optional)
  3. Static lexicon replacement (optional)
  4. Dynamic LLM preprocessing (optional)
  5. Nakdan vocalization (optional)
- Re-running `עבד טקסט` overrides `block["processed"]` with a fresh result from `block["original"]`
- Processing preferences are applied on next click without manual page refresh

### 3. TTS and background generation flow — Optimized

- TTS runs in a background thread managed by `ui/tts_job_manager.py`
- Thread state (`_TTS_THREADS`, `_TTS_RESULTS`, `_EDGE_PROGRESS`) lives in `tts_job_manager`, not in `blocks.py`
- Edge TTS progress uses `(converted_chars, total_chars)` — char-based, not chunk-index-based
- **No page darkening during generation**: the global poller calls `st.rerun()` only when `any_generating_block_needs_rerun()` is True (thread result ready or thread died), not on every timer tick
- **Edge progress fragment**: `@st.fragment(run_every=0.5)` renders the progress bar independently; fragment reruns are scoped and never darken the page
- Progress bar shows immediately at 0% on button click (pre-seeded before thread starts)

### 4. Preference snapshotting — Active

- On TTS click, a copy of preferences is stored per block: `block_{id}_preferences = preferences.copy()`
- This ensures in-flight background jobs are not affected by sidebar changes mid-run

### 5. MVC compliance — Improved

- `ui/blocks.py`: pure View, no thread knowledge, no pipeline logic, no CSS injection
- `ui/tts_job_manager.py`: Controller, no rendering
- `utils/text_pipeline.py`: Model-layer orchestrator, no UI knowledge
- `ui/styles.py`: single CSS file, no inline styles in other files
- `app.py`: rate limiter cleanup happens here (before render loop), not in the View

---

## UX Quality Assessment

### Overall score: 8.0/10

### Strengths

- Clear notebook-style block flow
- Good modular decomposition: View/Controller/Model roles are now well separated
- RTL support and Hebrew-focused interaction model
- Background processing pattern with no page darkening during generation
- Edge TTS progress bar: immediate 0% display, char-based updates per chunk
- All CSS in one file with robust key-based selectors

### Remaining Risks / Gaps

- Limited input validation before processing/TTS
- Error recovery UX is basic (needs richer retry guidance)
- Rate-limit feedback can be more actionable
- No block deletion and no undo path (high user-control gap)

---

## Doc-Code Alignment Notes

All previously noted misalignments have been resolved:
- `preprocess_text` is no longer imported in `ui/blocks.py`
- Pipeline orchestration is now in `utils/text_pipeline.py`, documented in `TEAM_CORE.md`
- CSS is consolidated in `ui/styles.py`; fragile positional selectors replaced with key-based selectors
- `voice_option` removed from the preferences dict
- `rate_limiter.clean_old_requests` moved from `render_sidebar` to `app.py`

---

## UX/UI Improvement Plan

### Phase 1 (Quick wins, low effort)

1. Add pre-flight validation for input text and processed text.
2. Add block delete action with confirmation.
3. Improve char counter with threshold context (remaining/near-limit state).
4. Improve rate-limit message with clear countdown and next-action text.
5. Standardize status feedback language for process, success, and failure.

### Phase 2 (Medium effort)

1. Improve error handling UX with retry and probable-cause hints.
2. Add lexicon editor validation (duplicates/empty rows/data quality checks).
3. Add accessibility pass for keyboard flow and clearer semantic labels.

### Phase 3 (Structural UX improvements)

1. Introduce undo/redo or at least staged history for processed text.
2. Add import/export support for notebook content.
3. Expand audio UX controls for power users.

## Execution Priorities

- Critical first:
  - Validation before API actions
  - Error recovery UX
  - Block-level user control (delete)
- Then advanced usability:
  - Undo/history
  - Import/export
  - Accessibility

## Notes for future updates

- Keep this file updated when UX-affecting behavior changes in:
  - `app.py`
  - `ui/blocks.py`
  - `ui/tts_job_manager.py`
  - `ui/sidebar.py`
- If architecture changes significantly, update `docs/TEAM_FRONTEND.md` and this file together.
