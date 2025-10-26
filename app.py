import os
import time
import json
import logging
from typing import Optional, Dict, Any, Iterable

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


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

# Optional: initialize Letta client when env is present
try:
    from letta_client import Letta  # type: ignore
except Exception:  # library not installed or optional
    Letta = None  # type: ignore

LETTA_TOKEN = os.getenv("LETTA_API_KEY") or os.getenv("LETTA_TOKEN")
LETTA_PROJECT = os.getenv("LETTA_PROJECT", "default-project")
LETTA_TEMPLATE_VERSION = os.getenv("LETTA_TEMPLATE_VERSION")  # e.g., "clever-jade-worm:latest"
LETTA_API_BASE = os.getenv("LETTA_API_BASE", "https://api.letta.com")

_client = None
if Letta and LETTA_TOKEN:
    try:
        _client = Letta(token=LETTA_TOKEN)
        logger.info("Letta client initialized for project=%s", LETTA_PROJECT)
    except Exception as e:
        logger.warning("Letta client init failed: %s", e)
        _client = None


_latest_agent_id: Optional[str] = None


def _extract_agent_id(resp: Any) -> Optional[str]:  # type: ignore[name-defined]
    """Best‑effort extraction of agent id from various response shapes.

    The Letta SDK may return a Pydantic model with `.agents`, a dict, or an
    object with `.id`. This function tries common patterns before giving up.
    """
    # 1) Direct attribute `.agents[0].id`
    try:
        agents = getattr(resp, "agents")
        if isinstance(agents, Iterable):
            agents_list = list(agents)
            if agents_list:
                first = agents_list[0]
                # object or dict
                if hasattr(first, "id"):
                    return getattr(first, "id")
                if isinstance(first, dict) and "id" in first:
                    return str(first["id"])
    except Exception:
        pass

    # 2) Single object with `.id`
    if hasattr(resp, "id"):
        try:
            rid = getattr(resp, "id")
            if isinstance(rid, (str, int)):
                return str(rid)
        except Exception:
            pass

    # 3) Pydantic v2 model → model_dump()
    try:
        md = getattr(resp, "model_dump", None)
        if callable(md):
            data = md()
            # common dict shapes
            if isinstance(data, dict):
                if "agents" in data and isinstance(data["agents"], list) and data["agents"]:
                    item = data["agents"][0]
                    if isinstance(item, dict) and "id" in item:
                        return str(item["id"])
                if "agent" in data and isinstance(data["agent"], dict) and "id" in data["agent"]:
                    return str(data["agent"]["id"])
                if "id" in data:
                    return str(data["id"])
                # Log keys to aid debugging without dumping entire payload
                try:
                    logger.info("Letta create response keys: %s", list(data.keys()))
                except Exception:
                    pass
    except Exception:
        pass

    # 4) Last resort: dict-like access
    if isinstance(resp, dict):
        if "agents" in resp and isinstance(resp["agents"], list) and resp["agents"]:
            item = resp["agents"][0]
            if isinstance(item, dict) and "id" in item:
                return str(item["id"])
        if "id" in resp:
            return str(resp["id"])

    return None

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
    global _latest_agent_id
    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")
    logger.info(
        "letta.create received | notebookId=%s ip=%s ua=%s",
        getattr(payload, "notebookId", None),
        client_ip,
        ua,
    )

    # If properly configured, create a fresh agent from a template.
    # Use the REST API directly to reliably capture the created agent id.
    if LETTA_TOKEN and LETTA_TEMPLATE_VERSION:
        try:
            import httpx  # local import to avoid hard dependency at import-time

            base_url = os.getenv("LETTA_API_BASE", "https://api.letta.com")
            url = f"{LETTA_API_BASE}/v1/templates/{LETTA_PROJECT}/{LETTA_TEMPLATE_VERSION}/agents"
            headers = {
                "Authorization": f"Bearer {LETTA_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Create the agent from the template and capture the id
            with httpx.Client(timeout=30) as client:
                r = client.post(url, json={}, headers=headers)

            r.raise_for_status()

            agent_id: Optional[str] = None
            # Prefer JSON body
            try:
                data = r.json()
            except Exception:
                data = None
            if isinstance(data, dict):
                if isinstance(data.get("agents"), list) and data["agents"]:
                    item = data["agents"][0]
                    if isinstance(item, dict) and "id" in item:
                        agent_id = str(item["id"]) 
                elif isinstance(data.get("agent"), dict) and "id" in data["agent"]:
                    agent_id = str(data["agent"]["id"]) 
                elif "id" in data:
                    agent_id = str(data["id"]) 

            # Fallback to Location header (…/agents/agent-xxxx)
            if not agent_id:
                loc = r.headers.get("Location") or r.headers.get("location")
                if loc:
                    part = loc.rstrip("/").split("/")[-1]
                    if part.startswith("agent-"):
                        agent_id = part

            if not agent_id:
                raise RuntimeError("No agent id returned from Letta")

            _latest_agent_id = agent_id

            logger.info(
                "letta.create agent created | notebookId=%s agentId=%s",
                payload.notebookId,
                agent_id,
            )

            return {
                "ok": True,
                "event": "letta.create.created",
                "ts": int(time.time()),
                "notebookId": payload.notebookId,
                "agentId": agent_id,
            }
        except Exception as e:
            # If creation fails, surface a clear message for the frontend
            logger.exception("Letta agent creation failed")
            raise HTTPException(status_code=502, detail=f"Letta error: {e}")

    # Fallback: acknowledge only (no Letta configured yet)
    _latest_agent_id = None
    return {
        "ok": True,
        "event": "letta.create.received",
        "ts": int(time.time()),
        "notebookId": payload.notebookId,
    }


def _send_notebook_to_letta(agent_id: str, payload: Dict[str, Any]) -> None:
    message = "NOTEBOOK:\n" + json.dumps(payload, indent=2, ensure_ascii=False)
    data = {"messages": [{"role": "user", "content": message}]}
    headers = {
        "Authorization": f"Bearer {LETTA_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    import httpx

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{LETTA_API_BASE}/v1/agents/{agent_id}/messages",
            json=data,
            headers=headers,
        )
    resp.raise_for_status()


class NotebookSavePayload(BaseModel):
    savedAt: str = Field(..., description="ISO timestamp of the save event")
    report: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    snapshot: Optional[Dict[str, Any]] = None
    agentId: Optional[str] = None
    notebookId: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


@app.post("/api/notebook/save")
async def notebook_save(payload: NotebookSavePayload):
    """Receive the notebook delta + snapshot and log it for now."""

    dump = payload.model_dump(exclude_none=True)
    pretty = json.dumps(dump, indent=2, ensure_ascii=False)
    logger.info(
        "notebook.save received | notebookId=%s agentId=%s savedAt=%s",
        dump.get("notebookId"),
        dump.get("agentId"),
        dump.get("savedAt"),
    )
    if payload.report:
        logger.info("notebook.save report:\n%s", payload.report)
    logger.info(
        "notebook.save payload:\n%s",
        pretty,
    )

    # overwrite log.md with the latest JSON snapshot
    try:
        with open("log.md", "w", encoding="utf-8") as f:
            f.write(pretty)
    except Exception as write_err:
        logger.warning("Failed to write log.md: %s", write_err)

    forwarded = False
    if LETTA_TOKEN and _latest_agent_id:
        try:
            _send_notebook_to_letta(_latest_agent_id, dump)
            forwarded = True
            logger.info(
                "notebook.save forwarded to Letta | agentId=%s",
                _latest_agent_id,
            )
        except Exception as err:
            logger.exception("Failed to forward notebook save to Letta: %s", err)

    return {
        "ok": True,
        "ts": int(time.time()),
        "received": dump,
        "forwarded": forwarded,
    }
