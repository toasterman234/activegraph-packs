"""Chat Adapter Pack tools — v0.1."""

from __future__ import annotations

from typing import Optional

from activegraph.packs import tool


# ── Plain implementation functions (callable from fixtures/tests) ─────────────


def submit_chat_input_fn(
    graph,
    user_ref: str,
    content: str,
    session_id: Optional[str] = None,
    frame_id: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """Submit a chat message from a user. Returns the ChatInput object."""
    return graph.add_object("chat_input", {
        "user_ref": user_ref,
        "content": content,
        "session_id": session_id,
        "frame_id": frame_id,
        "role": "user",
        "metadata": metadata or {},
    })


def get_session_turns_fn(graph, session_id: str) -> list:
    """Return all ChatTurn objects for a session, ordered by turn_number."""
    from packs.chat.behaviors import _MESSAGE_TO_TURN, _MESSAGE_TO_SESSION
    turn_ids = list({
        turn_id
        for msg_id, turn_id in _MESSAGE_TO_TURN.items()
        if _MESSAGE_TO_SESSION.get(msg_id) == session_id
    })
    turns = []
    for tid in turn_ids:
        try:
            obj = graph.get_object(tid)
            if obj:
                turns.append(obj)
        except Exception:
            pass
    return sorted(turns, key=lambda t: t.data.get("turn_number", 0))


# ── Decorated @tool wrappers ──────────────────────────────────────────────────


@tool(
    name="submit_chat_input",
    description=(
        "Submit a chat message from a user. Creates ChatInput → triggers chat_ingester → "
        "CommMessage + ChatSession + ChatTurn → chat_llm_responder → CommResponseCandidate → "
        "chat_responder delivers response."
    ),
)
def submit_chat_input(
    graph,
    user_ref: str,
    content: str,
    session_id: Optional[str] = None,
    frame_id: Optional[str] = None,
):
    return submit_chat_input_fn(graph, user_ref=user_ref, content=content,
                                 session_id=session_id, frame_id=frame_id)


@tool(
    name="get_session_turns",
    description="Return all ChatTurn objects for a given session_id (ordered by turn_number).",
)
def get_session_turns(graph, session_id: str) -> list:
    return get_session_turns_fn(graph, session_id=session_id)


TOOLS = [submit_chat_input, get_session_turns]
