#!/usr/bin/env python3
"""ActiveGraph Inspector Demo Server.

Runs an ActiveGraph runtime with the Assistant Bundle loaded and seeded
with demo data.  Exposes a lightweight JSON REST API that the Express
API server proxies to the React Inspector UI.

Usage:
    python packs/demo_server.py [--port PORT]

Port defaults to env var ACTIVEGRAPH_PORT or 7788.
"""

from __future__ import annotations

import os
import sys

# ── sys.path fix ──────────────────────────────────────────────────────────────
# When this file is run as a script, Python inserts the script's directory
# (packs/) into sys.path[0].  That causes packs/email/__init__.py to shadow
# the stdlib 'email' package, breaking http.server (which imports email.utils).
# Remove the packs/ dir and ensure the workspace root is on the path instead.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_workspace = os.path.dirname(_this_dir)
if _this_dir in sys.path:
    sys.path.remove(_this_dir)
if _workspace not in sys.path:
    sys.path.insert(0, _workspace)

import json
import threading
import traceback
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

# ─── Runtime singleton ────────────────────────────────────────────────────────

_runtime_lock = threading.Lock()
_rt = None                  # the live Runtime
_initial_events: list = []  # events captured at startup (for reset)
_frames: dict = {}          # frame_id -> {id, status, started_at, ended_at, events[]}

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _build_runtime():
    """Create and seed a fresh runtime, register frame tracking."""
    from bundles import build_assistant

    rt = build_assistant()

    # Attach a listener to collect frame events
    def _on_evt(evt):
        fid = getattr(evt, "frame_id", None)
        if fid and fid not in _frames:
            _frames[fid] = {
                "id": fid,
                "status": "running",
                "frame_type": "behavior",
                "started_at": _ts(),
                "ended_at": None,
                "event_count": 0,
                "events": [],
            }
        if fid and fid in _frames:
            _frames[fid]["event_count"] += 1
            _frames[fid]["events"].append(_event_to_dict(evt))
            if evt.type in ("frame.completed", "frame.failed", "runtime.idle"):
                _frames[fid]["status"] = "completed" if evt.type != "frame.failed" else "failed"
                _frames[fid]["ended_at"] = _ts()

    rt.graph.add_listener(_on_evt)

    # ── Seed demo objects ──────────────────────────────────────────────────
    rt.graph.add_object("source", {
        "kind": "chat_message",
        "content": "What is the current deal status for Northwind Robotics?",
        "channel": "chat",
        "sender_ref": "user:alice",
    })
    rt.graph.add_object("source", {
        "kind": "email",
        "content": "Please review the attached term sheet for the Series B round.",
        "channel": "email",
        "sender_ref": "founder@northwind.ai",
    })
    rt.graph.add_object("source", {
        "kind": "meeting_note",
        "content": "Kickoff call with Northwind team. Strong ARR traction, 3x YoY.",
        "channel": "internal",
        "sender_ref": "user:bob",
    })
    rt.graph.add_object("source", {
        "kind": "url",
        "content": "https://arxiv.org/abs/2312.00752",
        "channel": "api",
        "sender_ref": "user:alice",
    })

    rt.run_until_idle()
    return rt


def _get_rt():
    global _rt
    if _rt is None:
        with _runtime_lock:
            if _rt is None:
                _rt = _build_runtime()
    return _rt


def _reset_rt():
    global _rt, _frames
    with _runtime_lock:
        _frames = {}
        _rt = _build_runtime()


# ─── Serialisation helpers ────────────────────────────────────────────────────

def _event_to_dict(evt) -> dict:
    payload = {}
    try:
        p = evt.payload
        if p is not None:
            payload = p if isinstance(p, dict) else vars(p)
    except Exception:
        pass

    # Infer pack / behavior / object info from payload or actor
    pack_name = None
    behavior_name = None
    object_type = None
    object_id = None

    try:
        actor = getattr(evt, "actor", None) or {}
        if isinstance(actor, dict):
            pack_name = actor.get("pack")
            behavior_name = actor.get("behavior")
        if isinstance(payload, dict):
            object_type = payload.get("object_type") or payload.get("type")
            object_id = payload.get("object_id") or payload.get("id")
    except Exception:
        pass

    return {
        "id": str(evt.id),
        "event_type": str(evt.type),
        "timestamp": str(evt.timestamp) if evt.timestamp else _ts(),
        "pack": pack_name,
        "behavior_name": behavior_name,
        "frame_id": str(evt.frame_id) if evt.frame_id else None,
        "object_type": object_type,
        "object_id": str(object_id) if object_id else None,
        "payload": _safe_json(payload),
    }


def _object_to_dict(obj) -> dict:
    pack_name = "unknown"
    try:
        # object id format: "<type>#<n>"  e.g. "source#1"
        t = str(obj.type)
        # try to look up which pack declares this type
        rt = _rt
        if rt:
            for p in rt.loaded_packs():
                for ot in p.object_types:
                    if ot.name == t:
                        pack_name = p.name
                        break
    except Exception:
        pass

    data = {}
    try:
        raw = obj.data
        if raw is not None:
            data = raw if isinstance(raw, dict) else vars(raw)
        data = _safe_json(data)
    except Exception:
        pass

    created_at = None
    try:
        provenance = obj.provenance
        if provenance:
            created_at = str(provenance.get("timestamp", ""))
    except Exception:
        pass

    return {
        "id": str(obj.id),
        "type": str(obj.type),
        "pack": pack_name,
        "data": data,
        "created_at": created_at,
    }


def _relation_to_dict(rel) -> dict:
    data = {}
    try:
        raw = rel.data
        if raw is not None:
            data = raw if isinstance(raw, dict) else vars(raw)
        data = _safe_json(data)
    except Exception:
        pass
    return {
        "id": str(rel.id),
        "type": str(rel.type),
        "source_id": str(rel.source_id),
        "target_id": str(rel.target_id),
        "data": data,
    }


def _pack_to_dict(pack) -> dict:
    behaviors = []
    for b in pack.behaviors:
        behaviors.append({
            "name": b.name,
            "trigger": str(b.on[0]) if b.on else None,
            "description": None,
            "creates": list(b.creates) if b.creates else [],
            "capabilities": [],
        })

    object_types = []
    for ot in pack.object_types:
        desc = None
        try:
            desc = ot.schema.__doc__
            if desc:
                desc = desc.strip().split("\n")[0]
        except Exception:
            pass
        object_types.append({"name": ot.name, "description": desc})

    relation_types = []
    try:
        for rt_type in pack.relation_types:
            relation_types.append({
                "name": rt_type.name,
                "source_types": list(rt_type.source_types) if rt_type.source_types else [],
                "target_types": list(rt_type.target_types) if rt_type.target_types else [],
                "description": rt_type.description if hasattr(rt_type, "description") else None,
            })
    except Exception:
        pass

    return {
        "name": pack.name,
        "version": str(pack.version),
        "description": pack.description if hasattr(pack, "description") else None,
        "object_types": object_types,
        "relation_types": relation_types,
        "behaviors": behaviors,
    }


def _safe_json(obj: Any) -> Any:
    """Recursively convert obj to JSON-safe types."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(i) for i in obj]
    try:
        return str(obj)
    except Exception:
        return None


# ─── HTTP handler ─────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # suppress default access logs (noisy)
        pass

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, msg: str, status: int = 500):
        self._send_json({"error": msg}, status)

    def _parse_qs(self) -> dict:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        return {k: v[0] for k, v in qs.items()}

    def _path(self) -> str:
        return urlparse(self.path).path

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self._path()
        qs = self._parse_qs()
        try:
            if path == "/trace":
                self._handle_trace(qs)
            elif path == "/graph":
                self._handle_graph(qs)
            elif path == "/packs":
                self._handle_packs()
            elif path == "/frames":
                self._handle_frames()
            elif path == "/summary":
                self._handle_summary()
            elif path == "/health":
                self._send_json({"status": "ok"})
            else:
                self._send_error("Not found", 404)
        except Exception as e:
            traceback.print_exc()
            self._send_error(str(e), 500)

    def do_POST(self):
        path = self._path()
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        try:
            if path == "/chat":
                self._handle_chat(body)
            elif path == "/reset":
                self._handle_reset()
            else:
                self._send_error("Not found", 404)
        except Exception as e:
            traceback.print_exc()
            self._send_error(str(e), 500)

    # ── GET /trace ─────────────────────────────────────────────────────────

    def _handle_trace(self, qs: dict):
        rt = _get_rt()
        limit = int(qs.get("limit", 200))
        offset = int(qs.get("offset", 0))
        pack_filter = qs.get("pack")
        frame_filter = qs.get("frame_id")
        type_filter = qs.get("event_type")

        events = [_event_to_dict(e) for e in rt.graph.events]

        if pack_filter:
            events = [e for e in events if e.get("pack") == pack_filter]
        if frame_filter:
            events = [e for e in events if e.get("frame_id") == frame_filter]
        if type_filter:
            events = [e for e in events if type_filter in e.get("event_type", "")]

        total = len(events)
        page = events[offset : offset + limit]

        self._send_json({
            "events": page,
            "total": total,
            "offset": offset,
            "limit": limit,
        })

    # ── GET /graph ─────────────────────────────────────────────────────────

    def _handle_graph(self, qs: dict):
        rt = _get_rt()
        pack_filter = qs.get("pack")

        objects = [_object_to_dict(o) for o in rt.graph.all_objects()]
        relations = [_relation_to_dict(r) for r in rt.graph.all_relations()]

        if pack_filter:
            objects = [o for o in objects if o.get("pack") == pack_filter]
            obj_ids = {o["id"] for o in objects}
            relations = [r for r in relations
                         if r["source_id"] in obj_ids or r["target_id"] in obj_ids]

        self._send_json({
            "objects": objects,
            "relations": relations,
            "object_count": len(objects),
            "relation_count": len(relations),
        })

    # ── GET /packs ─────────────────────────────────────────────────────────

    def _handle_packs(self):
        rt = _get_rt()
        packs = [_pack_to_dict(p) for p in rt.loaded_packs()]
        self._send_json({"packs": packs, "total": len(packs)})

    # ── GET /frames ────────────────────────────────────────────────────────

    def _handle_frames(self):
        frames = list(_frames.values())
        # Sort newest-first
        frames.sort(key=lambda f: f.get("started_at") or "", reverse=True)
        self._send_json({"frames": frames, "total": len(frames)})

    # ── GET /summary ───────────────────────────────────────────────────────

    def _handle_summary(self):
        rt = _get_rt()
        objects = rt.graph.all_objects()
        relations = rt.graph.all_relations()
        events = rt.graph.events
        packs = rt.loaded_packs()

        # Count by type + pack
        type_counts: dict[str, dict] = {}
        for o in objects:
            key = f"{o.type}|{_object_to_dict(o)['pack']}"
            if key not in type_counts:
                type_counts[key] = {"type": str(o.type), "pack": _object_to_dict(o)['pack'], "count": 0}
            type_counts[key]["count"] += 1

        self._send_json({
            "object_count": len(objects),
            "relation_count": len(relations),
            "event_count": len(events),
            "pack_count": len(packs),
            "frame_count": len(_frames),
            "by_type": list(type_counts.values()),
            "runtime_ready": True,
        })

    # ── POST /chat ─────────────────────────────────────────────────────────

    def _handle_chat(self, body: dict):
        rt = _get_rt()
        content = (body.get("content") or "").strip()
        if not content:
            self._send_error("content is required", 400)
            return

        frame_id = str(uuid.uuid4())

        objects_before = set(o.id for o in rt.graph.all_objects())
        events_before = len(rt.graph.events)

        # Inject as a chat_message source
        rt.graph.add_object("source", {
            "kind": "chat_message",
            "content": content,
            "channel": "chat",
            "frame_id": frame_id,
            "sender_ref": body.get("user_ref") or "user:inspector",
        })

        rt.run_until_idle()

        objects_after = rt.graph.all_objects()
        new_obj_ids = [str(o.id) for o in objects_after if o.id not in objects_before]

        # Register this as a frame
        events_after = len(rt.graph.events)
        _frames[frame_id] = {
            "id": frame_id,
            "status": "completed",
            "frame_type": "chat",
            "started_at": _ts(),
            "ended_at": _ts(),
            "event_count": events_after - events_before,
            "events": [_event_to_dict(e) for e in rt.graph.events[events_before:]],
        }

        # Build a reply from new artifacts/observations
        reply_lines = []
        for o in objects_after:
            if o.id not in objects_before:
                d = _object_to_dict(o)
                if d["type"] in ("artifact", "observation", "task"):
                    content_str = (d["data"] or {}).get("content") or (d["data"] or {}).get("title") or str(d["id"])
                    reply_lines.append(f"[{d['type']}] {content_str}")

        if reply_lines:
            reply = "Created:\n" + "\n".join(reply_lines[:8])
        else:
            reply = f"Processed message. {len(new_obj_ids)} new object(s) added to the graph."

        self._send_json({
            "content": reply,
            "frame_id": frame_id,
            "user_message": content,
            "event_count": events_after - events_before,
            "new_objects": new_obj_ids,
        })

    # ── POST /reset ────────────────────────────────────────────────────────

    def _handle_reset(self):
        _reset_rt()
        self._send_json({"success": True, "message": "Runtime reset to initial demo state."})


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    port = int(os.environ.get("ACTIVEGRAPH_PORT", "7788"))
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    # Eagerly init so first request is fast
    print(f"[demo_server] Initialising ActiveGraph runtime...", flush=True)
    _get_rt()
    print(f"[demo_server] Runtime ready. Listening on :{port}", flush=True)

    server = HTTPServer(("0.0.0.0", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
