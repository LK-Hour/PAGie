"""
File Explorer Component for PAGie
=================================

A file explorer component that shows CV files and allows users to view them directly
in the Streamlit interface.
"""

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import pypdf
import io

def render_file_explorer() -> None:
    """Render the file explorer section in the sidebar."""
    st.markdown("### :material/folder: File Explorer")
    
    cv_folder = Path("./data/drive")
    
    if not cv_folder.exists():
        st.info("No CV files folder found.\nRun 'Sync CV Files' first.")
        return
    
    # Get all PDF files
    pdf_files = list(cv_folder.glob("*.pdf"))
    
    if not pdf_files:
        st.info("No CV files found.\nRun 'Sync CV Files' to download CVs.")
        return
    
    # Sort files by modification time (newest first)
    pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    st.caption(f"Found {len(pdf_files)} CV files:")
    
    # Display files with clickable options
    for pdf_file in pdf_files:
        _render_file_item(pdf_file)

def _render_file_item(file_path: Path) -> None:
    """Render a single file item with metadata and actions."""
    
    # Get file metadata
    stat = file_path.stat()
    file_size = _format_file_size(stat.st_size)
    mod_time = datetime.fromtimestamp(stat.st_mtime)
    
    # Create unique key from file path (handle spaces and special chars)
    file_key = str(file_path).replace(" ", "_").replace("/", "_")
    
    # Create expandable section for each file
    with st.expander(f":material/description: {file_path.stem}", expanded=False):
        # File metadata
        st.caption(f"Size: {file_size}")
        st.caption(f"Modified: {mod_time.strftime('%b %d, %H:%M')}")
        
        st.divider()
        
        # Action buttons - equal columns for consistency
        col1, col2 = st.columns(2)
        
        with col1:
            # View button
            if st.button(
                ":material/visibility: View", 
                key=f"view_{file_key}", 
                use_container_width=True,
                help="View PDF in main area"
            ):
                _show_pdf_content(file_path)
        
        with col2:
            # Download button
            with open(file_path, "rb") as file:
                st.download_button(
                    label=":material/download: Download",
                    data=file.read(),
                    file_name=file_path.name,
                    mime="application/pdf",
                    key=f"download_{file_key}",
                    use_container_width=True,
                    help="Download PDF file"
                )

def _show_pdf_content(file_path: Path) -> None:
    """Display PDF content in the main area."""
    
    # Store selected file in session state to display in main area
    st.session_state['selected_file'] = str(file_path)
    st.session_state['show_file_viewer'] = True
    st.rerun()

def render_file_viewer() -> None:
    """Render the file viewer in the main content area."""
    
    if not st.session_state.get('show_file_viewer', False):
        return
    
    selected_file = st.session_state.get('selected_file')
    if not selected_file or not Path(selected_file).exists():
        st.error("File not found or no file selected.")
        return
    
    file_path = Path(selected_file)
    
    # File viewer header
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col1:
        if st.button(":material/arrow_back: Back", help="Back to chat"):
            st.session_state['show_file_viewer'] = False
            st.rerun()
    
    with col2:
        st.subheader(f":material/description: {file_path.name}")
    
    with col3:
        # Download button in header
        with open(file_path, "rb") as file:
            st.download_button(
                label=":material/download:",
                data=file.read(),
                file_name=file_path.name,
                mime="application/pdf",
                help="Download file"
            )
    
    st.divider()
    
    # Display PDF content
    try:
        # Method 1: Display PDF using st.file_uploader's built-in PDF viewer
        with open(file_path, "rb") as file:
            pdf_data = file.read()
            
        # Show PDF in an iframe-like viewer
        st.markdown("### PDF Content:")
        
        # Create base64 encoded PDF for display
        import base64
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        
        # Embed PDF viewer
        pdf_display = f'''
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            height="800px" 
            type="application/pdf">
        </iframe>
        '''
        
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Fallback: Text extraction
        st.markdown("### Extracted Text (for search and analysis):")
        
        pdf_text = _extract_pdf_text(file_path)
        if pdf_text:
            st.text_area(
                "PDF Content (searchable)", 
                pdf_text, 
                height=300,
                help="This is the text extracted from the PDF for analysis"
            )
        else:
            st.warning("Could not extract text from this PDF.")
            
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        
        # Fallback to text extraction only
        st.markdown("### Text Content:")
        pdf_text = _extract_pdf_text(file_path)
        if pdf_text:
            st.text_area("PDF Content", pdf_text, height=400)

def _extract_pdf_text(file_path: Path) -> str:
    """Extract text content from PDF file."""
    try:
        text_content = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception:
                    continue
        
        if text_content:
            return "\n\n".join(text_content)
        else:
            return "This PDF appears to be image-based or protected. Text extraction is not available.\n\nYou can still download and view the PDF file manually."
        
    except Exception as e:
        return f"Error extracting text: {str(e)}\n\nNote: Some PDFs cannot have their text extracted due to formatting or protection."

def _format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_cv_files_summary() -> Dict[str, Any]:
    """Get summary information about CV files."""
    cv_folder = Path("./data/drive")
    
    if not cv_folder.exists():
        return {"total_files": 0, "total_size": 0, "last_modified": None}
    
    pdf_files = list(cv_folder.glob("*.pdf"))
    
    if not pdf_files:
        return {"total_files": 0, "total_size": 0, "last_modified": None}
    
    total_size = sum(f.stat().st_size for f in pdf_files)
    last_modified = max(f.stat().st_mtime for f in pdf_files)
    
    return {
        "total_files": len(pdf_files),
        "total_size": _format_file_size(total_size),
        "last_modified": datetime.fromtimestamp(last_modified),
        "files": [f.name for f in pdf_files]
    }