## Overview

This FastAPI service bridges three pieces of the demo stack:

- **Notebook frontend** posts notebook changes and the user's `ANALYZE` command.
- **Letta agent** receives the notebook context, generates a structured protein-edit analysis, and returns JSON.
- **Visualization frontend** polls the backend for the latest analysis and renders the graph plus summaries.

## Data flow

1. The notebook UI captures notebook state and sends `POST /api/notebook/save`.  
   The backend logs the payload, overwrites `log.md`, and forwards the snapshot to the currently active Letta agent (when configured).
2. When the user clicks Analyze, the frontend sends `POST /api/letta/analyze`.  
   The backend calls Letta's Messages API, extracts the JSON analysis, validates it with Pydantic (`NotebookAnalysisResult`), stores it in memory, and writes the same JSON to `log.md`.
3. The visualization frontend requests `GET /api/analysis/result`.  
   The backend returns the cached JSON exactly as Letta produced it so the UI can populate summary tabs and render the Cytoscape graph.
4. Optional: `POST /api/analysis/result` exists for injecting mock analyses during development; it validates and caches the payload just like the Letta path.

The result object contains the headline summaries plus `graph.nodes`/`graph.edges` (capped at 10 nodes) that the frontend uses to draw the interaction network.

## Setup

1. Copy `.env.example` to `.env` and fill in your Letta API credentials (API key, template version).  
   If you omit them, the backend will run but skip the Letta integration.
2. Install dependencies: `pip install -r requirements.txt`.

## Running locally

- Quick start: `python run.py` (loads `.env`, starts Uvicorn with auto-reload).  
- Manual: `uvicorn app:app --reload`.
- Health check: `GET /health`.
- Create a fresh agent from your template: `POST /api/letta/create` (optional `{ "notebookId": "..." }`). On success it returns `{ "agentId": ... }` and stores it for subsequent calls.

## Environment variables

Set these in `.env` or export them before launching:

- `LETTA_API_KEY` – Letta API token (required for live agent calls).
- `LETTA_PROJECT` – Project slug; defaults to `default-project`.
- `LETTA_TEMPLATE_VERSION` – Template version slug, for example `clever-jade-worm:latest`.
- `ALLOWED_ORIGIN` – Comma-separated list of frontend origins for CORS (defaults to `*`).
