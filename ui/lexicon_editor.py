"""
Lexicon editor component for editing the static lexicon dictionary.
Allows users to add, edit, and delete lexicon entries via a dialog interface.
"""
import streamlit as st
import pandas as pd
import logging
from utils.static_lexicon import load_lexicon_from_file, save_lexicon_to_file, reload_lexicon

logger = logging.getLogger(__name__)


@st.dialog("עריכת מילון חריגים", width="large")
def edit_lexicon_dialog():
    """
    Dialog for editing the lexicon dictionary.
    Displays a table with current entries and allows adding, editing, and deleting.
    """
    try:
        # Load current lexicon
        current_lexicon = load_lexicon_from_file()
        
        # Convert lexicon to DataFrame for editing
        # סדר העמודות: מילה חדשה (מימין) | מילה מקורית (משמאל) - RTL
        if current_lexicon:
            df_data = [
                {"מילה חדשה": value, "מילה מקורית": key}
                for key, value in current_lexicon.items()
            ]
            df = pd.DataFrame(df_data)
        else:
            # Empty DataFrame with correct columns (מילה חדשה מימין)
            df = pd.DataFrame(columns=["מילה חדשה", "מילה מקורית"])
        
        st.markdown("ערוך את המילון החריגים. ניתן להוסיף, לערוך ולמחוק שורות.")
        
        # Data editor with dynamic rows
        # column_order כדי להבטיח שהעמודות מוצגות בסדר הנכון (RTL)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_order=["מילה חדשה", "מילה מקורית"],
            column_config={
                "מילה חדשה": st.column_config.TextColumn(
                    "מילה חדשה",
                    help="המילה החדשה שתופיע במקום המילה המקורית",
                    required=True
                ),
                "מילה מקורית": st.column_config.TextColumn(
                    "מילה מקורית",
                    help="המילה המקורית שתוחלף",
                    required=True
                ),
            },
            hide_index=True,
            key="lexicon_editor_table"
        )
        
        # Buttons for save and cancel
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 שמור", type="primary", use_container_width=True):
                # Convert DataFrame back to dictionary
                new_lexicon = {}
                for _, row in edited_df.iterrows():
                    original = str(row["מילה מקורית"]).strip()
                    replacement = str(row["מילה חדשה"]).strip()
                    
                    # Skip empty rows
                    if original and replacement:
                        new_lexicon[original] = replacement
                
                # Save to file
                if save_lexicon_to_file(new_lexicon):
                    # Reload lexicon in the module
                    reload_lexicon()
                    st.success("המילון נשמר בהצלחה!")
                    st.rerun()
                else:
                    st.error("שגיאה בשמירת המילון. נסה שוב.")
        
        with col2:
            if st.button("❌ ביטול", use_container_width=True):
                st.rerun()
                
    except Exception as e:
        logger.error(f"Error in lexicon editor dialog: {e}")
        st.error(f"שגיאה בטעינת המילון: {e}")


def render_lexicon_editor():
    """
    Renders the lexicon editor expander in the sidebar.
    """
    st.sidebar.markdown("---")
    
    # Lexicon editor expander
    with st.sidebar.expander("📝 עריכת מילון חריגים"):
        st.markdown("ערוך את המילון החריגים הסטטי.")
        st.markdown("המילון משמש להחלפת מילים אוטומטית בעיבוד הטקסט.")
        
        if st.button("✏️ פתח עורך מילון", use_container_width=True):
            edit_lexicon_dialog()
