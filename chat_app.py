"""
Chat with My Notes - A Local RAG Application

A Streamlit app for chatting with your local notes using:
- Ollama for local LLM inference (gemma3n:4b by default)
- Sentence Transformers for local embeddings
- Vector similarity search for relevant note retrieval
- Support for Markdown (.md) and text (.txt) files
"""

import streamlit as st
import ollama
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import frontmatter
import re
from typing import List, Dict, Tuple
import search  # Import our search module
import sources as sources_module  # Import our sources browser module

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Model configurations - change these to use different models
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Fast, lightweight embedding model
OLLAMA_MODEL = "gemma3n:e4b"            # Fixed LLM for chat responses

# =============================================================================
# CACHING AND MODEL LOADING
# =============================================================================

@st.cache_resource
def load_embedding_model():
    """
    Load the sentence transformer model for creating embeddings.
    
    Uses Streamlit caching to avoid reloading the model on every run.
    The model is loaded once and reused across sessions.
    
    Returns:
        SentenceTransformer: Loaded embedding model
    """
    return SentenceTransformer(EMBEDDING_MODEL)

# =============================================================================
# DOCUMENT PROCESSING AND LOADING
# =============================================================================

@st.cache_data
def load_notes(notes_folder: str):
    """
    Load and process all notes from the specified folder.
    
    Recursively scans the folder for .md and .txt files, processes them
    into chunks, and extracts metadata from frontmatter (for .md files).
    
    Args:
        notes_folder (str): Path to the folder containing notes
        
    Returns:
        List[Dict]: List of note chunks with metadata
    """
    notes = []
    notes_path = Path(notes_folder)
    
    # Check if the notes folder exists
    if not notes_path.exists():
        return []
    
    # Supported file extensions for note files
    extensions = ['.md', '.txt']
    
    # Process each supported file type
    for ext in extensions:
        # Recursively find all files with this extension
        for file_path in notes_path.rglob(f'*{ext}'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if ext == '.md':
                        # Parse markdown files with frontmatter support
                        post = frontmatter.load(f)
                        content = post.content      # Main content without frontmatter
                        metadata = post.metadata    # YAML frontmatter as dict
                    else:
                        # Plain text files - no frontmatter
                        content = f.read()
                        metadata = {}
                
                # Split content into manageable chunks
                chunks = chunk_text(content, file_path.name)
                
                # Create a note entry for each chunk
                for i, chunk in enumerate(chunks):
                    notes.append({
                        'file': str(file_path.relative_to(notes_path)),  # Relative path
                        'title': metadata.get('title', file_path.stem),  # Title from frontmatter or filename
                        'content': chunk,                                 # Text content of this chunk
                        'chunk_id': i,                                   # Index of chunk within document
                        'metadata': metadata                             # Full frontmatter metadata
                    })
                        
            except Exception as e:
                # Display error in Streamlit UI if file can't be loaded
                st.error(f"Error loading {file_path}: {str(e)}")
    
    return notes

# =============================================================================
# TEXT CHUNKING
# =============================================================================

def chunk_text(text: str, filename: str, max_length: int = 1000) -> List[str]:
    """
    Split text into smaller chunks with overlap for better context preservation.
    
    Splits text by paragraphs and markdown headers, ensuring chunks don't exceed
    max_length while maintaining some overlap between chunks to preserve context.
    
    Args:
        text (str): The text content to chunk
        filename (str): Name of the source file (for debugging)
        max_length (int): Maximum character length per chunk
        
    Returns:
        List[str]: List of text chunks
    """
    # Split by double newlines (paragraphs) or markdown headers (# ## ###)
    paragraphs = re.split(r'\n\s*\n|(?=^#{1,6}\s)', text, flags=re.MULTILINE)
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Check if adding this paragraph would exceed max_length
        if len(current_chunk) + len(para) > max_length and current_chunk:
            # Save the current chunk
            chunks.append(current_chunk.strip())
            
            # Start new chunk with some overlap (last sentence for context)
            sentences = current_chunk.split('.')
            if len(sentences) > 1:
                # Include last sentence from previous chunk for context
                current_chunk = sentences[-1] + '. ' + para
            else:
                # If no sentences to overlap, start fresh
                current_chunk = para
        else:
            # Add paragraph to current chunk
            current_chunk += '\n\n' + para if current_chunk else para
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Return chunks or original text if no splits were made
    return chunks if chunks else [text]

# =============================================================================
# EMBEDDING CREATION
# =============================================================================

@st.cache_data
def create_embeddings(_model, notes):
    """
    Create vector embeddings for all note chunks using the sentence transformer.
    
    Uses Streamlit caching to avoid recreating embeddings unnecessarily.
    The embeddings are created once and reused until notes are reloaded.
    
    Args:
        _model: The sentence transformer model (prefixed with _ for Streamlit caching)
        notes (List[Dict]): List of note chunks with content
        
    Returns:
        Tuple[np.ndarray, List[Dict]]: Embeddings matrix and original notes
    """
    if not notes:
        return np.array([]), []
    
    # Extract text content from all note chunks
    texts = [note['content'] for note in notes]
    
    # Create embeddings for all texts at once (more efficient than one-by-one)
    embeddings = _model.encode(texts)
    
    return embeddings, notes

# =============================================================================
# SEMANTIC SEARCH
# =============================================================================

def search_notes(query: str, embeddings: np.ndarray, notes: List[Dict], model, top_k: int = 5) -> List[Dict]:
    """
    Search for relevant notes using vector similarity.
    
    Encodes the user query and finds the most similar note chunks using
    cosine similarity between embeddings.
    
    Args:
        query (str): User's search query
        embeddings (np.ndarray): Pre-computed embeddings for all notes
        notes (List[Dict]): List of note chunks with metadata
        model: Sentence transformer model for encoding the query
        top_k (int): Maximum number of results to return
        
    Returns:
        List[Dict]: Most relevant note chunks with similarity scores
    """
    if len(notes) == 0:
        return []
    
    # Convert query to embedding vector
    query_embedding = model.encode([query])
    
    # Calculate cosine similarity between query and all note embeddings
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Get indices of top k most similar notes (sorted by similarity)
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        # Only include results above minimum similarity threshold
        if similarities[idx] > 0.1:  # Threshold to filter out very poor matches
            note = notes[idx].copy()
            note['similarity'] = similarities[idx]  # Add similarity score
            results.append(note)
    
    return results

# =============================================================================
# LLM INTERACTION
# =============================================================================

def query_ollama(prompt: str, model_name: str = OLLAMA_MODEL) -> str:
    """
    Send a prompt to Ollama and get the response.
    
    Communicates with the local Ollama server to get AI responses.
    Handles errors gracefully if Ollama is not running or model is unavailable.
    
    Args:
        prompt (str): The complete prompt to send to the LLM
        model_name (str): Name of the Ollama model to use
        
    Returns:
        str: The LLM's response or error message
    """
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            stream=False  # Get complete response at once (not streamed)
        )
        return response['message']['content']
    except Exception as e:
        return f"Error querying Ollama: {str(e)}"

# =============================================================================
# RAG PROMPT CONSTRUCTION
# =============================================================================

def create_rag_prompt(question: str, relevant_notes: List[Dict]) -> str:
    """
    Create a Retrieval-Augmented Generation (RAG) prompt.
    
    Combines the user's question with relevant note content to provide
    context for the LLM to generate accurate, grounded responses.
    
    Args:
        question (str): User's original question
        relevant_notes (List[Dict]): Most relevant note chunks from search
        
    Returns:
        str: Complete prompt with instructions, context, and question
    """
    # Build context section with all relevant notes
    context = ""
    for i, note in enumerate(relevant_notes, 1):
        context += f"\n\n--- Source {i}: {note['file']} ---\n"
        context += note['content']
        if note.get('similarity'):
            context += f"\n(Relevance: {note['similarity']:.2f})"
    
    # Create the complete RAG prompt with instructions
    prompt = f"""You are a helpful assistant that answers questions based on the provided notes. 
Answer the question using only the information from the sources below. If you cannot find the answer in the provided sources, say so clearly.
Answer in Spanish always even if doc is in Spanish.
Question: {question}

Sources:{context}

Answer based on the sources above:"""
    
    return prompt

# =============================================================================
# STREAMLIT USER INTERFACE
# =============================================================================

def main():
    """
    Main Streamlit application function.
    
    Sets up the UI, handles user interactions, and orchestrates the RAG pipeline:
    1. Configuration sidebar
    2. Document loading and processing  
    3. Chat interface with message history
    4. Search and response generation
    """
    # =========================
    # STREAMLIT PAGE CONFIGURATION
    # =========================
    st.set_page_config(
        page_title="Chat with My Notes",
        page_icon="📝",
        layout="wide",                     # Use full width of the browser
        initial_sidebar_state="expanded"   # Show sidebar by default
    )
    
    # =========================
    # PAGE HEADER
    # =========================
    st.title("📝 Chat with My Notes")
    st.markdown("Ask questions about your local notes using AI")
    
    # =========================
    # SIDEBAR CONFIGURATION
    # =========================
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Notes folder path input
        notes_folder = st.text_input(
            "Notes Folder Path",
            value="./notes",
            help="Path to your local notes folder"
        )
        
        # Model information
        st.markdown(f"**🤖 LLM Model:** {OLLAMA_MODEL}")
        st.markdown(f"**🔍 Embedding Model:** {EMBEDDING_MODEL}")
        
        # Search configuration
        top_k = st.slider("Number of relevant notes", 1, 10, 3)
        
        st.markdown("---")
        
        # Manual reload button
        if st.button("🔄 Load/Reload Notes"):
            st.cache_data.clear()  # Clear cached data to force reload
            st.rerun()             # Restart the app
    
    # =========================
    # SESSION STATE INITIALIZATION
    # =========================
    # Initialize chat history in session state (persists across reruns)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # =========================
    # MODEL AND DATA LOADING
    # =========================
    # Load embedding model (cached - only loads once)
    with st.spinner("Loading embedding model..."):
        embedding_model = load_embedding_model()
    
    # Load and process notes from folder (cached until folder changes)
    with st.spinner("Loading notes..."):
        notes = load_notes(notes_folder)
    
    # Check if any notes were found
    if not notes:
        st.warning(f"No notes found in '{notes_folder}'. Please check the path and add some .md or .txt files.")
        return
    
    # Create embeddings for all note chunks (cached until notes change)
    with st.spinner("Creating embeddings..."):
        embeddings, processed_notes = create_embeddings(embedding_model, notes)
    
    # Display statistics in sidebar
    st.sidebar.markdown(f"**📊 Loaded {len(processed_notes)} note chunks**")
    
    # =========================
    # MAIN INTERFACE WITH TABS
    # =========================
    # Create tabs for different functionality
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🔍 Search & Summarize", "📚 Sources"])
    
    with tab1:
        # =========================
        # CHAT INTERFACE
        # =========================
        st.header("💬 Chat")
        
        # Display existing chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show sources for assistant messages
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📎 Sources", expanded=False):
                        for source in message["sources"]:
                            st.markdown(f"**{source['file']}** (Relevance: {source['similarity']:.2f})")
                            st.markdown(f"```\n{source['content'][:300]}...\n```")

    with tab2:
        # =========================
        # SEARCH AND SUMMARIZATION TAB
        # =========================
        # Render the search interface from our search module
        search.render_search_tab(
            embeddings=embeddings,
            notes=processed_notes,
            model=embedding_model,
            ollama_model=OLLAMA_MODEL
        )
    
    with tab3:
        # =========================
        # SOURCES BROWSER TAB
        # =========================
        # Render the sources browser from our sources module
        sources_module.render_sources_tab(
            notes=processed_notes,
            notes_folder="./notes"
        )
    
    # =========================
    # CHAT INPUT (OUTSIDE TABS)
    # =========================
    # Chat input widget must be outside tabs due to Streamlit limitation
    if prompt := st.chat_input("Ask a question about your notes..."):
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Search for relevant notes using vector similarity
        with st.spinner("Searching notes..."):
            relevant_notes = search_notes(prompt, embeddings, processed_notes, embedding_model, top_k)
        
        # Generate response based on search results
        if not relevant_notes:
            # No relevant notes found
            response = "I couldn't find any relevant information in your notes to answer this question."
            sources = []
        else:
            # Create RAG prompt with context from relevant notes
            rag_prompt = create_rag_prompt(prompt, relevant_notes)
            
            # Get response from Ollama
            with st.spinner("Generating response..."):
                response = query_ollama(rag_prompt)
            
            sources = relevant_notes
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "sources": sources
        })
        
        # Force rerun to show the new message immediately
        st.rerun()

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main() 