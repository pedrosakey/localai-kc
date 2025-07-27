# Chat with My Notes

A simple Streamlit app for chatting with your local notes using Ollama and local embeddings.

**Presentacion**
[Ir a la presentacion](https://docs.google.com/presentation/d/1E-K28nZp0knQgzOXBkIPd3qRzrYmziGs/edit?usp=drive_link&ouid=101768567519265651809&rtpof=true&sd=true)

**Demo**
[Ir a la demo](https://drive.google.com/file/d/16-LsXyBDi5mlJznPtcsnoZwVskGpMh7l/view?usp=sharing)

## Features

- 📝 Load local Markdown (.md) and text (.txt) files
- 🔍 Semantic search using local embeddings
- 🤖 AI responses using Ollama (gemma3n:4b)
- 💬 Interactive chat interface
- 📎 Source citations showing relevant note chunks
- 🔗 **Wiki-links**: Click `[[note_name]]` to navigate between notes
- 📅 **Daily Notes**: Structured daily entries with status and areas
- 🎵 **AI Descriptions**: Generate descriptions for audio/photo files
- 🔄 **Auto-reload**: Content updates automatically after changes
- 🇪🇸 Spanish language support

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

### Main Interface

The app has three main tabs:

#### 💬 Chat
- Ask questions about your notes
- Get AI responses with source citations
- Sources show relevance scores

#### 🔍 Search  
- Semantic search across all notes
- Get summarized results in Spanish
- Adjust number of results with slider

#### 📁 Sources Browser
- **Source Files**: Browse all your notes
- **Daily Notes**: View structured daily entries
- **Linked Viewer**: Click wiki-links to see referenced content

### Configure the app

1. Set your notes folder path in the sidebar (default: `./notes`)
2. Choose your Ollama model (default: `gemma3n:4b`) 
3. Adjust the number of relevant notes to retrieve
4. Click "Load/Reload Notes" to refresh your note collection

## Note Formats

### Regular Markdown files (.md)
```markdown
---
title: "My Note"
tags: [ai, machine-learning]
---

# Main Topic
Content with [[wiki_links]] to other notes...
```

### Daily Notes format
```markdown
18:11 meeting notes status:: Completed area:: Work date::2025-07-29
[[project_notes]]

19:05 buy coffee status:: Pending area:: Personal date::2025-07-29
[[shopping_list]]
```

### Audio/Photo files
- Add `.md` files describing audio/photo content
- Use "🤖 Describir con IA" button to generate descriptions
- Content becomes immediately searchable after generation
- Automatic cache clearing and reload

## Wiki-Links

- Use `[[note_name]]` to link between notes
- Click links to view content in Linked Viewer
- Works in daily notes and regular content
- Auto-detects and resolves file references

## AI Descriptions

- **Smart Detection**: Generates specific content based on file type
- **Audio Files**: Creates detailed transcriptions with metrics
- **Photo Files**: Generates visual analysis and testing results
- **Auto-Reload**: Content immediately available in search after generation
- **Cache Management**: Automatically clears and reloads data

## How it works

1. **Document Loading**: Scans notes folder for .md and .txt files
2. **Text Chunking**: Splits documents into chunks (~1000 characters)
3. **Embeddings**: Creates vector embeddings using sentence-transformers
4. **Search**: Uses cosine similarity to find relevant chunks
5. **RAG**: Combines relevant chunks with your question
6. **AI Response**: Sends to Ollama for natural language response
7. **Citations**: Shows which note chunks were used as sources

