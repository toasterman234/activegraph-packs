"""Chat Adapter Pack behaviors — v0.2.

Behaviors:
  chat_ingester          — chat_input.created → Source + CommMessage + ChatSession + ChatTurn
  chat_context_assembler — comm_message.created (chat, inbound) → ChatContext (graph-native memory)
  chat_llm_responder     — comm_message.created (chat, inbound) → CommResponseCandidate
  chat_responder         — comm_response_candidate.created (chat, approved) → ChatTurn updated

Graph-native conversation memory (v0.2):
  Conversation memory is reconstructed from the graph, not from process memory.
  chat_context_assembler reads prior ChatTurns for the session (linked via
  session_contains_turn), formats them into a ChatContext, and links it to the
  inbound CommMessage. chat_llm_responder's depth-1 view then captures that
  ChatContext, so the prior turns reach the LLM. Because the turns are read from
  persisted graph objects, conversation context survives an API-server restart
  mid-session and needs no in-process state. See chat_context_assembler for the
  two approaches considered and why this one was chosen.

In-process maps (convenience caches only — never the source of truth):
  _SESSION_REGISTRY    user_ref → {"session_id", "turn_count"} — resume-by-user shortcut.
  _MESSAGE_TO_TURN     comm_message_id → chat_turn_id — delivery plumbing for chat_responder.
  _MESSAGE_TO_SESSION  comm_message_id → session_id — delivery plumbing.
  Every value these hold is also derivable from the graph; the behaviors fall
  back to graph lookups when a cache misses (e.g. after a restart). They exist
  purely to avoid graph scans on the hot path. Call clear_session_registry()
  between test fixtures.

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

# ================================================================ Session caches
# These are convenience caches, NOT the source of truth. Conversation memory and
# session identity live in the graph; these maps just avoid graph scans on the
# hot path and are rebuilt opportunistically. Behaviors fall back to the graph
# when a cache misses (e.g. after a restart wipes them).

_SESSION_REGISTRY: dict[str, dict] = {}
_MESSAGE_TO_TURN: dict[str, str] = {}
_MESSAGE_TO_SESSION: dict[str, str] = {}


def clear_session_registry() -> None:
    """Reset the in-process caches — call between test fixtures (and a useful
    way to simulate an API-server restart, since the graph is the real store)."""
    _SESSION_REGISTRY.clear()
    _MESSAGE_TO_TURN.clear()
    _MESSAGE_TO_SESSION.clear()


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
    # Resolution order, graph-first so it is restart-safe:
    #   1. Explicit session_id → resume directly from the persisted ChatSession
    #      object (graph.get_object). This is what the Inspector UI sends, and
    #      it works even after a restart has wiped the in-process caches.
    #   2. No session_id → resume the user's most recent session via the
    #      _SESSION_REGISTRY cache (a convenience; falls through to a new
    #      session on a cache miss).
    #   3. Otherwise → create a new session.
    session_key = user_ref
    session_id: Optional[str] = None
    turn_count = 1

    if given_session_id:
        try:
            sess = graph.get_object(given_session_id)
        except Exception:
            sess = None
        if sess is not None:
            session_id = given_session_id
            turn_count = int(sess.data.get("turn_count", 0)) + 1

    if session_id is None and session_key in _SESSION_REGISTRY:
        reg = _SESSION_REGISTRY[session_key]
        session_id = reg["session_id"]
        turn_count = reg["turn_count"] + 1

    if session_id is None:
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
        turn_count = 1

    # thread_id_hint = session_id ensures each session maps to its own
    # comm_thread (keyed "chat::<session_id>" by thread_tracker).
    thread_id_hint = session_id

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
        graph.add_relation(comm_msg_id, source_id, "derived_from_source")
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
        graph.add_relation(session_id, turn_id, "session_contains_turn")
    except Exception:
        pass
    try:
        graph.add_relation(turn_id, input_id, "turn_from_input")
    except Exception:
        pass

    # ── 5. Update session turn count + registries ──────────────────────────
    try:
        graph.patch_object(session_id, {"turn_count": turn_count})
    except Exception:
        pass

    # Refresh the convenience caches (hot-path shortcuts, not the source of
    # truth — every value here is also recorded on the graph objects above).
    _MESSAGE_TO_TURN[comm_msg_id] = turn_id
    _MESSAGE_TO_SESSION[comm_msg_id] = session_id
    _SESSION_REGISTRY[session_key] = {
        "session_id": session_id,
        "turn_count": turn_count,
    }
    # NOTE (v0.2): no in-process turn history is recorded here. Prior turns are
    # read back from the graph by chat_context_assembler, which is what makes
    # conversation memory restart-safe.


@behavior(
    name="chat_context_assembler",
    on=["object.created"],
    where={
        "object.type": "comm_message",
        "object.data.channel": "chat",
        "object.data.direction": "inbound",
    },
    # ── How prior turns reach the LLM ──────────────────────────────────────
    # CONTRACT: the runtime builds every LLM prompt from the serialized graph
    # *view* — a behavior never hand-writes prompt text. So for the model to
    # "remember" earlier turns, those turns must appear in the responder's view.
    # Two ActiveGraph-idiomatic ways to achieve that:
    #
    #   (a) Widen chat_llm_responder's own view to reach the ChatSession and
    #       its turns. Simplest possible change, but: the turns arrive as raw,
    #       scattered chat_turn objects; the responder cannot bound them to
    #       max_context_messages (the view pulls *every* turn in the session);
    #       and "what context did we actually send?" is never recorded.
    #
    #   (b) THIS behavior: assemble one ChatContext object that the responder
    #       reads. Mirrors agent_profile's profile_context_provider
    #       (request → context view). The responder stays declarative — its
    #       existing depth-1 view captures the linked ChatContext for free — the
    #       context is bounded and pre-formatted, and the exact memory handed to
    #       the model becomes a first-class, inspectable graph object.
    #
    # We choose (b): a declarative responder plus auditable, bounded memory.
    #
    # The view below anchors at the ChatSession (resolved from the inbound
    # message's metadata.session_id) at depth 1, so it contains the session plus
    # every chat_turn linked by session_contains_turn. Prior turns are therefore
    # read from the *graph*, never an in-process dict — which is exactly why
    # conversation memory survives an API-server restart mid-session.
    view={
        "around": "event.payload.object.data.metadata.session_id",
        "depth": 1,
        "recent_events": 0,
    },
    creates=["chat_context"],
)
def chat_context_assembler(event, graph, ctx, *, settings: ChatSettings):
    """Assemble graph-native conversation memory for an inbound chat message.

    On: object.created (comm_message, channel=chat, direction=inbound)
    Creates: chat_context (the prior conversation, bounded + formatted)
    Relations: provides_context_for (chat_context → comm_message)

    Reads prior ChatTurns for the session from the session-anchored graph view,
    formats the most recent ``max_context_messages`` of them into a transcript,
    and links the result to the inbound message so chat_llm_responder's depth-1
    view picks it up. Skips silently on the first turn (no prior memory yet).
    """
    obj = event.payload.get("object", {})
    msg_id = obj.get("id")
    msg_data = obj.get("data", {})
    session_id = (msg_data.get("metadata") or {}).get("session_id")
    frame_id = msg_data.get("frame_id")
    if not session_id:
        return

    # Prior turns come from the graph view (restart-safe), not a process dict.
    turns = [
        o for o in ctx.view.objects()
        if o.type == "chat_turn" and o.data.get("session_id") == session_id
    ]
    # Exclude the current, still-unanswered turn — it is the triggering event.
    prior = [t for t in turns if t.data.get("comm_message_id") != msg_id]
    if not prior:
        return  # First turn of the session: nothing to remember yet.

    prior.sort(key=lambda t: t.data.get("turn_number", 0))
    # Bound memory to the most recent N turns (0/negative → unbounded).
    limit = settings.max_context_messages
    if limit and limit > 0:
        prior = prior[-limit:]
    if not prior:
        return

    lines = [f"Conversation so far (most recent {len(prior)} turn(s)):"]
    for t in prior:
        n = t.data.get("turn_number", "?")
        user = (t.data.get("user_message") or "").strip()
        assistant = (t.data.get("assistant_message") or "").strip()
        lines.append(f"[{n}] User: {user}")
        if assistant:
            lines.append(f"    Assistant: {assistant}")
    transcript = "\n".join(lines)

    try:
        context = graph.add_object("chat_context", {
            "session_id": session_id,
            "message_id": msg_id,
            "turn_count": len(prior),
            "transcript": transcript,
            "frame_id": frame_id,
        })
        # Link to the inbound message so the responder's depth-1 view captures
        # this context without having to widen its own scope.
        # NOTE: add_relation signature is (source, target, type).
        graph.add_relation(context.id, msg_id, "provides_context_for")
    except Exception:
        pass


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
        # recent_events MUST stay 0. Prior conversation reaches the model on
        # exactly one path: the ChatContext that chat_context_assembler linked to
        # this message (captured by depth=1 above), whose transcript is already
        # bounded to max_context_messages. A non-zero recent_events would fold
        # raw prior-turn event payloads into the prompt as a second, UNBOUNDED
        # memory channel — defeating max_context_messages and re-introducing a
        # side-channel. Keep memory single-sourced through ChatContext.
        "recent_events": 0,
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

    # The prior conversation reaches this LLM call via the ChatContext that
    # chat_context_assembler linked to this message: the depth-1 view below
    # captures it, the runtime serializes it into the prompt, and `out` is the
    # model's reply. "How many prior turns were shown" is recorded on that
    # ChatContext object (chat_context.turn_count) — the auditable, graph-native
    # source of truth — so we don't duplicate it onto the candidate.
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
        })
        graph.add_relation(candidate.id, msg_id, "response_to")
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

    Writing the assistant_message back onto the ChatTurn is what makes the
    completed Q&A part of the graph — so the next turn's chat_context_assembler
    reads it straight from the graph (no in-process history needed).

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

    # Resolve the ChatTurn to patch. The _MESSAGE_TO_TURN cache is the hot path;
    # if it misses (e.g. after a restart), fall back to the graph view — the
    # turn records its comm_message_id, so the mapping is always recoverable.
    turn_id = _MESSAGE_TO_TURN.get(message_id)
    if not turn_id:
        for o in ctx.view.objects():
            if o.type == "chat_turn" and o.data.get("comm_message_id") == message_id:
                turn_id = o.id
                break

    if turn_id:
        try:
            graph.patch_object(turn_id, {
                "assistant_message": response_content,
                "response_candidate_id": candidate_id,
            })
        except Exception:
            pass


# ================================================================ BEHAVIORS registry

# Registration order is execution order. chat_context_assembler must run BEFORE
# chat_llm_responder so the ChatContext (and its provides_context_for edge)
# exists when the responder's view is built and the LLM is called.
BEHAVIORS = [
    chat_ingester,
    chat_context_assembler,
    chat_llm_responder,
    chat_responder,
]
