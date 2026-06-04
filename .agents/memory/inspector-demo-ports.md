---
name: Inspector demo server ports & chat API
description: How to reach/test the ActiveGraph Inspector demo server and its chat endpoint locally.
---

The Python demo server (packs/demo_server.py) listens on **localhost:7788**.
The Express api-server listens on **:8080** and proxies to it.

**Testing:** curl the demo server directly on `localhost:7788`. Curling via
`$REPLIT_DEV_DOMAIN` returns HTTP 000 — a proxy connectivity quirk, not a server
failure. After editing demo_server.py, restart the `artifacts/api-server` workflow
(it launches the Python process).

**Chat endpoint:** POST /chat expects body `{"content": "..."}` (NOT `message`).
Response returns the assistant reply in the `content` field, plus `llm_mode`
(mock|live), `frame_id`, `turn_id`, `new_objects`, etc.

**Config/secrets:** GET/POST /chat/config and GET/POST /secrets. POST /secrets sets
`os.environ` in-process only (never persisted to graph/events/disk); it writes a
name-only credential_ref and rejects reserved env names (PATH, PYTHONPATH, etc.).
POST /reset wipes the store back to seeded demo state (clears test credential_refs).
