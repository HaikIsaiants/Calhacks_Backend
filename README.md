## Setup

1. Copy `.env.example` to `.env` and fill in your Letta API key and agent id.
2. Install dependencies: `pip install -r requirements.txt`.

## Dev server (demo endpoints)

- Quick start: `python run.py` (loads `.env`, starts Uvicorn with reload)
- Or start directly: `uvicorn app:app --reload`
- Health check: `GET /health`
- Create from template: `POST /api/letta/create` (accepts optional `{ "notebookId": "..." }`).
  - If env vars are set, this will create a fresh Letta agent from your template and return `{ agentId }`.
  - If not configured, it returns an acknowledgement only.
- Save hook (demo logging only): `POST /api/notebook/save`

### Environment

Set these in `.env` (or export before running):

- `LETTA_API_KEY` – your Letta API token
- `LETTA_PROJECT` – project slug (default: `default-project`)
- `LETTA_TEMPLATE_VERSION` – template version slug, e.g. `clever-jade-worm:latest`
