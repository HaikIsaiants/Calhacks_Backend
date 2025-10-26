import os
import time
import json
import logging
import httpx
from typing import Optional, Dict, Any, Iterable, List, Literal

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


class CreatePayload(BaseModel):
    notebookId: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def _origin_list(val: Optional[str]):
    if not val or val.strip() == "*":
        return ["*"]
    return [v.strip() for v in val.split(",") if v.strip()]


class TextWithSources(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str = Field(...)
    source_ids: Optional[List[str]] = Field(default=None)


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique identifier for the graph node")
    label: str = Field(..., description="Short display label (prefer acronyms)")
    type: Literal["protein", "drug", "entity"] = Field(
        ..., description="Classification of the node for visualization"
    )
    isEdited: bool = Field(
        False, description="Flag to highlight the edited protein in the graph"
    )
    notes: Optional[TextWithSources] = Field(
        None, description="Optional context about the node or its role"
    )
    relationship_to_edited: Optional[TextWithSources] = Field(
        None, description="Relationship to the edited protein"
    )
    role_summary: Optional[TextWithSources] = Field(
        None, description="Brief summary of the node's role"
    )
    source_ids: Optional[List[str]] = Field(
        default=None, description="Optional list of sources associated with this node"
    )

    @field_validator("notes", "relationship_to_edited", "role_summary", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value: Any):
        if value is None or isinstance(value, TextWithSources):
            return value
        if isinstance(value, str):
            return {"text": value}
        if isinstance(value, dict):
            return value
        raise TypeError("Expected string, dict, or TextWithSources-compatible value")


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str = Field(..., description="Node id where the interaction originates")
    target: str = Field(..., description="Node id where the interaction ends")
    interaction: str = Field(..., description="Short label describing the interaction")
    mechanism: Optional[str] = Field(
        None, description="Optional mechanistic detail for the interaction"
    )


class InteractionGraph(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nodes: List[GraphNode] = Field(
        default_factory=list,
        description="Nodes in the interaction graph",
    )
    edges: List[GraphEdge] = Field(
        default_factory=list,
        description="Edges describing interactions between nodes",
    )

    @model_validator(mode="after")
    def validate_graph(self):
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) > 10:
            raise ValueError("Graph cannot contain more than 10 nodes")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Graph nodes must have unique ids")

        known = set(node_ids)
        dangling = [
            (edge.source, edge.target)
            for edge in self.edges
            if edge.source not in known or edge.target not in known
        ]
        if dangling:
            invalid = ", ".join(f"{src}->{tgt}" for src, tgt in dangling)
            raise ValueError(f"Edges reference unknown nodes: {invalid}")
        return self


class EditedProtein(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Node id for the edited protein")
    label: str = Field(..., description="Short name/acronym for the edited protein")
    description: Optional[TextWithSources] = Field(
        None, description="Brief note describing the edit"
    )
    mutations: List[TextWithSources] = Field(
        default_factory=list, description="List of mutations included in the edit"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1, if available",
    )


class NotebookAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    analysis_summary: TextWithSources = Field(
        ..., description="Plain-English summary of the notebook analysis"
    )
    edited_protein: EditedProtein = Field(
        ..., description="Metadata describing the edited protein"
    )
    graph: InteractionGraph = Field(
        ..., description="Interaction graph capturing relevant entities"
    )


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
_latest_analysis_result: Optional[NotebookAnalysisResult] = None


def _store_analysis_result(result: NotebookAnalysisResult, *, source: str) -> None:
    """Persist the latest analysis result for retrieval by the frontend."""

    global _latest_analysis_result
    _latest_analysis_result = result

    try:
        with open("log.md", "w", encoding="utf-8") as f:
            f.write(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    except Exception as write_err:
        logger.warning("Failed to write analysis log: %s", write_err)

    logger.info(
        "analysis stored | source=%s edited=%s nodes=%d edges=%d",
        source,
        result.edited_protein.label,
        len(result.graph.nodes),
        len(result.graph.edges),
    )


def _safe_truncate(s: str, limit: int = 600) -> str:
    try:
        s = s.replace("\n", " ")
    except Exception:
        pass
    return (s[: limit] + ("…" if len(s) > limit else "")) if isinstance(s, str) else str(s)


def _debug_log_letta_response(resp_json: Optional[Dict[str, Any]], raw_text: Optional[str]) -> None:
    try:
        if isinstance(resp_json, dict):
            top_keys = list(resp_json.keys())
            logger.info("letta.analyze response keys: %s", top_keys)
            msgs = resp_json.get("messages")
            if isinstance(msgs, list):
                logger.info("letta.analyze messages count: %d", len(msgs))
                # Try to log last assistant message content shape
                for msg in reversed(msgs):
                    role = (str(msg.get("role") or msg.get("speaker") or msg.get("author") or "").lower()
                            if isinstance(msg, dict) else str(getattr(msg, "role", "")).lower())
                    if role in {"assistant", "model", "agent"}:
                        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
                        ctype = type(content).__name__
                        logger.info("letta.analyze assistant content type: %s", ctype)
                        if isinstance(content, str):
                            logger.info("letta.analyze assistant text snippet: %s", _safe_truncate(content))
                        elif isinstance(content, list):
                            shapes = []
                            for it in content:
                                if isinstance(it, dict):
                                    shapes.append(f"dict:{list(it.keys())}")
                                else:
                                    shapes.append(type(it).__name__)
                            logger.info("letta.analyze assistant content items: %s", shapes)
                        elif isinstance(content, dict):
                            logger.info("letta.analyze assistant content keys: %s", list(content.keys()))
                        break
        # Always log a short raw body snippet to help debug parsing
        if raw_text:
            logger.info("letta.analyze raw body snippet: %s", _safe_truncate(raw_text))
    except Exception as e:
        logger.debug("Failed to log detailed Letta response: %s", e)


def _find_analysis_like_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Heuristic search for an analysis-like dict containing a graph.

    Looks for a dict with keys resembling our schema: 'graph' with 'nodes'/'edges',
    plus 'analysis_summary' and 'edited_protein'. Recurses into lists/dicts.
    """

    def _has_text_payload(val: Any) -> bool:
        if isinstance(val, str):
            return True
        if isinstance(val, dict):
            text_val = val.get("text")
            return isinstance(text_val, str) and text_val.strip() != ""
        return False

    try:
        if isinstance(obj, dict):
            g = obj.get("graph")
            if (
                isinstance(g, dict)
                and isinstance(g.get("nodes"), list)
                and isinstance(g.get("edges"), list)
                and _has_text_payload(obj.get("analysis_summary"))
                and isinstance(obj.get("edited_protein"), dict)
            ):
                return obj
            for v in obj.values():
                found = _find_analysis_like_dict(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for it in obj:
                found = _find_analysis_like_dict(it)
                if found:
                    return found
    except Exception:
        return None
    return None


def _extract_json_from_messages(resp_json: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Try to extract a JSON analysis object directly from Letta 'messages' envelope."""
    if not isinstance(resp_json, dict):
        return None
    messages = resp_json.get("messages")
    if not isinstance(messages, list):
        return None

    # Prefer assistant/final messages; iterate from the end
    for msg in reversed(messages):
        if not isinstance(msg, dict):
            continue
        mtype = str(msg.get("message_type") or "").lower()
        role = str(msg.get("role") or msg.get("speaker") or msg.get("author") or "").lower()
        if mtype and ("assistant" in mtype or "final" in mtype or "output" in mtype) or role in {"assistant", "agent", "model"}:
            content = msg.get("content")
            # 1) Content as list of blocks
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    # Common keys: json, json_object, data, value, content
                    for key in ("json", "json_object"):
                        val = block.get(key)
                        if isinstance(val, dict):
                            return val
                        if isinstance(val, str):
                            try:
                                return json.loads(val)
                            except Exception:
                                pass
                    # MIME-typed text
                    if block.get("mime_type") in ("application/json", "text/json"):
                        txt = block.get("text") or block.get("value") or block.get("content")
                        if isinstance(txt, str):
                            try:
                                return json.loads(txt)
                            except Exception:
                                pass
                    # Fallback: nested data/value/content containing the shape
                    for key in ("data", "value", "content"):
                        v = block.get(key)
                        if isinstance(v, dict):
                            found = _find_analysis_like_dict(v)
                            if found:
                                return found
                        if isinstance(v, str):
                            try:
                                candidate = json.loads(v)
                                if isinstance(candidate, dict):
                                    found = _find_analysis_like_dict(candidate)
                                    if found:
                                        return found
                            except Exception:
                                pass
            # 2) Content as single dict
            if isinstance(content, dict):
                for key in ("json", "json_object", "data", "value", "content"):
                    v = content.get(key)
                    if isinstance(v, dict):
                        found = _find_analysis_like_dict(v)
                        if found:
                            return found
                    if isinstance(v, str):
                        try:
                            candidate = json.loads(v)
                            if isinstance(candidate, dict):
                                found = _find_analysis_like_dict(candidate)
                                if found:
                                    return found
                        except Exception:
                            pass
            # 3) Content as raw string
            if isinstance(content, str):
                try:
                    candidate = json.loads(content)
                    if isinstance(candidate, dict):
                        return candidate
                except Exception:
                    pass

    # Last resort: search entire structure
    return _find_analysis_like_dict(resp_json)

def _content_to_text(content: Any) -> Optional[str]:
    """Normalize heterogeneous message content structures to plain text."""

    if isinstance(content, str):
        return content.strip() or None

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "value", "content"):
                    val = item.get(key)
                    if isinstance(val, str):
                        parts.append(val)
                        break
        merged = "\n".join(part.strip() for part in parts if part and part.strip())
        return merged or None

    if isinstance(content, dict):
        # Some SDKs wrap text in {"text": "..."}
        for key in ("text", "value", "content"):
            val = content.get(key)
            if isinstance(val, str):
                return val.strip() or None
    return None


def _extract_assistant_text(payload: Any) -> Optional[str]:
    """Attempt to pull the assistant's reply text from a Letta API response."""

    if isinstance(payload, dict):
        messages = payload.get("messages")
        if isinstance(messages, list):
            for msg in reversed(messages):
                role = ""
                if isinstance(msg, dict):
                    role = (
                        str(msg.get("role") or msg.get("speaker") or msg.get("author") or "")
                        .lower()
                        .strip()
                    )
                    content = msg.get("content")
                else:
                    role = str(getattr(msg, "role", "")).lower().strip()
                    content = getattr(msg, "content", None)
                if role in {"assistant", "model", "agent"}:
                    text = _content_to_text(content)
                    if text:
                        return text

        message = payload.get("message")
        if isinstance(message, dict):
            text = _content_to_text(message.get("content"))
            if text:
                return text

        data_block = payload.get("data")
        if isinstance(data_block, dict):
            nested = _extract_assistant_text(data_block)
            if nested:
                return nested

    return None


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
            url = f"{LETTA_API_BASE}/v1/templates/{LETTA_PROJECT}/{LETTA_TEMPLATE_VERSION}/agents"
            headers = {
                "Authorization": f"Bearer {LETTA_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=120) as client:
                resp = client.post(url, json={}, headers=headers)
            resp.raise_for_status()

            agent_id: Optional[str] = None
            # Prefer JSON body
            try:
                data = resp.json()
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
                loc = resp.headers.get("Location") or resp.headers.get("location")
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
    with httpx.Client(timeout=1200) as client:
        resp = client.post(
            f"{LETTA_API_BASE}/v1/agents/{agent_id}/messages",
            json=data,
            headers=headers,
        )
    resp.raise_for_status()
    return None


@app.post("/api/letta/analyze")
async def letta_analyze(request: Request):
    """Run the Letta agent to produce the final JSON analysis and store it.

    - Uses the most recently created agent id unless `agentId` is provided via query.
    - Sends a single 'ANALYZE' message and expects the agent to reply with JSON.
    - If the reply parses and validates against NotebookAnalysisResult, it is stored
      and returned verbatim in the response.
    """
    agent_id = request.query_params.get("agentId") or _latest_agent_id
    if not (LETTA_TOKEN and agent_id):
        raise HTTPException(status_code=400, detail="Agent not configured or missing")

    headers = {
        "Authorization": f"Bearer {LETTA_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {"messages": [{"role": "user", "content": "ANALYZE"}]}

    # Kick off the analysis and capture the run id
    with httpx.Client(timeout=120) as client:
        start_resp = client.post(
            f"{LETTA_API_BASE}/v1/agents/{agent_id}/messages",
            json=body,
            headers=headers,
        )
    start_resp.raise_for_status()

    try:
        start_payload = start_resp.json()
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Invalid Letta response: {err}")

    try:
        logger.info("letta.analyze start payload: %s", json.dumps(start_payload, indent=2))
    except Exception:
        logger.info("letta.analyze start payload (raw): %s", start_payload)

    # Try to extract the analysis directly from the initial response
    analysis_payload: Optional[Dict[str, Any]] = None
    analysis_payload = _extract_json_from_messages(start_payload)
    if analysis_payload is None:
        analysis_payload = _find_analysis_like_dict(start_payload)

    if analysis_payload is None:
        # Fallback: poll Letta for completion when the initial payload doesn't contain the final JSON.
        run_id: Optional[str] = None
        if isinstance(start_payload, dict):
            run_id = (
                start_payload.get("run_id")
                or start_payload.get("id")
                or start_payload.get("message_id")
            )
            if not run_id:
                data_block = start_payload.get("data")
                if isinstance(data_block, dict):
                    run_id = (
                        data_block.get("run_id")
                        or data_block.get("id")
                        or data_block.get("message_id")
                    )

        if not isinstance(run_id, str):
            raise HTTPException(status_code=502, detail="Letta response missing run id")

        poll_interval = 3.0
        deadline = time.time() + 1200
        status_url = f"{LETTA_API_BASE}/v1/runs/{run_id}"
        messages_url = f"{LETTA_API_BASE}/v1/runs/{run_id}/messages"

        while time.time() < deadline:
            try:
                with httpx.Client(timeout=120) as client:
                    status_resp = client.get(status_url, headers=headers)
                status_resp.raise_for_status()
                status_data = status_resp.json()
                logger.info("letta.analyze poll state: %s", status_data)
            except Exception as poll_exc:
                logger.warning("letta.analyze poll failed: %s", poll_exc)
                time.sleep(poll_interval)
                continue

            state = None
            if isinstance(status_data, dict):
                state = status_data.get("state") or status_data.get("status")
            if isinstance(state, str):
                state = state.lower()

            if state in {"completed", "finished", "succeeded"}:
                try:
                    with httpx.Client(timeout=120) as client:
                        messages_resp = client.get(messages_url, headers=headers)
                    messages_resp.raise_for_status()
                    messages_data = messages_resp.json()
                    try:
                        logger.info(
                            "letta.analyze messages payload: %s",
                            json.dumps(messages_data, indent=2),
                        )
                    except Exception:
                        logger.info("letta.analyze messages payload (raw): %s", messages_data)
                    analysis_payload = _extract_json_from_messages(messages_data)
                    if analysis_payload is None:
                        analysis_payload = _find_analysis_like_dict(messages_data)
                except Exception as fetch_exc:
                    raise HTTPException(status_code=502, detail=f"Failed to fetch analysis: {fetch_exc}")
                break

            if state in {"failed", "error"}:
                raise HTTPException(status_code=502, detail="Letta reported run failure")

            time.sleep(poll_interval)

        if analysis_payload is None:
            raise HTTPException(status_code=504, detail="Letta analysis timed out")

    try:
        validated = NotebookAnalysisResult.model_validate(analysis_payload)
    except Exception as e:
        logger.warning("Validation failed for analysis: %s | keys=%s", e, list(analysis_payload.keys()))
        raise HTTPException(status_code=422, detail=f"Analysis failed validation: {e}")

    _store_analysis_result(validated, source="letta.analyze")

    return {"ok": True, "analysis": analysis_payload, "ts": int(time.time())}


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


@app.post("/api/analysis/result")
async def analysis_result(result: NotebookAnalysisResult):
    """Accept the agent's final analysis payload (summary + interaction graph)."""

    _store_analysis_result(result, source="api.analysis.result")
    return {"ok": True, "ts": int(time.time())}


@app.get("/api/analysis/result")
async def get_analysis_result():
    """Return the most recent agent analysis as the raw JSON object."""

    if _latest_analysis_result is None:
        raise HTTPException(status_code=404, detail="No analysis available")

    # Return the analysis object directly (no wrapper), matching frontend expectations.
    return _latest_analysis_result.model_dump()
