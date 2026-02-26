"""
Text saver utility for saving processed text blocks to Markdown files.
Each notebook = one file, all blocks are appended to the same file.
"""
import os
import re
from pathlib import Path
import streamlit as st


def get_unique_notebook_filename(notebook_name: str, directory: str) -> str:
    """
    Returns a unique filename for a notebook by appending numeric suffix if needed.
    
    Logic:
    1. Base name: notebook_name with spaces replaced by '_' + '.md'
    2. Check if file exists in directory:
       - If not: use base name
       - If exists: add numeric suffix (_1, _2, etc.) and check again
    3. Continue until finding an available filename
    
    Args:
        notebook_name: Name of the notebook
        directory: Directory where files are stored
        
    Returns:
        Unique filename (without full path)
        
    Examples:
        - "My Notebook" -> "My_Notebook.md" (if doesn't exist)
        - "My Notebook" -> "My_Notebook_1.md" (if My_Notebook.md exists)
        - "My Notebook" -> "My_Notebook_2.md" (if My_Notebook_1.md exists)
        - "מחברת שלי" -> "מחברת_שלי.md" or "מחברת_שלי_1.md" etc.
    """
    # Replace spaces with underscores
    base_name = notebook_name.replace(" ", "_")
    
    # Ensure .md extension
    if not base_name.endswith(".md"):
        base_name += ".md"
    
    # Check if base name exists
    base_path = Path(directory) / base_name
    if not base_path.exists():
        return base_name
    
    # Extract base name without extension
    name_without_ext = base_name[:-3]  # Remove .md
    
    # Check for existing numeric suffixes
    counter = 1
    while True:
        new_name = f"{name_without_ext}_{counter}.md"
        new_path = Path(directory) / new_name
        if not new_path.exists():
            return new_name
        counter += 1


def save_processed_text(notebook_name: str, block_name: str, processed_text: str) -> str:
    """
    Saves processed text block to a Markdown file.
    All blocks from the same notebook are appended to the same file.
    
    If notebook name changes, the existing file is renamed.
    
    Args:
        notebook_name: Name of the notebook (from session_state)
        block_name: Name of the block (displayed as heading)
        processed_text: The processed text to save
        
    Returns:
        Path to the saved file
    """
    # Get project directory (where app.py is located)
    project_dir = Path(__file__).parent.parent
    notebooks_dir = project_dir / "notebooks"
    
    # Create notebooks directory if it doesn't exist
    notebooks_dir.mkdir(exist_ok=True)
    
    # Check if notebook name changed or if this is first block
    current_file_path = st.session_state.get("notebook_file_path")
    current_file_name = st.session_state.get("notebook_file_name")
    
    if current_file_path and current_file_name == notebook_name:
        # Same notebook - use existing file
        file_path = Path(current_file_path)
    else:
        # Notebook name changed or first block - determine new filename
        new_filename = get_unique_notebook_filename(notebook_name, str(notebooks_dir))
        new_file_path = notebooks_dir / new_filename
        
        # If there's an existing file, rename it
        if current_file_path and Path(current_file_path).exists():
            old_file_path = Path(current_file_path)
            # Only rename if the new path is different
            if old_file_path != new_file_path:
                try:
                    # get_unique_notebook_filename already ensures the name is unique,
                    # but double-check in case of race condition
                    if new_file_path.exists() and new_file_path != old_file_path:
                        # Target exists but is different file - need new unique name
                        new_filename = get_unique_notebook_filename(notebook_name, str(notebooks_dir))
                        new_file_path = notebooks_dir / new_filename
                    
                    old_file_path.rename(new_file_path)
                    file_path = new_file_path
                except Exception as e:
                    # If rename fails, log error but continue with new file
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to rename file {old_file_path} to {new_file_path}: {e}")
                    file_path = new_file_path
            else:
                # Same path, no rename needed
                file_path = old_file_path
        else:
            # No existing file - create new one
            file_path = new_file_path
        
        # Update session_state
        st.session_state.notebook_file_path = str(file_path)
        st.session_state.notebook_file_name = notebook_name
    
    # Prepare content to append
    content = f"# {block_name}\n\n{processed_text}\n\n---\n\n"
    
    # Append to file (or create if doesn't exist)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)
    
    return str(file_path)
