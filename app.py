"""
Main Streamlit application for Gemini Hebrew TTS.
"""
import streamlit as st
import logging
from utils.rate_limiter import RateLimiter
from utils.logging_config import setup_logging
from ui.styles import inject_custom_css
from ui.sidebar import render_sidebar
from ui.blocks import render_text_block, render_add_block_button
from ui.tts_job_manager import any_generating_block_needs_rerun, make_block

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Hebrew TTS Reader", page_icon="🎙️", layout="wide")

inject_custom_css()

if "api_requests" not in st.session_state:
    st.session_state.api_requests = []

if "notebook_name" not in st.session_state:
    st.session_state.notebook_name = "Gemini Hebrew TTS Notebook"

col1, col2 = st.columns([0.05, 0.95])
with col1:
    st.markdown("# 🎙️")
with col2:
    notebook_title = st.text_input(
        "Notebook Title",
        value=st.session_state.notebook_name,
        key="notebook_title_input",
        label_visibility="collapsed",
    )
    if notebook_title != st.session_state.notebook_name:
        st.session_state.notebook_name = notebook_title
        st.rerun()

if "blocks" not in st.session_state:
    st.session_state.blocks = [make_block(0)]


rate_limiter = RateLimiter(max_requests=3, time_window_seconds=60)

# Clean stale API request timestamps before rendering (model mutation, not View).
st.session_state.api_requests = rate_limiter.clean_old_requests(
    st.session_state.api_requests
)

preferences = render_sidebar(rate_limiter)

for i, block in enumerate(st.session_state.blocks):
    render_text_block(block, i, preferences, rate_limiter)

render_add_block_button()


def _any_generation_active() -> bool:
    """Returns True when at least one block is currently generating audio."""
    return any(
        key.startswith("block_") and key.endswith("_generating") and bool(value)
        for key, value in st.session_state.items()
    )


@st.fragment(run_every=1)
def render_global_generation_poller() -> None:
    """
    Global poller that triggers a full-page rerun only when a background
    thread has a result ready for finalization. During active generation,
    progress is handled by per-block fragment reruns which are scoped and
    do not darken the page.
    """
    if _any_generation_active() and any_generating_block_needs_rerun():
        st.rerun()


render_global_generation_poller()
