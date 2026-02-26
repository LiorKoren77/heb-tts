"""
Reusable component for processing step checkboxes.
Contains: checkbox, number icon, description text, and help tooltip.
Layout: Right side (checkbox, number icon, text) | Left side (help icon)
"""
import streamlit as st


def render_processing_step_checkbox(
    label: str,
    value: bool,
    help_text: str,
    step_number: int,
    step_emoji: str = "🔢",
    key: str = None
) -> bool:
    """
    Renders a processing step checkbox with custom layout.
    
    Layout:
    - Right side: checkbox, number icon (step_emoji + step_number), description text
    - Left side: help tooltip icon (❓)
    
    Args:
        label: The description text for the processing step
        value: Initial checkbox value
        help_text: Tooltip text to display on hover
        step_number: Step number (1, 2, 3, 4, etc.)
        step_emoji: Emoji to display before the step number (default: 🔢)
        key: Unique key for the checkbox widget
        
    Returns:
        Current checkbox value (bool)
    """
    # Create custom layout using sidebar columns
    # Left column for help icon, right column for checkbox + number + text
    col_left, col_right = st.sidebar.columns([0.15, 0.85])
    
    with col_left:
        # Help tooltip icon on the left
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; height: 100%; padding-top: 0.5rem;">
            <span title="{help_text}" style="cursor: help; font-size: 1.1rem; color: #808495;">❓</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        # Right side: checkbox, number icon, and description text
        # Format: {step_emoji} {step_number}️⃣ {label}
        checkbox_value = st.checkbox(
            f"{step_emoji} {step_number}️⃣ {label}",
            value=value,
            key=key,
            help=""  # Empty help since we have custom tooltip on the left
        )
    
    return checkbox_value
