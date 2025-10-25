# Chroma + Letta Agentic RAG Setup

## Overview
- Upload documents into **ChromaDB Cloud** (e.g., collection `rag_collection`).
- Expose a **Letta tool** that runs similarity search against that collection.
- Configure the **Letta agent** persona/instructions to call the tool when it needs external knowledge.
- In Letta ADE declare tool dependencies (`chromadb`) and required environment variables (`CHROMA_*`).
- Use a lightweight client script to chat with the agent; Letta orchestrates tool invocations automatically.

## Requirements
- Letta account and ChromaDB Cloud project.
- Python 3.8+ (tools execute in Python even if the client is Node/TypeScript).
- Any terminal/editor.
- No additional embedding service required for the Chroma backend (other vector options may need Hugging Face embeddings).

## Local Project Bootstrap
```bash
mkdir agentic-rag-chroma
cd agentic-rag-chroma
python -m venv venv          # optional isolation
source venv/bin/activate     # Windows: .\venv\Scripts\Activate.ps1
```

Create `requirements.txt`:
```
letta-client
chromadb
pypdf
python-dotenv
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Optional `.gitignore` entries:
```
venv/
__pycache__/
*.pyc
.env
.DS_Store
```

## Credentials & Environment Variables
1. **Letta API key** – Letta dashboard → API Keys → Create → copy.
2. **Chroma Cloud values** – Chroma project settings provide:
   - `CHROMA_API_KEY`
   - `CHROMA_TENANT`
   - `CHROMA_DATABASE`
   - Optional default collection name `CHROMA_COLLECTION` (e.g., `rag_collection`).

Example `.env`:
```dotenv
# Letta
LETTA_API_KEY="your-letta-key"

# Chroma Cloud
CHROMA_API_KEY="your-chroma-key"
CHROMA_TENANT="tenant-name"
CHROMA_DATABASE="database-id"
CHROMA_COLLECTION="rag_collection"
```
