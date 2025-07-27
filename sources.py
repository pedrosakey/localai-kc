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
    
    # Create three-column layout: Sources | Content Viewer | Linked Viewer
    left_col, middle_col, right_col = st.columns([1, 1.5, 1.5])
    
    with left_col:
        render_sources_sidebar(sources_by_type, notes, notes_folder)
    
    with middle_col:
        render_content_viewer(notes, notes_folder)
    
    with right_col:
        render_linked_viewer(notes, notes_folder)

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
        default=['daily'],
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
            
            # Render content with clickable wikilink buttons
            render_content_with_wikilink_buttons(content, notes, selected_file)
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

# =============================================================================
# WIKILINK PROCESSING AND LINKED VIEWER
# =============================================================================

def extract_wikilinks(content: str) -> List[str]:
    """
    Extract wikilinks from content in [[...]] format.
    
    Args:
        content (str): Text content to parse
        
    Returns:
        List[str]: List of wikilink references (without brackets)
    """
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(pattern, content)
    return matches

def resolve_wikilink(wikilink: str, notes: List[Dict]) -> Optional[str]:
    """
    Resolve a wikilink to an actual file path.
    
    Args:
        wikilink (str): Wikilink text to resolve
        notes (List[Dict]): All available notes
        
    Returns:
        Optional[str]: File path if found, None otherwise
    """
    wikilink_lower = wikilink.lower()
    
    # Try exact matches first
    for note in notes:
        file_path = note.get('file', '')
        file_stem = Path(file_path).stem.lower()
        
        # Direct stem match
        if file_stem == wikilink_lower:
            return file_path
            
        # Title match from metadata
        if note.get('metadata', {}).get('title', '').lower() == wikilink_lower:
            return file_path
    
    # Try partial matches
    for note in notes:
        file_path = note.get('file', '')
        file_stem = Path(file_path).stem.lower()
        
        # Partial stem match
        if wikilink_lower in file_stem or file_stem in wikilink_lower:
            return file_path
    
    return None

def render_linked_viewer(notes: List[Dict], notes_folder: str):
    """
    Render the linked content viewer that shows content only when a wikilink is clicked.
    
    Args:
        notes (List[Dict]): List of note chunks
        notes_folder (str): Path to the notes folder
    """
    st.subheader("🔗 Linked Viewer")
    
    # Check if a wikilink has been clicked
    if 'selected_wikilink' not in st.session_state:
        st.info("👈 Click on a wikilink in the Content Viewer to see linked content here")
        return
    
    # Get the selected wikilink info
    selected_wikilink = st.session_state.selected_wikilink
    
    # Show clear button to close linked viewer
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Showing:** `{selected_wikilink}`")
    with col2:
        if st.button("✖️", key="close_linked_viewer", help="Close linked viewer"):
            del st.session_state.selected_wikilink
            if 'wikilink_context' in st.session_state:
                del st.session_state.wikilink_context
            st.rerun()
    
    # Show context if available (from daily notes)
    if 'wikilink_context' in st.session_state:
        context = st.session_state.wikilink_context
        st.markdown("### 📝 Contexto de la referencia")
        
        # Show the daily note entry that referenced this wikilink
        st.markdown(f"**⏰ {context['time']} - {context['description']}**")
        
        # Show metadata
        meta_info = []
        if context.get('status'):
            meta_info.append(f"Status: {context['status']}")
        if context.get('area'):
            meta_info.append(f"Área: {context['area']}")
        if context.get('date'):
            meta_info.append(f"Fecha: {context['date']}")
        
        if meta_info:
            st.caption(" | ".join(meta_info))
        
        # Show the full content with audio/photo descriptions
        if context.get('content'):
            with st.expander("📄 Contenido completo de la entrada", expanded=True):
                st.markdown(context['content'])
        
        st.markdown("---")
    
    # Resolve wikilink to file path
    resolved_path = resolve_wikilink(selected_wikilink, notes)
    
    if not resolved_path:
        st.error(f"❌ Could not find file for: `{selected_wikilink}`")
        
        # Show suggestions for similar files
        st.markdown("**Suggestions:**")
        similar_files = []
        for note in notes[:5]:
            file_name = Path(note.get('file', '')).stem.lower()
            if selected_wikilink.lower() in file_name:
                similar_files.append(note.get('file', ''))
        
        if similar_files:
            for similar_file in similar_files:
                if st.button(f"📄 {similar_file}", key=f"similar_{similar_file}"):
                    st.session_state.selected_source = similar_file
                    del st.session_state.selected_wikilink  # Clear wikilink selection
                    st.rerun()
        else:
            st.info("No similar files found")
        return
    
    # Display the linked file content
    st.markdown(f"### 📄 Contenido del archivo: `{selected_wikilink}`")
    render_linked_file_content(resolved_path, notes_folder, selected_wikilink)

def render_linked_file_content(file_path: str, notes_folder: str, wikilink_name: str):
    """
    Render the content of a linked file.
    
    Args:
        file_path (str): Path to the linked file
        notes_folder (str): Base notes folder
        wikilink_name (str): Original wikilink name for display
    """
    # Content display mode
    col1, col2 = st.columns([3, 1])
    
    with col1:
        display_mode = st.selectbox(
            "Modo de visualización:",
            ["Preview", "Contenido completo"],
            key="linked_viewer_mode",
            help="Elige cómo mostrar el contenido del archivo"
        )
    
    with col2:
        # Check if this is an audio or photo file content
        is_audio_photo = (
            "🔊" in wikilink_name or 
            "audio" in wikilink_name.lower() or
            "foto" in wikilink_name.lower() or
            "photo" in wikilink_name.lower() or
            "imagen" in wikilink_name.lower() or
            "📷" in wikilink_name or
            "📸" in wikilink_name
        )
        
        if is_audio_photo:
            if st.button(
                "🤖 Describir con IA", 
                key="describe_with_ai",
                help="Generar descripción con inteligencia artificial",
                use_container_width=True
            ):
                # Fake AI description functionality
                import os
                import datetime
                
                # Generate fake AI description based on content type
                if "🔊" in wikilink_name or "audio" in wikilink_name.lower():
                    fake_ai_description = f"""

---

## 🤖 Descripción generada por IA - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

Notas personales del análisis de métricas: Después de revisar los últimos resultados del modelo de Whisper AI, puedo confirmar que hemos logrado un Word Error Rate de 2.8% en condiciones de laboratorio, lo cual representa una mejora significativa desde el 4.1% anterior. Las métricas de precisión muestran que estamos alcanzando 94.2% de accuracy en acentos mexicanos y 89% en el modelo de detección de emociones. La latencia promedio es de 180ms lo cual está por debajo de nuestro objetivo de 200ms. Estos números indican que el proyecto está listo para la siguiente fase de testing con usuarios reales.
"""
                else:  # Photo/image content
                    # Check if this is the specific testing photo file
                    if "testing_29_07_foto" in wikilink_name.lower():
                        fake_ai_description = f"""

---

## 🤖 Descripción generada por IA - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

---
title: "Resultados de Testing con Usuarios Reales"
date: 2025-07-29
type: "photo-documentation"
context: "user-testing-session-results"
---

# 📷 Resultados de Sesiones de Testing con Usuarios Reales

## Documentación Visual de Resultados Obtenidos

Esta fotografía captura **los resultados finales de nuestras sesiones de testing con usuarios reales** del sistema de reconocimiento de voz IA. La imagen muestra la pantalla principal donde se desplegaron todos los datos obtenidos durante las pruebas con participantes reales.

### Resultados Visualizados en Pantalla:

**📊 Métricas de Rendimiento Obtenidas:**
- **Accuracy Final**: 94.2% en reconocimiento de español mexicano (visible en gráfico principal)
- **Word Error Rate**: 2.8% mostrado en el dashboard de resultados  
- **Latencia Promedio**: 165ms documentada en tiempo real
- **Detección Emocional**: 89% de precisión en identificación de estados

**👥 Resultados por Usuario:**
La pantalla muestra los resultados individuales de los **3 usuarios reales** que participaron:
- Usuario 1: 96% accuracy, latencia 150ms
- Usuario 2: 93% accuracy, latencia 170ms  
- Usuario 3: 94% accuracy, latencia 175ms
"""
                    else:
                        # Generic photo description for other photo files
                        fake_ai_description = f"""

---

## 🤖 Descripción generada por IA - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

**Análisis de Imagen Automático:**

Esta imagen muestra una sesión de testing de interfaz de usuario con elementos relacionados al desarrollo de software:

- **Contenido visual**: Pantallas de aplicación, interfaces de usuario, métricas en pantalla
- **Contexto técnico**: Sesión de pruebas de usabilidad y evaluación de performance
- **Elementos destacados**: Gráficos de rendimiento, dashboards de métricas, resultados de testing
- **Ambiente**: Entorno de desarrollo/testing profesional

**Objetos detectados**: Pantallas, gráficos, métricas, interfaces, dashboards
**Tipo de imagen**: Screenshot/Captura de testing
**Calidad**: Alta resolución técnica
"""
                
                try:
                    # Read current file content
                    full_path = os.path.join(notes_folder, file_path)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    # Check if AI description already exists
                    if "🤖 Descripción generada por IA" not in current_content:
                        # Append the fake AI description
                        updated_content = current_content + fake_ai_description
                        
                        # Write back to file
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        
                        st.success("✅ Descripción IA agregada exitosamente")
                        st.info("🔄 Recargando contenido para búsqueda...")
                        
                        # Clear cached data and force rerun to reload content
                        st.cache_data.clear()  # Clear cached data to force reload
                        st.rerun()             # Restart the app
                    else:
                        st.warning("⚠️ Ya existe una descripción IA para este archivo")
                        
                except Exception as e:
                    st.error(f"❌ Error al agregar descripción IA: {str(e)}")
    
    # Read file content
    content = read_full_file_content(file_path, notes_folder)
    
    if not content or content.startswith("Error") or content.startswith("File not found"):
        st.warning("📄 empty")
        return
    
    # Check if file is empty
    if content.strip() == "":
        st.warning("📄 empty file")
        return
    
    if display_mode == "Preview":
        # Show first 500 characters as preview
        preview = content[:500]
        if len(content) > 500:
            preview += "..."
        
        if file_path.endswith('.md'):
            st.markdown(preview)
        else:
            st.text(preview)
            
        if len(content) > 500:
            st.caption(f"Mostrando los primeros 500 de {len(content)} caracteres")
    
    else:  # Contenido completo
        if file_path.endswith('.md'):
            st.markdown(content)
        else:
            st.text(content)
    
    # Check for nested wikilinks
    nested_links = extract_wikilinks(content)
    if nested_links:
        st.markdown("---")
        st.markdown(f"**🔗 Enlaces en este archivo ({len(nested_links)}):**")
        
        # Show up to 5 nested links
        for i, nested_link in enumerate(nested_links[:5]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• `{nested_link}`")
            with col2:
                if st.button("→", key=f"nested_link_{i}_{nested_link}", help=f"Seguir {nested_link}"):
                    # Resolve and display nested link
                    nested_path = resolve_wikilink(nested_link, notes)
                    if nested_path:
                        st.session_state.selected_source = nested_path
                        st.rerun()
        
        if len(nested_links) > 5:
            st.caption(f"+ {len(nested_links) - 5} enlaces más...")

def render_content_with_wikilink_buttons(content: str, notes: List[Dict], source_file: str):
    """
    Render content with inline clickable wikilinks and improved daily note formatting.
    
    Args:
        content (str): Original content with wikilinks
        notes (List[Dict]): All notes for resolution
        source_file (str): Source file path for unique keys
    """
    import re
    
    # Check if this is a daily note for special formatting
    is_daily = is_daily_note(source_file)
    
    if is_daily:
        render_daily_note_content(content, notes, source_file)
    else:
        render_regular_content_with_inline_wikilinks(content, notes, source_file)

def render_daily_note_content(content: str, notes: List[Dict], source_file: str):
    """
    Render daily note content with special formatting for entries.
    """
    import re
    
    lines = content.split('\n')
    current_entry = {}
    entry_count = 0
    in_separator = False
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('#'):
            if line.startswith('#'):
                st.markdown(line)
            continue
        
        # Check for separator (---)
        if line == '---':
            # Render previous entry if exists
            if current_entry:
                render_daily_entry_card(current_entry, notes, source_file, entry_count)
                entry_count += 1
                current_entry = {}
            in_separator = True
            continue
        
        # Check for time-based entry (e.g., "18:11 captura dia 5")
        time_match = re.match(r'^(\d{1,2}:\d{2})\s+(.*)$', line)
        if time_match:
            # Render previous entry if exists
            if current_entry:
                render_daily_entry_card(current_entry, notes, source_file, entry_count)
                entry_count += 1
            
            # Start new entry
            current_entry = {
                'time': time_match.group(1),
                'description': time_match.group(2),
                'status': '',
                'area': '',
                'date': '',
                'wikilinks': [],
                'content_lines': [],  # For full content
                'raw_lines': [original_line]
            }
            in_separator = False
            continue
        
        # Process content for current entry
        if current_entry and not in_separator:
            current_entry['raw_lines'].append(original_line)
            
            if line.startswith('status::'):
                current_entry['status'] = line.replace('status::', '').strip()
            elif line.startswith('area::'):
                current_entry['area'] = line.replace('area::', '').strip()
            elif line.startswith('date::'):
                current_entry['date'] = line.replace('date::', '').strip()
            else:
                # This is content (including audio/photo descriptions)
                current_entry['content_lines'].append(original_line)
                
                # Extract wikilinks from any content line
                if '[[' in line and ']]' in line:
                    wikilinks = extract_wikilinks(line)
                    current_entry['wikilinks'].extend(wikilinks)
    
    # Render last entry
    if current_entry:
        render_daily_entry_card(current_entry, notes, source_file, entry_count)

def render_daily_entry_card(entry: Dict, notes: List[Dict], source_file: str, entry_count: int):
    """
    Render a daily entry as a card with proper formatting.
    """
    with st.container():
        # Create a card-like container
        st.markdown("""
        <div style="
            border: 1px solid #e0e0e0; 
            border-radius: 8px; 
            padding: 16px; 
            margin: 8px 0; 
            background-color: #fafafa;
        ">
        """, unsafe_allow_html=True)
        
        # Header with time and description
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### ⏰ {entry['time']} - {entry['description']}")
        
        with col2:
            status = entry.get('status', '')
            if status:
                if status == 'Not Processed':
                    st.markdown("🔴 **Not Processed**")
                elif status == 'Processed':
                    st.markdown("🟢 **Processed**")
                elif status == 'In Progress':
                    st.markdown("🟡 **In Progress**")
                else:
                    st.markdown(f"⚪ **{status}**")
        
        with col3:
            area = entry.get('area', '')
            if area:
                st.markdown(f"📂 **{area}**")
        
        # Date if available
        date = entry.get('date', '')
        if date:
            st.caption(f"📅 {date}")
        
        # Show full content including audio/photo descriptions
        content_lines = entry.get('content_lines', [])
        if content_lines:
            st.markdown("---")
            full_content = '\n'.join(content_lines)
            
            # Process the content to make wikilinks clickable but show everything
            processed_content = process_daily_content_with_wikilinks(full_content, notes, source_file, entry_count)
            st.markdown(processed_content, unsafe_allow_html=True)
        
        # Store entry context for linked viewer
        entry_context = {
            'time': entry['time'],
            'description': entry['description'],
            'status': entry.get('status', ''),
            'area': entry.get('area', ''),
            'date': entry.get('date', ''),
            'content': '\n'.join(content_lines),
            'source_file': source_file
        }
        
        # Render wikilinks as buttons with context
        if entry.get('wikilinks'):
            st.markdown("---")
            st.markdown("**🔗 Referencias:**")
            for i, wikilink in enumerate(entry['wikilinks']):
                resolved_path = resolve_wikilink(wikilink, notes)
                button_key = f"daily_wikilink_{source_file}_{entry_count}_{i}_{wikilink}".replace("/", "_").replace(".", "_").replace(" ", "_")
                
                if resolved_path:
                    if st.button(
                        f"📄 {wikilink}",
                        key=button_key,
                        help=f"Click to view {wikilink} with context in Linked Viewer"
                    ):
                        # Store both the wikilink and its context
                        st.session_state.selected_wikilink = wikilink
                        st.session_state.wikilink_context = entry_context
                        st.rerun()
                else:
                    st.markdown(f"❌ {wikilink} (not found)")
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_regular_content_with_inline_wikilinks(content: str, notes: List[Dict], source_file: str):
    """
    Render regular content with styled wikilinks and clickable buttons.
    """
    import re
    
    # Find all wikilinks in content
    wikilinks = extract_wikilinks(content)
    
    # Split content by lines to process wikilinks
    lines = content.split('\n')
    processed_lines = []
    
    for line_num, line in enumerate(lines):
        if '[[' in line and ']]' in line:
            # Process line with wikilinks
            processed_line = process_line_with_inline_wikilinks(line, notes, source_file, line_num)
            processed_lines.append(processed_line)
        else:
            processed_lines.append(line)
    
    # Join and display the content
    processed_content = '\n'.join(processed_lines)
    
    if source_file.endswith('.md'):
        st.markdown(processed_content, unsafe_allow_html=True)
    else:
        st.text(processed_content)
    
    # Add clickable wikilink buttons below content (only if wikilinks exist)
    if wikilinks:
        st.markdown("---")
        st.markdown("**🔗 Links in this content:**")
        cols = st.columns(min(len(wikilinks), 3))  # Max 3 columns
        
        for i, wikilink in enumerate(wikilinks):
            col_index = i % 3
            with cols[col_index]:
                resolved_path = resolve_wikilink(wikilink, notes)
                button_key = f"regular_wikilink_{source_file}_{i}_{wikilink}".replace("/", "_").replace(".", "_").replace(" ", "_")
                
                if resolved_path:
                    if st.button(
                        f"🔗 {wikilink}",
                        key=button_key,
                        help=f"Click to view {wikilink} in Linked Viewer",
                        use_container_width=True
                    ):
                        st.session_state.selected_wikilink = wikilink
                        st.rerun()

def process_line_with_inline_wikilinks(line: str, notes: List[Dict], source_file: str, line_num: int) -> str:
    """
    Process a line to style wikilinks (actual clicking handled separately).
    """
    import re
    
    def replace_wikilink(match):
        wikilink_text = match.group(1)
        resolved_path = resolve_wikilink(wikilink_text, notes)
        
        if resolved_path:
            # Style valid wikilinks
            return f'<span style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border: 1px solid #1976d2; border-radius: 6px; padding: 4px 8px; color: #1976d2; font-weight: 500; margin: 0 2px; display: inline-block;">🔗 {wikilink_text}</span>'
        else:
            # Style broken wikilinks
            return f'<span style="background-color: #ffebee; padding: 4px 8px; border-radius: 6px; border: 1px solid #d32f2f; color: #d32f2f; margin: 0 2px; display: inline-block;">❌ {wikilink_text}</span>'
    
    # Replace wikilinks with styled elements
    pattern = r'\[\[([^\]]+)\]\]'
    processed_line = re.sub(pattern, replace_wikilink, line)
    
    return processed_line 

def process_daily_content_with_wikilinks(content: str, notes: List[Dict], source_file: str, entry_count: int) -> str:
    """
    Process daily note content to make wikilinks clickable while preserving formatting.
    """
    import re
    
    def replace_wikilink(match):
        wikilink_text = match.group(1)
        resolved_path = resolve_wikilink(wikilink_text, notes)
        
        if resolved_path:
            # Make it clickable and styled - but since we can't make it truly clickable in markdown,
            # we'll style it to show it's a link
            return f'<span style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border: 1px solid #1976d2; border-radius: 6px; padding: 4px 8px; color: #1976d2; font-weight: 500; margin: 0 2px; display: inline-block; cursor: pointer;">🔗 {wikilink_text}</span>'
        else:
            return f'<span style="background-color: #ffebee; padding: 4px 8px; border-radius: 6px; border: 1px solid #d32f2f; color: #d32f2f; margin: 0 2px; display: inline-block;">❌ {wikilink_text}</span>'
    
    # Replace wikilinks with styled spans
    pattern = r'\[\[([^\]]+)\]\]'
    processed_content = re.sub(pattern, replace_wikilink, content)
    
    return processed_content 