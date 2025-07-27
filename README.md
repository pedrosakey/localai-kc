# Chat with My Notes

A simple Streamlit app for chatting with your local notes using Ollama and local embeddings.

## Features

- 📝 Load local Markdown (.md) and text (.txt) files
- 🔍 Semantic search using local embeddings
- 🤖 AI responses using Ollama (gemma2:2b)
- 💬 Interactive chat interface
- 📎 Source citations showing relevant note chunks
- 🔄 Real-time note reloading

## Setup

### 1. Install Ollama

First, install Ollama on your system:
- Visit [ollama.ai](https://ollama.ai) and download for your OS
- Install and start Ollama

### 2. Pull the Gemma model

```bash
ollama pull gemma3n:4b
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare your notes

- Create a `notes` folder in the project directory
- Add your Markdown (.md) or text (.txt) files
- Sample notes are included in the `notes/` folder

## Usage

### Run the app

```bash
streamlit run chat_app.py
```

### Configure the app

1. Set your notes folder path in the sidebar (default: `./notes`)
2. Choose your Ollama model (default: `gemma2:2b`)
3. Adjust the number of relevant notes to retrieve
4. Click "Load/Reload Notes" to refresh your note collection

### Chat with your notes

- Type questions about your notes in the chat input
- The app will search for relevant content and generate AI responses
- Click on "Sources" to see which note chunks were used
- Sources show relevance scores to help you understand the search quality

## Supported Note Formats

### Markdown files (.md)
- Supports frontmatter with metadata (title, tags, etc.)
- Headers and content are properly chunked
- Example:
```markdown
---
title: "My Note"
tags: [ai, machine-learning]
---

# Main Topic
Content here...
```

### Text files (.txt)
- Plain text content
- Automatically chunked by paragraphs

## How it works

1. **Document Loading**: Scans your notes folder for .md and .txt files
2. **Text Chunking**: Splits documents into manageable chunks (~1000 characters)
3. **Embeddings**: Creates vector embeddings using sentence-transformers
4. **Search**: Uses cosine similarity to find relevant chunks for your query
5. **RAG**: Combines relevant chunks with your question in a prompt
6. **AI Response**: Sends to Ollama for natural language response
7. **Citations**: Shows which note chunks were used as sources

## Customization

### Change embedding model
Edit the `load_embedding_model()` function to use a different sentence-transformers model:
```python
return SentenceTransformer('all-mpnet-base-v2')  # Higher quality but slower
```

### Change chunk size
Modify the `max_length` parameter in `chunk_text()`:
```python
def chunk_text(text: str, filename: str, max_length: int = 1500):
```

## Troubleshooting

### Ollama connection issues
- Make sure Ollama is running: `ollama serve`
- Check if the model is available: `ollama list`
- Pull the model if missing: `ollama pull gemma2:2b`

### No notes found
- Check the notes folder path
- Ensure files have .md or .txt extensions
- Verify file permissions

### Slow performance
- Use smaller embedding models
- Reduce chunk size or number of retrieved chunks
- Use faster Ollama models like gemma2:2b

## Requirements

- Python 3.8+
- Ollama installed and running
- At least 4GB RAM for embeddings and Ollama model 