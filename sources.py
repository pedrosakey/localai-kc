"""
Sources Browser Module

Provides a comprehensive view of all note sources with a split-pane interface:
- Left pane: List of all source files with metadata
- Right pane: Content viewer for selected source
"""

import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
import frontmatter
import re

# =============================================================================
# DAILY NOTES PROCESSING
# =============================================================================

def is_daily_note(file_path: str) -> bool:
    """
    Check if a file is a daily note (in daily/ folder or follows date pattern).
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        bool: True if it's a daily note
    """
    return (
        'daily/' in file_path or 
        '/daily/' in file_path or
        file_path.startswith('daily/') or
        # Match date patterns like 2025-07-27.md
        bool(re.match(r'.*\d{4}-\d{2}-\d{2}\.md$', file_path))
    )

# =============================================================================
# SOURCE ORGANIZATION AND FILTERING
# =============================================================================

def organize_sources_by_type(notes: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Organize notes by file type and extract unique sources, including daily notes.
    
    Args:
        notes (List[Dict]): List of note chunks with metadata
        
    Returns:
        Dict[str, List[Dict]]: Sources organized by file type
    """
    sources_by_type = {
        'daily': [],      # Special category for daily notes
        'markdown': [],
        'text': [],
        'other': []
    }
    
    # Track unique files to avoid duplicates
    seen_files = set()
    
    for note in notes:
        file_path = note.get('file', '')
        if file_path in seen_files:
            continue
        
        seen_files.add(file_path)
        
        # Check if it's a daily note first
        if is_daily_note(file_path):
            file_type = 'daily'
        # Then determine regular file type
        elif file_path.endswith('.md'):
            file_type = 'markdown'
        elif file_path.endswith('.txt'):
            file_type = 'text'
        else:
            file_type = 'other'
        
        # Create source entry
        source_info = {
            'file': file_path,
            'title': note.get('title', Path(file_path).stem),
            'metadata': note.get('metadata', {}),
            'chunks_count': sum(1 for n in notes if n.get('file') == file_path),
            'tags': note.get('metadata', {}).get('tags', []) if isinstance(note.get('metadata', {}), dict) else [],
            'is_daily': file_type == 'daily'
        }
        
        sources_by_type[file_type].append(source_info)
    
    return sources_by_type

def get_file_stats(notes: List[Dict], file_path: str) -> Dict:
    """
    Get statistics for a specific file.
    
    Args:
        notes (List[Dict]): List of note chunks
        file_path (str): Path to the file
        
    Returns:
        Dict: File statistics
    """
    file_chunks = [note for note in notes if note.get('file') == file_path]
    
    total_chars = sum(len(chunk.get('content', '')) for chunk in file_chunks)
    total_words = sum(len(chunk.get('content', '').split()) for chunk in file_chunks)
    
    return {
        'chunks': len(file_chunks),
        'characters': total_chars,
        'words': total_words,
        'avg_chunk_size': total_chars // len(file_chunks) if file_chunks else 0
    }

# =============================================================================
# CONTENT READING AND DISPLAY
# =============================================================================

def read_full_file_content(file_path: str, notes_folder: str = "./notes") -> Optional[str]:
    """
    Read the full content of a source file.
    
    Args:
        file_path (str): Relative path to the file
        notes_folder (str): Base notes folder path
        
    Returns:
        Optional[str]: Full file content or error message
    """
    try:
        # Debug: Show what we're trying to read
        import os
        current_dir = os.getcwd()
        
        # Normalize paths by removing "./" prefix if present
        clean_notes_folder = notes_folder.lstrip("./")
        
        # Try multiple path combinations to find the file
        possible_paths = [
            Path(notes_folder) / file_path,              # Standard: ./notes/daily/file.md
            Path(clean_notes_folder) / file_path,        # Clean: notes/daily/file.md
            Path(file_path),                             # Direct path: daily/file.md
            Path(".") / file_path,                       # Current directory
            Path(current_dir) / clean_notes_folder / file_path,  # Absolute path
        ]
        
        for full_path in possible_paths:
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith('.md'):
                        # Parse markdown with frontmatter
                        post = frontmatter.load(f)
                        if post.metadata:
                            # Show frontmatter + content
                            frontmatter_text = "---\n"
                            for key, value in post.metadata.items():
                                frontmatter_text += f"{key}: {value}\n"
                            frontmatter_text += "---\n\n"
                            return frontmatter_text + post.content
                        else:
                            return post.content
                    else:
                        return f.read()
        
        # If no file found, return error message with debug info
        debug_info = []
        for p in possible_paths:
            debug_info.append(f"{str(p.resolve())} (exists: {p.exists()})")
        
        return f"File not found. Current dir: {current_dir}, Notes folder: {notes_folder}, File path: {file_path}. Tried: {debug_info}"
        
    except Exception as e:
        return f"Error reading file: {str(e)}"

# =============================================================================
# STREAMLIT SOURCES INTERFACE
# =============================================================================

def render_sources_tab(notes: List[Dict], notes_folder: str = "./notes"):
    """
    Render the sources browser tab with split-pane interface.
    
    Args:
        notes (List[Dict]): List of note chunks with metadata
        notes_folder (str): Path to the notes folder
    """
    st.header("📚 Sources Browser")
    st.markdown("Browse and explore all your note sources")
    
    if not notes:
        st.info("No sources found. Add some .md or .txt files to your notes folder.")
        return
    
    # Organize sources by type
    sources_by_type = organize_sources_by_type(notes)
    
    # Create main layout columns
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        render_sources_sidebar(sources_by_type, notes, notes_folder)
    
    with right_col:
        render_content_viewer(notes, notes_folder)

def render_sources_sidebar(sources_by_type: Dict[str, List[Dict]], notes: List[Dict], notes_folder: str = "./notes"):
    """
    Render the left sidebar with source listings.
    
    Args:
        sources_by_type (Dict): Sources organized by file type
        notes (List[Dict]): Original notes list for statistics
    """
    st.subheader("📋 Source Files")
    
    # Summary statistics
    total_files = sum(len(sources) for sources in sources_by_type.values())
    total_chunks = len(notes)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Files", total_files)
    with col2:
        st.metric("Total Chunks", total_chunks)
    
    # Search/filter functionality
    search_term = st.text_input("🔍 Filter sources", placeholder="Search by filename or tags...")
    
    # File type filter
    selected_types = st.multiselect(
        "📁 File Types",
        options=['daily', 'markdown', 'text', 'other'],
        default=['daily', 'markdown', 'text'],
        format_func=lambda x: f"📅 {x.title()} Notes" if x == 'daily' else f"📝 {x.title()}" if x == 'markdown' else f"📄 {x.title()}" if x == 'text' else f"📋 {x.title()}"
    )
    
    st.markdown("---")
    
    # Display sources by type
    for file_type in selected_types:
        if file_type not in sources_by_type or not sources_by_type[file_type]:
            continue
        
        # Filter sources based on search term
        filtered_sources = sources_by_type[file_type]
        if search_term:
            filtered_sources = [
                source for source in filtered_sources
                if search_term.lower() in source['file'].lower() or
                   search_term.lower() in source['title'].lower() or
                   any(search_term.lower() in str(tag).lower() for tag in source.get('tags', []))
            ]
        
        if not filtered_sources:
            continue
        
        # Section header
        icon = "📅" if file_type == 'daily' else "📝" if file_type == 'markdown' else "📄" if file_type == 'text' else "📋"
        section_title = f"Daily Notes" if file_type == 'daily' else f"{file_type.title()} Files"
        st.markdown(f"### {icon} {section_title} ({len(filtered_sources)})")
        
        # Display each source
        for source in filtered_sources:
            with st.container():
                # Special handling for daily notes
                if file_type == 'daily':
                    render_daily_note_item(source, notes, notes_folder)
                else:
                    render_regular_note_item(source)
                
                st.markdown("---")

def render_daily_note_item(source: Dict, all_notes: List[Dict], notes_folder: str = "./notes"):
    """
    Render a daily note item.
    
    Args:
        source (Dict): Source information
        all_notes (List[Dict]): All available notes
    """
    # Create clickable source item
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # File selection button with date indicator
        display_name = source['title']
        if st.button(
            f"📅 {display_name}", 
            key=f"select_{source['file']}",
            help=f"Click to view {source['file']}"
        ):
            st.session_state.selected_source = source['file']
    
    with col2:
        st.caption(f"{source['chunks_count']} chunks")
    
    # Show metadata if available
    metadata = source.get('metadata', {})
    if metadata:
        meta_items = []
        for key, value in list(metadata.items())[:2]:  # Show first 2 metadata items
            if key not in ['tags'] and value:
                meta_items.append(f"`{key}: {value}`")
        if meta_items:
            st.caption(" ".join(meta_items))

def render_regular_note_item(source: Dict):
    """
    Render a regular note item.
    
    Args:
        source (Dict): Source information
    """
    # Create clickable source item
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # File selection button
        if st.button(
            f"📄 {source['title']}", 
            key=f"select_{source['file']}",
            help=f"Click to view {source['file']}"
        ):
            st.session_state.selected_source = source['file']
    
    with col2:
        st.caption(f"{source['chunks_count']} chunks")
    
    # Show tags if available
    if source.get('tags'):
        tags_text = " ".join([f"`{tag}`" for tag in source['tags'][:3]])
        if len(source['tags']) > 3:
            tags_text += f" +{len(source['tags']) - 3} more"
        st.caption(tags_text)



def render_content_viewer(notes: List[Dict], notes_folder: str):
    """
    Render the right panel content viewer.
    
    Args:
        notes (List[Dict]): List of note chunks
        notes_folder (str): Path to the notes folder
    """
    st.subheader("📖 Content Viewer")
    
    # Check if a source is selected
    if 'selected_source' not in st.session_state:
        st.info("👈 Select a source file from the left panel to view its content")
        return
    
    selected_file = st.session_state.selected_source
    
    # Display file header
    st.markdown(f"### 📄 {selected_file}")
    
    # Get file statistics
    file_stats = get_file_stats(notes, selected_file)
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Chunks", file_stats['chunks'])
    with col2:
        st.metric("Words", f"{file_stats['words']:,}")
    with col3:
        st.metric("Characters", f"{file_stats['characters']:,}")
    with col4:
        st.metric("Avg Chunk", f"{file_stats['avg_chunk_size']}")
    
    # Content display options
    view_mode = st.selectbox(
        "View Mode",
        ["Full Content", "Chunks Only", "Metadata Only"],
        help="Choose how to display the file content"
    )
    
    if view_mode == "Full Content":
        # Read and display full file content
        content = read_full_file_content(selected_file, notes_folder)
        if content and not content.startswith("Error") and not content.startswith("File not found"):
            st.markdown("#### 📖 Full File Content")
            if selected_file.endswith('.md'):
                st.markdown(content)
            else:
                st.text(content)
        else:
            st.error(f"Could not read file content: {content}")

    elif view_mode == "Chunks Only":
        # Display individual chunks
        file_chunks = [note for note in notes if note.get('file') == selected_file]
        st.markdown(f"#### 🧩 File Chunks ({len(file_chunks)})")
        
        for i, chunk in enumerate(file_chunks, 1):
            with st.expander(f"Chunk {i} - {len(chunk.get('content', ''))} chars", expanded=i == 1):
                if chunk.get('heading'):
                    st.markdown(f"**Section:** {chunk['heading']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if chunk.get('start_line'):
                        st.markdown(f"**Lines:** {chunk['start_line']}-{chunk.get('end_line', 'N/A')}")
                with col2:
                    if chunk.get('token_count'):
                        st.markdown(f"**Tokens:** {chunk['token_count']}")
                
                st.markdown("**Content:**")
                st.markdown(f"```\n{chunk['content']}\n```")
    
    elif view_mode == "Metadata Only":
        # Display file metadata
        file_chunks = [note for note in notes if note.get('file') == selected_file]
        if file_chunks and file_chunks[0].get('metadata'):
            st.markdown("#### ℹ️ File Metadata")
            metadata = file_chunks[0]['metadata']
            
            for key, value in metadata.items():
                st.markdown(f"**{key.title()}:** {value}")
        else:
            st.info("No metadata found for this file")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search in this file"):
            # Set up search query for this specific file
            if 'search_query' not in st.session_state:
                st.session_state.search_query = ""
            st.session_state.search_query = f"file:{selected_file}"
            st.info("Switch to Search tab to search within this file")
    
    with col2:
        if st.button("💬 Chat about this file"):
            # Add a chat message about this file
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({
                "role": "user", 
                "content": f"Tell me about the file {selected_file}"
            })
            st.info("Switch to Chat tab to see the response")
    
    with col3:
        if st.button("📊 File Analytics"):
            # Show detailed analytics
            show_file_analytics(notes, selected_file)

def show_file_analytics(notes: List[Dict], file_path: str):
    """
    Show detailed analytics for a file.
    
    Args:
        notes (List[Dict]): List of note chunks
        file_path (str): Path to the file
    """
    file_chunks = [note for note in notes if note.get('file') == file_path]
    
    st.markdown("#### 📊 File Analytics")
    
    # Chunk size distribution
    chunk_sizes = [len(chunk.get('content', '')) for chunk in file_chunks]
    
    if chunk_sizes:
        import pandas as pd
        
        # Create chunk size chart
        chart_data = pd.DataFrame({
            'Chunk': [f"Chunk {i+1}" for i in range(len(chunk_sizes))],
            'Size': chunk_sizes
        })
        
        st.bar_chart(chart_data.set_index('Chunk')['Size'])
        
        # Additional statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Min Chunk Size", min(chunk_sizes))
            st.metric("Max Chunk Size", max(chunk_sizes))
        with col2:
            st.metric("Median Chunk Size", sorted(chunk_sizes)[len(chunk_sizes)//2])
            st.metric("Std Deviation", f"{(sum((x - sum(chunk_sizes)/len(chunk_sizes))**2 for x in chunk_sizes) / len(chunk_sizes))**0.5:.1f}") 