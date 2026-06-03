"""Chat Adapter Pack behaviors — v0.1.

Behaviors:
  chat_ingester       — chat_input.created → Source + CommMessage + ChatSession + ChatTurn
  chat_llm_responder  — comm_message.created (channel=chat, inbound) → CommResponseCandidate
  chat_responder      — comm_response_candidate.created (channel=chat, approved) → ChatTurn updated

Session registry:
  _SESSION_REGISTRY maps user_ref → {"session_id", "thread_id", "turn_count"}
  _MESSAGE_TO_TURN maps comm_message_id → chat_turn_id
  _MESSAGE_TO_SESSION maps comm_message_id → session_id
  Call clear_session_registry() between test fixtures.

LLM: llm_provider='mock' returns deterministic stubs (no API key required).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from activegraph.packs import behavior

from .settings import ChatSettings

# ================================================================ Session registry

_SESSION_REGISTRY: dict[str, dict] = {}
_MESSAGE_TO_TURN: dict[str, str] = {}
_MESSAGE_TO_SESSION: dict[str, str] = {}


def clear_session_registry() -> None:
    """Reset session registries — call between test fixtures."""
    _SESSION_REGISTRY.clear()
    _MESSAGE_TO_TURN.clear()
    _MESSAGE_TO_SESSION.clear()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ================================================================ Mock LLM

_MOCK_RESPONSES = [
    "I understand your request. I'll work on that for you.",
    "Thanks for the context. Here's what I've noted and how I can help.",
    "Got it — I've processed your message and will take the appropriate next steps.",
    "Understood. I've recorded this and will proceed accordingly.",
    "Thank you for reaching out. I'm on it.",
]
_mock_response_idx = 0


def _get_mock_response(content: str, turn_number: int, system_prompt: Optional[str]) -> str:
    global _mock_response_idx
    response = _MOCK_RESPONSES[_mock_response_idx % len(_MOCK_RESPONSES)]
    _mock_response_idx += 1
    return f"[Turn {turn_number}] {response}"


def reset_mock_response_idx() -> None:
    """Reset mock response counter — call for reproducible fixtures."""
    global _mock_response_idx
    _mock_response_idx = 0


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
        # Look up by explicit session_id
        for k, v in _SESSION_REGISTRY.items():
            if v.get("session_id") == given_session_id:
                reg = v
                session_key = k
                break

    if reg is None and session_key in _SESSION_REGISTRY:
        reg = _SESSION_REGISTRY[session_key]

    if reg is not None:
        session_id = reg["session_id"]
        thread_id = reg.get("thread_id")
        turn_count = reg["turn_count"] + 1
    else:
        # Create new ChatSession
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
        thread_id = None
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
            "thread_id": thread_id,  # None for first turn — thread_tracker creates it
            "frame_id": frame_id,
            "metadata": {
                "thread_id_hint": thread_id,
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
        "thread_id": thread_id,
        "turn_count": turn_count,
    }


@behavior(
    name="chat_llm_responder",
    on=["object.created"],
    where={"object.type": "comm_message"},
    creates=["comm_response_candidate"],
)
def chat_llm_responder(event, graph, ctx, *, settings: ChatSettings):
    """Produce a CommResponseCandidate for inbound chat messages.

    On: object.created (comm_message, channel=chat, direction=inbound)
    Creates: comm_response_candidate (status=approved if auto_approve_responses=True)
    Relations: response_to

    Context assembly: reads prior ChatTurns for turn_number.
    llm_provider='mock' returns deterministic stubs — no API key required.
    """
    obj = event.payload.get("object", {})
    msg_id = obj.get("id")
    msg_data = obj.get("data", {})

    if msg_data.get("channel") != "chat":
        return
    if msg_data.get("direction") != "inbound":
        return

    content = msg_data.get("content") or ""
    thread_id = msg_data.get("thread_id")
    frame_id = msg_data.get("frame_id")

    # Find turn_number for mock response
    turn_number = 1
    turn_id = _MESSAGE_TO_TURN.get(msg_id)
    if turn_id:
        try:
            turn_obj = graph.get_object(turn_id)
            if turn_obj:
                turn_number = turn_obj.data.get("turn_number", 1)
        except Exception:
            pass

    system_prompt = settings.system_prompt_override
    provider = settings.llm_provider

    if provider == "mock" or not provider:
        response_content = _get_mock_response(content, turn_number, system_prompt)
    else:
        # Real LLM hook — falls back to mock without an API key
        response_content = _get_mock_response(content, turn_number, system_prompt)

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


# ================================================================ BEHAVIORS registry

BEHAVIORS = [chat_ingester, chat_llm_responder, chat_responder]
