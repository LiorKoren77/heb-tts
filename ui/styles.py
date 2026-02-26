"""
CSS styles for the application.
All custom CSS lives here. No inline st.markdown(<style>) calls elsewhere.
"""
import streamlit as st


def inject_custom_css() -> None:
    """Injects all custom CSS for RTL layout, input styling, and sidebar."""
    st.markdown("""
        <style>

        /* ===== Global RTL layout ===== */

        .block-container, [data-testid="stSidebarContent"] {
            direction: rtl;
        }

        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, span {
            text-align: right !important;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {
            direction: rtl !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebarContent"] h1,
        [data-testid="stSidebarContent"] h2,
        [data-testid="stSidebarContent"] h3 {
            text-align: right !important;
            direction: rtl !important;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebarContent"] label {
            text-align: right !important;
            direction: rtl !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebarContent"] [data-testid="stSelectbox"] label {
            text-align: right !important;
            direction: rtl !important;
        }

        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebarContent"] .stCaption,
        [data-testid="stSidebar"] [data-baseweb="notification"],
        [data-testid="stSidebarContent"] [data-baseweb="notification"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebarContent"] p {
            text-align: right !important;
            direction: rtl !important;
        }

        div.stButton, div.stDownloadButton {
            display: flex;
            justify-content: flex-start !important;
            direction: rtl !important;
        }

        /* ===== Sidebar checkboxes (RTL layout) ===== */

        [data-testid="stSidebar"] [data-testid="stCheckbox"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] {
            direction: rtl !important;
            width: 100% !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] {
            display: flex !important;
            flex-direction: row-reverse !important;
            align-items: center !important;
            justify-content: flex-end !important;
            width: 100% !important;
            direction: rtl !important;
            gap: 0.5rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child {
            order: 3 !important;
            flex-shrink: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"],
        [data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input,
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input {
            order: 2 !important;
            margin-left: 0.5rem !important;
            margin-right: 0 !important;
            flex-shrink: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > div,
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"] > div {
            order: 1 !important;
            display: flex !important;
            flex-direction: row-reverse !important;
            align-items: center !important;
            justify-content: flex-end !important;
            direction: rtl !important;
            flex: 1 !important;
            min-width: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] [data-testid="stWidgetLabel"] {
            display: flex !important;
            flex-direction: row-reverse !important;
            align-items: center !important;
            justify-content: flex-end !important;
            direction: rtl !important;
            gap: 0.25rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] {
            order: 2 !important;
            text-align: right !important;
            direction: rtl !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {
            text-align: right !important;
            direction: rtl !important;
            margin: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-testid="stTooltipIcon"],
        [data-testid="stSidebarContent"] [data-testid="stCheckbox"] [data-testid="stTooltipIcon"] {
            order: 1 !important;
            flex-shrink: 0 !important;
        }

        /* Sidebar checkbox with key="sidebar_static_lexicon": help icon on the left */
        [data-testid="stSidebar"] [data-testid="stCheckbox"]:has(input[key="sidebar_static_lexicon"]) label[data-baseweb="checkbox"] > div {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: space-between !important;
            direction: ltr !important;
            width: 100% !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"]:has(input[key="sidebar_static_lexicon"]) [data-testid="stWidgetLabel"] {
            display: flex !important;
            flex-direction: row-reverse !important;
            align-items: center !important;
            justify-content: flex-end !important;
            direction: rtl !important;
            flex: 1 !important;
            order: 2 !important;
        }

        [data-testid="stSidebar"] [data-testid="stCheckbox"]:has(input[key="sidebar_static_lexicon"]) [data-testid="stTooltipIcon"] {
            order: 1 !important;
            margin-left: 0 !important;
            margin-right: 0.5rem !important;
            flex-shrink: 0 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="checkbox"],
        [data-testid="stSidebarContent"] [data-baseweb="checkbox"] {
            direction: rtl !important;
            flex-direction: row-reverse !important;
        }

        [data-testid="stCheckbox"] {
            direction: rtl;
            display: flex;
            justify-content: flex-start;
            text-align: right;
        }

        [data-testid="stCheckbox"] > label {
            flex-direction: row-reverse;
            justify-content: flex-end;
            width: 100%;
        }

        /* ===== Text areas ===== */

        div.stTextArea > div > div > textarea {
            direction: rtl;
            text-align: right;
        }

        /* ===== Notebook title input (styled as heading) ===== */

        div[data-testid="stTextInput"]:has(input[key="notebook_title_input"]) > div > div > input {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
            color: inherit !important;
        }

        div[data-testid="stTextInput"]:has(input[key="notebook_title_input"]) > div > div > input:focus {
            border: 2px solid #1f77b4 !important;
            border-radius: 4px !important;
            padding: 0.25rem !important;
            background: white !important;
        }

        /* ===== Block name inputs (styled as sub-headings, one rule covers all blocks) ===== */

        div[data-testid="stTextInput"]:has(input[id^="block_name_"]) > div > div > input {
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
            color: inherit !important;
        }

        div[data-testid="stTextInput"]:has(input[id^="block_name_"]) > div > div > input:focus {
            border: 2px solid #1f77b4 !important;
            border-radius: 4px !important;
            padding: 0.25rem !important;
            background: white !important;
        }

        /* ===== Block container ===== */

        .block-container {
            padding: 2rem;
            border-radius: 10px;
            background-color: rgba(128, 128, 128, 0.05);
            margin-bottom: 2rem;
        }

        </style>
    """, unsafe_allow_html=True)
