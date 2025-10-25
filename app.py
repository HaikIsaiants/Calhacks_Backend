import os
import time
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class CreatePayload(BaseModel):
    notebookId: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def _origin_list(val: Optional[str]):
    if not val or val.strip() == "*":
        return ["*"]
    return [v.strip() for v in val.split(",") if v.strip()]


app = FastAPI(title="Calhacks Backend", version="0.1.0")

# CORS: allow the frontend origin(s); default to all for demo purposes.
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origin_list(ALLOWED_ORIGIN),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("letta-demo")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@app.get("/health")
async def health():
    return {"ok": True, "ts": int(time.time())}


@app.post("/api/letta/create")
async def letta_create(payload: CreatePayload, request: Request):
    """Acknowledges the 'Open Notebook' action.

    For the demo, this endpoint does not create anything. It simply logs
    the event and returns an OK response so the frontend knows the click
    was received. Later, wire real Letta agent creation here.
    """
    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")
    logger.info(
        "letta.create received | notebookId=%s ip=%s ua=%s",
        getattr(payload, "notebookId", None),
        client_ip,
        ua,
    )
    return {
        "ok": True,
        "event": "letta.create.received",
        "ts": int(time.time()),
        "notebookId": payload.notebookId,
    }

