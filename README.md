## Setup

1. Copy `.env.example` to `.env` and fill in your Letta API key and agent id.
2. Install dependencies: `pip install -r requirements.txt`.

## Dev server (demo endpoints)

- Start API: `uvicorn app:app --reload`
- Health check: `GET /health`
- Button hook (no-op): `POST /api/letta/create` (accepts optional `{ "notebookId": "..." }`, just logs and returns `{ ok: true }`).
