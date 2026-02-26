"""
Sidebar component for settings and preferences.
Uses session_state to prevent reruns from interrupting audio generation.
"""
import streamlit as st

from utils.prefs import load_prefs, save_prefs
from utils.rate_limiter import RateLimiter
from ui.niqqud_helper import render_niqqud_helper
from ui.lexicon_editor import render_lexicon_editor

GEMINI_VOICE_OPTIONS = ("Puck", "Charon", "Kore", "Fenrir", "Aoede")
EDGE_VOICE_OPTIONS = (
    "he-IL-AvriNeural",
    "he-IL-HilaNeural",
    "he-IL-AvriMultilingualNeural",
    "he-IL-HilaMultilingualNeural",
)


def render_sidebar(rate_limiter: RateLimiter) -> dict:
    """
    Renders the sidebar with settings and returns the selected preferences.

    Args:
        rate_limiter: RateLimiter instance for displaying API limit status.

    Returns:
        Dictionary with user preferences:
          - tts_engine, gemini_voice, edge_voice, gemini_prompt
          - auto_nakdan_enabled, auto_numbers_enabled,
            static_lexicon_enabled, dynamic_llm_enabled
          - wait_time
    """
    if "preferences" not in st.session_state:
        prefs = load_prefs()
        st.session_state.preferences = {
            "tts_engine": prefs.get("tts_engine", "gemini"),
            "gemini_voice": prefs.get("gemini_voice", "Puck"),
            "edge_voice": prefs.get("edge_voice", "he-IL-AvriNeural"),
            "gemini_prompt": prefs.get("gemini_prompt", ""),
            "auto_nakdan_enabled": prefs.get("auto_nakdan", False),
            "auto_numbers_enabled": prefs.get("auto_numbers", True),
            "static_lexicon_enabled": prefs.get("static_lexicon", True),
            "dynamic_llm_enabled": prefs.get("dynamic_llm", False),
        }

    # --- Voice / engine settings ---
    st.sidebar.header("הגדרות קול")

    current_engine = st.session_state.preferences.get("tts_engine", "gemini")
    engine_options = ("gemini", "edge")
    engine_labels = {"gemini": "Gemini TTS", "edge": "Microsoft Edge TTS"}
    engine_index = (
        engine_options.index(current_engine)
        if current_engine in engine_options
        else 0
    )

    tts_engine = st.sidebar.selectbox(
        "בחר מנוע TTS:",
        engine_options,
        index=engine_index,
        format_func=lambda value: engine_labels[value],
        help="בחר מנוע. ההגדרות למטה משתנות לפי המנוע הנבחר.",
        key="sidebar_tts_engine_selectbox",
    )

    st.sidebar.subheader("הגדרות מנוע")
    gemini_voice = st.session_state.preferences.get("gemini_voice", "Puck")
    edge_voice = st.session_state.preferences.get("edge_voice", "he-IL-AvriNeural")
    gemini_prompt = st.session_state.preferences.get("gemini_prompt", "")

    if tts_engine == "gemini":
        gemini_default_index = (
            GEMINI_VOICE_OPTIONS.index(gemini_voice)
            if gemini_voice in GEMINI_VOICE_OPTIONS
            else 0
        )
        gemini_voice = st.sidebar.selectbox(
            "קול Gemini:",
            GEMINI_VOICE_OPTIONS,
            index=gemini_default_index,
            help="Puck ו-Charon נוטים להיות גבריים יותר, Kore ו-Aoede נשיים.",
            key="sidebar_gemini_voice_selectbox",
        )
        gemini_prompt = st.sidebar.text_area(
            "Prompt לסגנון דיבור (Gemini בלבד):",
            value=gemini_prompt,
            height=90,
            placeholder="לדוגמה: דבר כמו קריין רדיו, או דבר בביישנות ובעדינות.",
            help="הוראת סגנון אופציונלית למנוע Gemini בלבד.",
            key="sidebar_gemini_prompt_textarea",
        )
    else:
        edge_default_index = (
            EDGE_VOICE_OPTIONS.index(edge_voice)
            if edge_voice in EDGE_VOICE_OPTIONS
            else 0
        )
        edge_voice = st.sidebar.selectbox(
            "קול Edge:",
            EDGE_VOICE_OPTIONS,
            index=edge_default_index,
            help="בחר קול לבדיקת ניקוד מהירה וחסכונית לפני רינדור סופי ב-Gemini.",
            key="sidebar_edge_voice_selectbox",
        )

    # --- Processing options ---
    st.sidebar.markdown("---")
    st.sidebar.header("הגדרות עיבוד טקסט")

    auto_numbers_enabled = st.sidebar.checkbox(
        "1️⃣ המר מספרים למילים (num2words)",
        value=st.session_state.preferences["auto_numbers_enabled"],
        help="ממיר אוטומטית ספרות (לדוגמה '3') למילים בעברית ('שלוש'). מתבצע ראשון בעיבוד.",
        key="sidebar_auto_numbers",
    )

    static_lexicon_enabled = st.sidebar.checkbox(
        "2️⃣ הפעל מילון חריגים סטטי",
        value=st.session_state.preferences["static_lexicon_enabled"],
        help="מבצע 'מצא והחלף' מהיר למילים קבועות מראש (כמו דו\"ח -> דוח). מתבצע שני בעיבוד.",
        key="sidebar_static_lexicon",
    )

    dynamic_llm_enabled = st.sidebar.checkbox(
        "3️⃣ ✨ הפעל עיבוד דינמי (Gemini LLM)",
        value=st.session_state.preferences["dynamic_llm_enabled"],
        help=(
            "נותן ל-Gemini לקרוא את הטקסט לפני ההקראה ולפתוח ראשי תיבות או לזהות "
            "מונחים באנגלית באופן אוטומטי. מוסיף כמה שניות לעיבוד. מתבצע שלישי בעיבוד."
        ),
        key="sidebar_dynamic_llm",
    )

    auto_nakdan_enabled = st.sidebar.checkbox(
        "4️⃣ הפעל ניקוד אוטומטי (Nakdan API)",
        value=st.session_state.preferences["auto_nakdan_enabled"],
        help="מנקד את הטקסט אוטומטית בעזרת המנוע של Dicta. מתבצע אחרון בעיבוד.",
        key="sidebar_auto_nakdan",
    )

    # --- Persist any changes in a single save pass ---
    new_prefs = {
        "tts_engine": tts_engine,
        "gemini_voice": gemini_voice,
        "edge_voice": edge_voice,
        "gemini_prompt": gemini_prompt,
        "auto_numbers_enabled": auto_numbers_enabled,
        "static_lexicon_enabled": static_lexicon_enabled,
        "dynamic_llm_enabled": dynamic_llm_enabled,
        "auto_nakdan_enabled": auto_nakdan_enabled,
    }

    if any(
        new_prefs[k] != st.session_state.preferences.get(k)
        for k in new_prefs
    ):
        st.session_state.preferences.update(new_prefs)
        save_prefs({
            "tts_engine": tts_engine,
            "gemini_voice": gemini_voice,
            "edge_voice": edge_voice,
            "gemini_prompt": gemini_prompt,
            "auto_nakdan": auto_nakdan_enabled,
            "auto_numbers": auto_numbers_enabled,
            "static_lexicon": static_lexicon_enabled,
            "dynamic_llm": dynamic_llm_enabled,
        })

    # --- Rate limit status (display only — mutation happens in app.py) ---
    wait_time = rate_limiter.get_wait_time(st.session_state.api_requests)
    requests_used = len(st.session_state.api_requests)

    st.sidebar.markdown("---")
    if tts_engine == "gemini":
        st.sidebar.caption(
            f"📊 סטטוס בקשות API בדקה האחרונה (Gemini): {requests_used}/3"
        )
        if wait_time > 0:
            st.sidebar.warning(f"מגבלת חינם פעילה. מתפנה בעוד {wait_time} שניות.")
    else:
        st.sidebar.caption("ℹ️ Edge TTS פעיל - ללא מגבלת Gemini בדקה זו.")

    # --- Utility panels ---
    render_niqqud_helper()
    render_lexicon_editor()

    return {
        "tts_engine": st.session_state.preferences["tts_engine"],
        "gemini_voice": st.session_state.preferences["gemini_voice"],
        "edge_voice": st.session_state.preferences["edge_voice"],
        "gemini_prompt": st.session_state.preferences["gemini_prompt"],
        "auto_nakdan_enabled": st.session_state.preferences["auto_nakdan_enabled"],
        "auto_numbers_enabled": st.session_state.preferences["auto_numbers_enabled"],
        "static_lexicon_enabled": st.session_state.preferences["static_lexicon_enabled"],
        "dynamic_llm_enabled": st.session_state.preferences["dynamic_llm_enabled"],
        "wait_time": wait_time if st.session_state.preferences["tts_engine"] == "gemini" else 0,
    }
