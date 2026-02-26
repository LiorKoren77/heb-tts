"""
Niqqud (Hebrew diacritics) helper tool for the sidebar.
Allows users to view and select niqqud marks for Hebrew letters.
"""
import streamlit as st


# סימני הניקוד בעברית עם שמותיהם
NIQQUD_MARKS = {
    "פתח": "ַ",  # Patach
    "קמץ": "ָ",  # Kamatz
    "צירה": "ֵ",  # Tzeire
    "סגול": "ֶ",  # Segol
    "חולם": "ֹ",  # Holam
    "שורוק": "וּ",  # Shuruk
    "קובוץ": "ֻ",  # Kubutz
    "חיריק": "ִ",  # Hiriq
    "שווא": "ְ",  # Sheva
    "חטף פתח": "ֲ",  # Hataf Patach
    "חטף קמץ": "ֳ",  # Hataf Kamatz
    "חטף סגול": "ֱ",  # Hataf Segol
}

# אותיות עבריות — רשימה רגילה + אותיות בגדכפת דגושות (U+05BC)
HEBREW_LETTERS = list("אבגדהוזחטיכלמנסעפצקרשת") + [
    "בּ", "גּ", "דּ", "כּ", "פּ", "תּ",  # begadkefat with dagesh
]


def render_niqqud_helper():
    """
    Renders the niqqud helper tool in the sidebar.
    Allows users to select a letter and view/change its niqqud mark.
    """
    st.sidebar.markdown("---")
    
    # כלי עזר לניקוד - ניתן לקיפול
    letter_with_niqqud = HEBREW_LETTERS[0]
    
    with st.sidebar.expander("🔤 כלי עזר לניקוד"):
        # בחירת אות
        selected_letter = st.selectbox(
            "בחר אות:",
            options=HEBREW_LETTERS,
            index=0,
            help="בחר אות כדי לראות ולשנות את הניקוד שלה"
        )
        
        # בחירת ניקוד
        niqqud_options = ["ללא ניקוד"] + list(NIQQUD_MARKS.keys())
        selected_niqqud_name = st.radio(
            "בחר ניקוד:",
            options=niqqud_options,
            help="בחר ניקוד כדי לראות את האות המנוקדת"
        )
        
        # הצגת האות עם או בלי ניקוד
        if selected_niqqud_name == "ללא ניקוד":
            selected_niqqud_mark = ""
            letter_with_niqqud = selected_letter
        else:
            selected_niqqud_mark = NIQQUD_MARKS[selected_niqqud_name]
            letter_with_niqqud = selected_letter + selected_niqqud_mark
        st.markdown(f"**האות עם ניקוד:**")
        st.code(letter_with_niqqud)
        
        # מידע נוסף
        with st.expander("ℹ️ מידע על ניקוד"):
            st.markdown("""
            **סימני הניקוד:**
            - **פתח** (ַ) - צליל 'a' כמו במילה 'אבא'
            - **קמץ** (ָ) - צליל 'a' ארוך
            - **צירה** (ֵ) - צליל 'e' כמו במילה 'בית'
            - **סגול** (ֶ) - צליל 'e' קצר
            - **חולם** (ֹ) - צליל 'o' כמו במילה 'בית'
            - **שורוק** (וּ) - צליל 'u' ארוך
            - **קובוץ** (ֻ) - צליל 'u' קצר
            - **חיריק** (ִ) - צליל 'i' כמו במילה 'בית'
            - **שווא** (ְ) - ללא צליל או צליל קצר מאוד
            - **חטף פתח** (ֲ), **חטף קמץ** (ֳ), **חטף סגול** (ֱ) - שווא עם ניקוד
            """)
    
