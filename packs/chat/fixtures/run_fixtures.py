"""Chat Adapter Pack fixtures.

Tests:
  1. 3-turn conversation — full pipeline: chat_input → CommMessage → CommResponseCandidate
     → ChatTurn.assistant_message populated
  2. Session continuity — second set of turns resumes the same ChatSession
  3. Mock LLM responses — deterministic stubs, no API key required
  4. Cross-pack: Chat + Communication + Core all wired together
"""

from __future__ import annotations

import sys

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings
from packs.communication import pack as comm_pack, CommunicationSettings
from packs.communication.behaviors import clear_thread_registry
from packs.chat import pack as chat_pack, ChatSettings
from packs.chat.behaviors import clear_session_registry
from packs.chat.llm import MockChatProvider
from packs.chat.tools import get_session_turns_fn, submit_chat_input_fn


def _make_runtime(auto_approve: bool = True) -> tuple:
    clear_thread_registry()
    clear_session_registry()

    g = Graph()
    # chat_llm_responder is an @llm_behavior — the runtime requires a provider.
    # MockChatProvider runs the pipeline end-to-end with no API key.
    rt = Runtime(g, llm_provider=MockChatProvider())
    rt.load_pack(core_pack, settings=CoreSettings())
    rt.load_pack(comm_pack, settings=CommunicationSettings())
    rt.load_pack(
        chat_pack,
        settings=ChatSettings(
            llm_provider="mock",
            auto_approve_responses=auto_approve,
        ),
    )
    return g, rt


def run_three_turn_conversation_fixture() -> dict:
    """Demonstrate a 3-turn conversation: each turn produces observations, tasks, and artifacts."""
    g, rt = _make_runtime()

    # ── Turn 1 ──────────────────────────────────────────────────────────────
    submit_chat_input_fn(g, user_ref="alice@example.com",
                         content="What is the status of the Northwind deal?")
    rt.run_until_idle()

    sessions_t1 = list(g.objects(type="chat_session"))
    turns_t1 = list(g.objects(type="chat_turn"))
    comm_msgs_t1 = list(g.objects(type="comm_message"))
    comm_threads_t1 = list(g.objects(type="comm_thread"))
    intents_t1 = list(g.objects(type="comm_intent"))
    candidates_t1 = list(g.objects(type="comm_response_candidate"))

    assert len(sessions_t1) == 1, f"Turn 1: expected 1 session, got {len(sessions_t1)}"
    assert len(turns_t1) == 1, f"Turn 1: expected 1 turn, got {len(turns_t1)}"
    assert len(comm_msgs_t1) == 1, f"Turn 1: expected 1 comm_message, got {len(comm_msgs_t1)}"
    assert len(comm_threads_t1) == 1, f"Turn 1: expected 1 thread, got {len(comm_threads_t1)}"
    assert len(intents_t1) >= 1, f"Turn 1: expected >=1 intent"
    assert len(candidates_t1) >= 1, f"Turn 1: expected >=1 response candidate"

    turn1 = turns_t1[0]
    assert turn1.data.get("assistant_message") is not None, "Turn 1: assistant_message should be populated"
    assert turn1.data.get("turn_number") == 1, "Turn 1: turn_number should be 1"

    session_id = sessions_t1[0].id

    # ── Turn 2 (continues session by user_ref) ────────────────────────────
    submit_chat_input_fn(g, user_ref="alice@example.com",
                         content="Please draft a brief summary of the deal highlights.")
    rt.run_until_idle()

    sessions_t2 = list(g.objects(type="chat_session"))
    turns_t2 = list(g.objects(type="chat_turn"))

    assert len(sessions_t2) == 1, f"Turn 2: should still have 1 session (resumed), got {len(sessions_t2)}"
    assert len(turns_t2) == 2, f"Turn 2: expected 2 total turns, got {len(turns_t2)}"

    turn2 = turns_t2[-1]
    assert turn2.data.get("turn_number") == 2, "Turn 2: turn_number should be 2"
    assert turn2.data.get("assistant_message") is not None, "Turn 2: assistant_message populated"

    # ── Turn 3 ────────────────────────────────────────────────────────────
    submit_chat_input_fn(g, user_ref="alice@example.com",
                         content="Thanks. What are the next steps we should prioritize?")
    rt.run_until_idle()

    turns_t3 = list(g.objects(type="chat_turn"))
    assert len(turns_t3) == 3, f"Turn 3: expected 3 total turns, got {len(turns_t3)}"

    turn3 = turns_t3[-1]
    assert turn3.data.get("turn_number") == 3, "Turn 3: turn_number should be 3"
    assert turn3.data.get("assistant_message") is not None, "Turn 3: assistant_message populated"

    # ── Verify session metadata ───────────────────────────────────────────
    session = g.get_object(session_id)
    assert session.data.get("turn_count") == 3, \
        f"Session.turn_count should be 3, got {session.data.get('turn_count')}"

    # ── Verify session_contains_turn relations ───────────────────────────
    session_turn_rels = list(g.relations(type="session_contains_turn"))
    assert len(session_turn_rels) == 3, \
        f"Expected 3 session_contains_turn rels, got {len(session_turn_rels)}"
    assert all(r.source == session_id for r in session_turn_rels), \
        "session_contains_turn relations must originate from the session"

    # ── Collect intent observations ───────────────────────────────────────
    all_intents = list(g.objects(type="comm_intent"))
    intent_values = [i.data.get("intent") for i in all_intents]

    return {
        "turns_completed": len(turns_t3),
        "session_id": session_id,
        "session_turn_count": session.data.get("turn_count"),
        "intents_detected": intent_values,
        "comm_threads": len(list(g.objects(type="comm_thread"))),
        "comm_messages": len(list(g.objects(type="comm_message"))),
        "response_candidates": len(list(g.objects(type="comm_response_candidate"))),
        "sources_created": len(list(g.objects(type="source"))),
    }


def run_session_continuity_fixture() -> dict:
    """Test that session resumes correctly when session_id is provided explicitly."""
    g, rt = _make_runtime()

    # First turn — creates session
    submit_chat_input_fn(g, user_ref="bob@example.com", content="Hello!")
    rt.run_until_idle()

    sessions = list(g.objects(type="chat_session"))
    assert len(sessions) == 1
    session_id = sessions[0].id

    # Resume by explicit session_id
    submit_chat_input_fn(g, user_ref="bob@example.com", content="Follow up.",
                         session_id=session_id)
    rt.run_until_idle()

    sessions_after = list(g.objects(type="chat_session"))
    assert len(sessions_after) == 1, "Should still be 1 session after explicit resume"

    turns = list(g.objects(type="chat_turn"))
    assert len(turns) == 2, f"Expected 2 turns after explicit resume, got {len(turns)}"

    return {"sessions": len(sessions_after), "turns": len(turns)}


def run_multi_turn_recall_fixture() -> dict:
    """Conversation memory is graph-native and restart-safe.

    Proves that prior turns are reconstructed from the graph (not from process
    memory): we wipe ALL in-process caches between turns to simulate an
    API-server restart mid-session, then confirm turn 2 still resumes the same
    session AND assembles a ChatContext containing turn 1's exchange.
    """
    g, rt = _make_runtime()

    # ── Turn 1 ────────────────────────────────────────────────────────────
    submit_chat_input_fn(g, user_ref="sam@example.com", content="My name is Sam.")
    rt.run_until_idle()
    session_id = list(g.objects(type="chat_session"))[0].id

    # Simulate an API-server restart: drop every in-process cache. The graph is
    # the only surviving store — if memory weren't graph-native, this would
    # break session continuity and lose the prior turn.
    clear_session_registry()

    # ── Turn 2 — resume by explicit session_id (as the Inspector UI does) ──
    submit_chat_input_fn(g, user_ref="sam@example.com",
                         content="What is my name?", session_id=session_id)
    rt.run_until_idle()

    # Session continuity survived the cache wipe (resolved from the graph).
    sessions = list(g.objects(type="chat_session"))
    assert len(sessions) == 1, f"expected 1 session after restart, got {len(sessions)}"
    turns = sorted(g.objects(type="chat_turn"), key=lambda t: t.data.get("turn_number", 0))
    assert len(turns) == 2, f"expected 2 turns, got {len(turns)}"
    assert turns[-1].data.get("turn_number") == 2, "turn 2 must continue numbering"
    assert turns[-1].data.get("assistant_message") is not None, "turn 2 must be answered"

    # A ChatContext was assembled for turn 2 (and only turn 2 — turn 1 had no
    # prior memory), and it contains turn 1's user message.
    contexts = list(g.objects(type="chat_context"))
    assert len(contexts) == 1, f"expected 1 chat_context, got {len(contexts)}"
    ctx_obj = contexts[0]
    assert ctx_obj.data.get("turn_count") == 1, \
        f"context should include 1 prior turn, got {ctx_obj.data.get('turn_count')}"
    transcript = ctx_obj.data.get("transcript") or ""
    assert "My name is Sam." in transcript, \
        "graph-derived context must include the prior user message"

    # The context is linked to the inbound message (provides_context_for) so the
    # responder's depth-1 view captures it — this edge is what actually carries
    # the prior turns into the LLM prompt.
    ctx_rels = list(g.relations(type="provides_context_for"))
    assert len(ctx_rels) == 1, \
        f"expected 1 provides_context_for rel, got {len(ctx_rels)}"
    assert ctx_rels[0].source == ctx_obj.id, "rel must originate from the chat_context"
    assert ctx_rels[0].target == ctx_obj.data.get("message_id"), \
        "rel must point at the inbound message the context was assembled for"

    return {
        "sessions": len(sessions),
        "turns": len(turns),
        "context_turn_count": ctx_obj.data.get("turn_count"),
    }


def run_bounded_context_fixture() -> dict:
    """max_context_messages bounds how many prior turns enter the context."""
    g = Graph()
    clear_thread_registry()
    clear_session_registry()
    rt = Runtime(g, llm_provider=MockChatProvider())
    rt.load_pack(core_pack, settings=CoreSettings())
    rt.load_pack(comm_pack, settings=CommunicationSettings())
    rt.load_pack(
        chat_pack,
        settings=ChatSettings(
            llm_provider="mock",
            auto_approve_responses=True,
            max_context_messages=1,  # only the single most recent prior turn
        ),
    )

    session_id = None
    for i in range(3):
        submit_chat_input_fn(g, user_ref="cap@example.com",
                             content=f"Message {i + 1}.", session_id=session_id)
        rt.run_until_idle()
        if session_id is None:
            session_id = list(g.objects(type="chat_session"))[0].id

    # Turns 2 and 3 each assemble a context; with max_context_messages=1 every
    # one must be bounded to a single prior turn (never 2), proving the cap.
    contexts = list(g.objects(type="chat_context"))
    assert len(contexts) == 2, f"expected 2 contexts (turns 2 & 3), got {len(contexts)}"
    assert all(c.data.get("turn_count") == 1 for c in contexts), \
        f"every context must be bounded to 1 turn, got {[c.data.get('turn_count') for c in contexts]}"

    # Boundedness must hold for the actual text the LLM sees, not just the count.
    # Turn 3's context (prior = [turn 2]) must include "Message 2." and must NOT
    # leak the older "Message 1." — proving the cap drops dropped turns entirely.
    turn3_ctx = next(
        (c for c in contexts
         if "Message 2." in (c.data.get("transcript") or "")), None)
    assert turn3_ctx is not None, "expected a context covering the most recent prior turn"
    assert "Message 1." not in (turn3_ctx.data.get("transcript") or ""), \
        "older turn leaked past max_context_messages into the transcript"

    return {"contexts": len(contexts), "bounded_to": 1}


def run_all() -> bool:
    print("=" * 60)
    print("Chat Adapter Pack Fixtures")
    print("=" * 60)
    all_pass = True

    print("\n[1] 3-turn conversation fixture")
    try:
        result = run_three_turn_conversation_fixture()
        print(f"  PASS: turns={result['turns_completed']}, "
              f"session_turn_count={result['session_turn_count']}, "
              f"intents={result['intents_detected']}")
        print(f"        threads={result['comm_threads']}, "
              f"messages={result['comm_messages']}, "
              f"sources={result['sources_created']}")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        all_pass = False

    print("\n[2] session continuity fixture")
    try:
        result = run_session_continuity_fixture()
        print(f"  PASS: sessions={result['sessions']}, turns={result['turns']}")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        all_pass = False

    print("\n[3] multi-turn recall (graph-native, restart-safe) fixture")
    try:
        result = run_multi_turn_recall_fixture()
        print(f"  PASS: sessions={result['sessions']}, turns={result['turns']}, "
              f"context_turn_count={result['context_turn_count']}")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        all_pass = False

    print("\n[4] bounded context (max_context_messages) fixture")
    try:
        result = run_bounded_context_fixture()
        print(f"  PASS: contexts={result['contexts']}, bounded_to={result['bounded_to']}")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        all_pass = False

    print(f"\n{'ALL PASS' if all_pass else 'SOME FAILURES'}")
    return all_pass


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
