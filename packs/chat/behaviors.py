"""Chat Adapter Pack behaviors — v0.1.

Behaviors:
  chat_ingester       — chat_input.created → Source + CommMessage + ChatSession + ChatTurn
  chat_llm_responder  — comm_message.created (channel=chat, inbound) → CommResponseCandidate
  chat_responder      — comm_response_candidate.created (channel=chat, approved) → ChatTurn updated

Session registry:
  _SESSION_REGISTRY maps user_ref → {"session_id", "thread_id_hint", "turn_count"}
  _MESSAGE_TO_TURN maps comm_message_id → chat_turn_id
  _MESSAGE_TO_SESSION maps comm_message_id → session_id
  _SESSION_TURN_HISTORY maps session_id → [{"turn_number", "user", "assistant"}]
  Call clear_session_registry() between test fixtures.

Thread continuity:
  CommMessage.metadata.thread_id_hint is set to session_id so each session gets its
  own distinct comm_thread (keyed "chat::<session_id>" by thread_tracker).

LLM wiring (native):
  chat_llm_responder is an @llm_behavior — the runtime owns the LLM lifecycle
  (emits llm.requested → provider.complete() → llm.responded) and assembles the
  prompt from the triggering comm_message plus a scoped graph view. The active
  provider is set on the Runtime (see packs/chat/llm.py: select_chat_provider).
  With no provider key configured the MockChatProvider serves an instructive
  canned reply, so the full pipeline runs end-to-end without an API key.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from activegraph.packs import behavior, llm_behavior

from .llm import ChatReply
from .settings import ChatSettings

# ================================================================ Session registry

_SESSION_REGISTRY: dict[str, dict] = {}
_MESSAGE_TO_TURN: dict[str, str] = {}
_MESSAGE_TO_SESSION: dict[str, str] = {}
_SESSION_TURN_HISTORY: dict[str, list] = {}


def clear_session_registry() -> None:
    """Reset session registries — call between test fixtures."""
    _SESSION_REGISTRY.clear()
    _MESSAGE_TO_TURN.clear()
    _MESSAGE_TO_SESSION.clear()
    _SESSION_TURN_HISTORY.clear()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ================================================================ Behaviors


@behavior(
    name="chat_ingester",
    on=["object.created"],
    where={"object.type": "chat_input"},
    creates=["source", "comm_message", "chat_session", "chat_turn"],
)
def chat_ingester(event, graph, ctx, *, settings: ChatSettings):
    """Translate ChatInput into CommMessage + ChatSession + ChatTurn.

    On: object.created (chat_input)
    Creates: source(kind=chat_message), comm_message(channel=chat, inbound),
             chat_session (or resumes), chat_turn
    Relations: derived_from_source, session_contains_turn, turn_from_input

    Session continuity: resumes existing session by user_ref (or explicit session_id).
    Thread continuity: uses session_id as thread_id_hint so thread_tracker creates a
      per-session comm_thread (key="chat::<session_id>") rather than a shared root.
    CommThread is created downstream by thread_tracker (Communication Pack).
    """
    obj = event.payload.get("object", {})
    input_id = obj.get("id")
    inp = obj.get("data", {})

    user_ref = inp.get("user_ref") or "unknown_user"
    content = inp.get("content") or ""
    given_session_id = inp.get("session_id")
    frame_id = inp.get("frame_id")
    now = _now_iso()

    # ── 1. Resolve or create ChatSession ──────────────────────────────────
    session_key = user_ref
    reg = None

    if given_session_id:
        for k, v in _SESSION_REGISTRY.items():
            if v.get("session_id") == given_session_id:
                reg = v
                session_key = k
                break

    if reg is None and session_key in _SESSION_REGISTRY:
        reg = _SESSION_REGISTRY[session_key]

    if reg is not None:
        session_id = reg["session_id"]
        # thread_id_hint = session_id ensures we reuse the same comm_thread
        thread_id_hint = reg.get("thread_id_hint") or session_id
        turn_count = reg["turn_count"] + 1
    else:
        try:
            session_obj = graph.add_object("chat_session", {
                "user_ref": user_ref,
                "started_at": now,
                "status": "active",
                "turn_count": 0,
                "llm_config": {},
                "frame_id": frame_id,
            })
            session_id = session_obj.id
        except Exception:
            return
        # Use session_id as the hint so each session → unique comm_thread
        thread_id_hint = session_id
        turn_count = 1

    # ── 2. Create Core Source ──────────────────────────────────────────────
    try:
        source = graph.add_object("source", {
            "kind": "chat_message",
            "content": content,
            "channel": "chat",
            "sender_ref": user_ref,
            "frame_id": frame_id,
            "metadata": {
                "session_id": session_id,
                "turn_number": turn_count,
            },
        })
        source_id = source.id
    except Exception:
        return

    # ── 3. Create CommMessage ──────────────────────────────────────────────
    try:
        comm_msg = graph.add_object("comm_message", {
            "channel": "chat",
            "sender_ref": user_ref,
            "content": content,
            "direction": "inbound",
            "source_id": source_id,
            "thread_id": None,
            "frame_id": frame_id,
            "metadata": {
                "thread_id_hint": thread_id_hint,
                "session_id": session_id,
            },
        })
        comm_msg_id = comm_msg.id
    except Exception:
        return

    try:
        graph.add_relation("derived_from_source", comm_msg_id, source_id)
    except Exception:
        pass

    # ── 4. Create ChatTurn ─────────────────────────────────────────────────
    try:
        turn = graph.add_object("chat_turn", {
            "session_id": session_id,
            "user_message": content,
            "assistant_message": None,
            "turn_number": turn_count,
            "comm_message_id": comm_msg_id,
            "frame_id": frame_id,
        })
        turn_id = turn.id
    except Exception:
        return

    try:
        graph.add_relation("session_contains_turn", session_id, turn_id)
    except Exception:
        pass
    try:
        graph.add_relation("turn_from_input", turn_id, input_id)
    except Exception:
        pass

    # ── 5. Update session turn count + registries ──────────────────────────
    try:
        graph.patch_object(session_id, {"turn_count": turn_count})
    except Exception:
        pass

    _MESSAGE_TO_TURN[comm_msg_id] = turn_id
    _MESSAGE_TO_SESSION[comm_msg_id] = session_id
    _SESSION_REGISTRY[session_key] = {
        "session_id": session_id,
        "thread_id_hint": thread_id_hint,
        "turn_count": turn_count,
    }

    # ── 6. Record in turn history for context assembly ─────────────────────
    if session_id not in _SESSION_TURN_HISTORY:
        _SESSION_TURN_HISTORY[session_id] = []
    _SESSION_TURN_HISTORY[session_id].append({
        "turn_number": turn_count,
        "user": content,
        "assistant": None,
        "_turn_id": turn_id,
    })


@llm_behavior(
    name="chat_llm_responder",
    on=["object.created"],
    # Scoped precisely so the (potentially paid) LLM call fires only for
    # inbound chat messages — never for outbound/email/other comm traffic.
    where={
        "object.type": "comm_message",
        "object.data.channel": "chat",
        "object.data.direction": "inbound",
    },
    description=(
        "You are the assistant in an ActiveGraph-powered chat. Read the user's "
        "most recent message (the triggering comm_message) together with any "
        "prior context in the graph view, then reply helpfully and concisely."
    ),
    output_schema=ChatReply,
    # model=None → the runtime resolves the model from the active provider's
    # default_model at call time (set via packs/chat/llm.py: select_chat_provider).
    # This also skips cross-family model validation, which a static model name
    # would trip when the configured provider differs.
    model=None,
    view={
        "around": "event.payload.object.id",
        "depth": 1,
        "recent_events": 15,
    },
    creates=["comm_response_candidate"],
    temperature=0.7,
    max_tokens=1024,
)
def chat_llm_responder(event, graph, ctx, out, *, settings: ChatSettings):
    """Produce a CommResponseCandidate for inbound chat messages (native LLM).

    On: object.created (comm_message, channel=chat, direction=inbound)
    Creates: comm_response_candidate (status=approved if auto_approve_responses=True)
    Relations: response_to

    The runtime drives the LLM (emitting llm.requested/llm.responded events) and
    hands us ``out`` — a parsed :class:`ChatReply`. We map ``out.reply`` onto a
    CommResponseCandidate; chat_responder then writes it to the ChatTurn.
    """
    obj = event.payload.get("object", {})
    msg_id = obj.get("id")
    msg_data = obj.get("data", {})

    thread_id = msg_data.get("thread_id")
    frame_id = msg_data.get("frame_id")
    session_id = _MESSAGE_TO_SESSION.get(msg_id)

    response_content = (getattr(out, "reply", None) or "").strip()
    if not response_content:
        return

    status = "approved" if settings.auto_approve_responses else "proposed"

    try:
        candidate = graph.add_object("comm_response_candidate", {
            "message_id": msg_id,
            "thread_id": thread_id,
            "channel": "chat",
            "content": response_content,
            "status": status,
            "created_by_behavior": "chat_llm_responder",
            "frame_id": frame_id,
            "context_turn_count": len(
                _SESSION_TURN_HISTORY.get(session_id or "", [])
            ),
        })
        graph.add_relation("response_to", candidate.id, msg_id)
    except Exception:
        pass


@behavior(
    name="chat_responder",
    on=["object.created"],
    where={"object.type": "comm_response_candidate"},
)
def chat_responder(event, graph, ctx, *, settings: ChatSettings):
    """Deliver approved chat responses by updating ChatTurn.assistant_message.

    On: object.created (comm_response_candidate, channel=chat, status=approved)
    Patches: chat_turn.assistant_message + response_candidate_id

    Also updates _SESSION_TURN_HISTORY with the assistant message so subsequent
    turns have full Q&A context available to chat_llm_responder.

    This is the 'delivery' step for the chat channel. After this fires,
    response_dispatcher (Communication Pack) marks the candidate as 'sent'.
    """
    obj = event.payload.get("object", {})
    candidate_id = obj.get("id")
    data = obj.get("data", {})

    if data.get("channel") != "chat":
        return
    if data.get("status") != "approved":
        return

    message_id = data.get("message_id")
    response_content = data.get("content") or ""

    turn_id = _MESSAGE_TO_TURN.get(message_id)
    if turn_id:
        try:
            graph.patch_object(turn_id, {
                "assistant_message": response_content,
                "response_candidate_id": candidate_id,
            })
        except Exception:
            pass

    # Update turn history so next turns have assistant context
    session_id = _MESSAGE_TO_SESSION.get(message_id)
    if session_id and session_id in _SESSION_TURN_HISTORY:
        history = _SESSION_TURN_HISTORY[session_id]
        for entry in reversed(history):
            if entry.get("_turn_id") == turn_id:
                entry["assistant"] = response_content
                break


# ================================================================ BEHAVIORS registry

BEHAVIORS = [chat_ingester, chat_llm_responder, chat_responder]
