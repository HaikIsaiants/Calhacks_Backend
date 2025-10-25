## Objective
Build a Letta agent that ingests lab notebooks (data tables, lab notes, protein structures/sequences, experiment protocols) and produces a concise plain-English summary of the current experiment status.

## 1. Environment & Secrets
- Add `.env` with `LETTA_API_KEY`, `LETTA_AGENT_ID`, and any storage credentials; keep `.env` ignored.
- Install required libraries: `letta`, `python-dotenv`, `pydantic`, `pandas`, `biopython` (or other parsers), `pytest`.
- Create a reusable config loader that validates required env vars on startup.

## 2. Notebook Ingestion Pipeline
- Define supported notebook formats (directory of files, .zip, Jupyter `.ipynb`, etc.).
- Implement parsers for:
  - Lab notes (Markdown/Plain text).
  - Data tables (CSV/TSV via `pandas`).
  - Protein structures/sequences (PDB/FASTA via `biopython`).
  - Protocol docs (PDF/Text via existing parser or TODO placeholder).
- Normalize parsed content into a shared schema: `{source, content_type, metadata, text}`.
- Write unit tests covering representative notebook samples.

## 3. Tooling for Letta Agent
- Wrap ingestion pipeline in Letta tools:
  - `list_notebook_assets(notebook_id)` returns manifest.
  - `load_notebook_section(notebook_id, section_id)` streams normalized text.
  - Optional: analysis helpers (e.g., compute stats on data tables).
- Register tools using SDK: define JSON schemas, link callable functions.
- Document tool usage expectations in agent instructions.

## 4. Memory & Retrieval Strategy
- Choose memory blocks (short-term scratchpad + long-term vector store).
- Index normalized notebook chunks into vector store with metadata (experiment id, date).
- Expose retrieval tool that lets the agent fetch relevant past experiments.
- Add tests ensuring embeddings and retrieval return expected sections.

## 5. Agent Policy & Prompting
- Craft system prompt: role, goals, tone, constraints (plain-English summary, highlight anomalies, pending actions).
- Define conversation start template giving agent context about incoming notebook payload.
- Configure reasoning mode (e.g., ReAct) and set max tool calls / depth limits.
- Maintain prompt + config in version-controlled module for reproducibility.

## 6. Execution Flow
- Build a driver function: `run_notebook_review(notebook_path, experiment_id)` that
  1. Parses notebook.
  2. Uploads/updates notebook artifacts if needed.
  3. Calls `client.run_agent` with initial message referencing notebook id.
  4. Collects final agent summary + intermediate notes.
- Log runs (timestamps, prompt tokens, cost estimates) for observability.

## 7. Output Handling
- Define response schema (summary, key findings, action items, confidence).
- Validate agent output against schema; fall back to descriptive error if malformed.
- Persist summaries to database (placeholder if DB not ready) and optionally notify downstream systems (webhook, email).

## 8. Testing & Evaluation
- Assemble benchmark notebooks with known “correct” summaries.
- Write automated evaluation harness comparing agent outputs to expected highlights (semantic comparison + manual review checklist).
- Monitor tool usage and fallback when parser fails; add regression tests for bug fixes.

## 9. Deployment & Operations
- Package code into backend service or cron job; integrate with project’s deployment pipeline.
- Provide CLI entry point for ad-hoc reviews (`python -m notebooks.review path/to/notebook`).
- Set up error tracking/monitoring (Sentry or logs).
- Document runbook: how to rotate API keys, handle failures, extend parsers/tools.

## 10. Future Enhancements (Backlog)
- Add multimodal support (images/plots) via vision model tool.
- Implement active learning loop to capture human feedback and refine summaries.
- Explore cost optimization (batched retrieval, caching, selective parsing).
