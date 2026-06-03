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
from packs.chat.behaviors import (
    clear_session_registry,
    reset_mock_response_idx,
)
from packs.chat.tools import get_session_turns_fn, submit_chat_input_fn


def _make_runtime(auto_approve: bool = True) -> tuple:
    clear_thread_registry()
    clear_session_registry()
    reset_mock_response_idx()

    g = Graph()
    rt = Runtime(g)
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
    rels = list(g.relations())
    session_turn_rels = [r for r in rels if r.source == "session_contains_turn"]
    assert len(session_turn_rels) == 3, \
        f"Expected 3 session_contains_turn rels, got {len(session_turn_rels)}"

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

    print(f"\n{'ALL PASS' if all_pass else 'SOME FAILURES'}")
    return all_pass


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
