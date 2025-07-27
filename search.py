"""
Search and Summarization Module

Provides search functionality with AI-powered summarization of results.
Integrates with the main chat app to provide focused search capabilities.
"""

import streamlit as st
import ollama
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

# =============================================================================
# SEARCH AND SUMMARIZATION FUNCTIONS
# =============================================================================

def search_and_summarize(query: str, embeddings: np.ndarray, notes: List[Dict], 
                        model, ollama_model: str, top_k: int = 10) -> Dict:
    """
    Search for relevant notes and create an AI summary.
    
    Args:
        query (str): User's search query
        embeddings (np.ndarray): Pre-computed embeddings for all notes
        notes (List[Dict]): List of note chunks with metadata
        model: Sentence transformer model for encoding the query
        ollama_model (str): Name of the Ollama model for summarization
        top_k (int): Number of top results to include in summary
        
    Returns:
        Dict: Summary text and source information
    """
    if len(notes) == 0:
        return {
            "summary": "No notes available to search.",
            "sources": [],
            "query": query
        }
    
    # Convert query to embedding vector
    query_embedding = model.encode([query])
    
    # Calculate cosine similarity between query and all note embeddings
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Get indices of top k most similar notes
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    relevant_notes = []
    for idx in top_indices:
        # Include results above minimum similarity threshold
        if similarities[idx] > 0.1:
            note = notes[idx].copy()
            note['similarity'] = similarities[idx]
            relevant_notes.append(note)
    
    if not relevant_notes:
        return {
            "summary": f"No relevant information found for '{query}' in your notes.",
            "sources": [],
            "query": query
        }
    
    # Create summarization prompt
    summary_prompt = create_summarization_prompt(query, relevant_notes)
    
    # Get AI summary
    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[{'role': 'user', 'content': summary_prompt}],
            stream=False
        )
        summary = response['message']['content']
    except Exception as e:
        summary = f"Error generating summary: {str(e)}"
    
    return {
        "summary": summary,
        "sources": relevant_notes,
        "query": query
    }

def create_summarization_prompt(query: str, relevant_notes: List[Dict]) -> str:
    """
    Create a specialized prompt for summarizing search results.
    
    Args:
        query (str): Original search query
        relevant_notes (List[Dict]): Most relevant note chunks
        
    Returns:
        str: Complete summarization prompt
    """
    # Build context from relevant notes
    context = ""
    for i, note in enumerate(relevant_notes, 1):
        context += f"\n\n--- Source {i}: {note['file']} ---\n"
        if note.get('heading'):
            context += f"Section: {note['heading']}\n"
        context += note['content']
        context += f"\n(Relevance Score: {note['similarity']:.2f})"
    
    # Create the summarization prompt
    prompt = f"""Based on the provided sources, give a brief overview for: "{query}"

Keep it concise - just 2-3 sentences highlighting the key points.

SOURCES:{context}

OVERVIEW:"""
    
    return prompt

# =============================================================================
# STREAMLIT SEARCH INTERFACE
# =============================================================================

def render_search_tab(embeddings: np.ndarray, notes: List[Dict], model, ollama_model: str):
    """
    Render the search and summarization tab interface.
    
    Args:
        embeddings (np.ndarray): Pre-computed embeddings for all notes
        notes (List[Dict]): List of note chunks with metadata
        model: Sentence transformer model
        ollama_model (str): Name of the Ollama model
    """
    st.header("🔍 Search & Summarize")
    st.markdown("Search your notes and get AI-powered summaries of the results.")
    
    # Search configuration
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="e.g., 'machine learning algorithms', 'iOS development patterns', 'AI applications'",
            help="Enter keywords or questions to search your notes"
        )
    
    with col2:
        search_depth = st.selectbox(
            "Search Depth",
            options=[5, 10, 15, 20],
            index=1,
            help="Number of relevant notes to include in summary"
        )
    
    # Search button
    if st.button("🔍 Search & Summarize", type="primary", use_container_width=True):
        if not search_query.strip():
            st.warning("Please enter a search query.")
            return
        
        with st.spinner("Searching and generating summary..."):
            results = search_and_summarize(
                query=search_query,
                embeddings=embeddings,
                notes=notes,
                model=model,
                ollama_model=ollama_model,
                top_k=search_depth
            )
        
        # Display results
        display_search_results(results)
    
    # Show example queries
    st.markdown("---")
    st.markdown("### 💡 Example Queries")
    example_queries = [
        "What are the main types of machine learning?",
        "How do I get started with iOS development?", 
        "What are neural networks and how do they work?",
        "Explain the difference between supervised and unsupervised learning",
        "What are the best practices for iOS app development?"
    ]
    
    for query in example_queries:
        if st.button(f"📝 {query}", key=f"example_{hash(query)}"):
            # Set the query in session state to trigger search
            st.session_state.search_query = query
            st.rerun()

def display_search_results(results: Dict):
    """
    Display search results with summary and sources.
    
    Args:
        results (Dict): Search results containing summary and sources
    """
    # Display query
    st.markdown(f"### 🔍 Results for: *\"{results['query']}\"*")
    
    if not results['sources']:
        st.info(results['summary'])
        return
    
    # Display summary
    st.markdown("### 📄 Summary")
    st.markdown(results['summary'])
    
    # Display sources
    st.markdown("### 📚 Sources")
    st.markdown(f"*Found {len(results['sources'])} relevant sources*")
    
    # Create tabs for different source views
    tab1, tab2 = st.tabs(["📋 Source List", "📊 Relevance Chart"])
    
    with tab1:
        for i, source in enumerate(results['sources'], 1):
            with st.expander(
                f"📄 {source['file']} - Relevance: {source['similarity']:.1%}",
                expanded=i <= 3  # Expand first 3 sources by default
            ):
                # Show metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**File:** {source['file']}")
                with col2:
                    st.markdown(f"**Relevance:** {source['similarity']:.1%}")
                with col3:
                    if source.get('heading'):
                        st.markdown(f"**Section:** {source['heading']}")
                
                # Show content
                st.markdown("**Content:**")
                st.markdown(f"```\n{source['content']}\n```")
    
    with tab2:
        # Create a simple relevance chart
        import pandas as pd
        
        chart_data = pd.DataFrame({
            'Source': [f"{s['file'][:20]}..." if len(s['file']) > 20 else s['file'] 
                      for s in results['sources']],
            'Relevance': [s['similarity'] for s in results['sources']]
        })
        
        st.bar_chart(chart_data.set_index('Source')['Relevance'])
        
        # Show statistics
        avg_relevance = np.mean([s['similarity'] for s in results['sources']])
        max_relevance = max([s['similarity'] for s in results['sources']])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sources Found", len(results['sources']))
        with col2:
            st.metric("Average Relevance", f"{avg_relevance:.1%}")
        with col3:
            st.metric("Best Match", f"{max_relevance:.1%}")

# =============================================================================
# SEARCH UTILITIES
# =============================================================================

def get_search_suggestions(notes: List[Dict], limit: int = 10) -> List[str]:
    """
    Generate search suggestions based on note content.
    
    Args:
        notes (List[Dict]): List of note chunks
        limit (int): Maximum number of suggestions
        
    Returns:
        List[str]: List of suggested search terms
    """
    # Extract common terms from note titles and headings
    suggestions = set()
    
    for note in notes:
        # Add file titles (remove extensions)
        title = note.get('title', '').replace('.md', '').replace('.txt', '')
        if title and len(title) > 3:
            suggestions.add(title)
        
        # Add headings from content
        content = note.get('content', '')
        for line in content.split('\n'):
            if line.startswith('#') and len(line) > 4:
                heading = line.strip('#').strip()
                if len(heading) > 3 and len(heading) < 50:
                    suggestions.add(heading)
    
    # Convert to sorted list and limit
    return sorted(list(suggestions))[:limit] 