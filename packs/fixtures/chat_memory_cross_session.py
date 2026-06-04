"""Cross-session integration fixture: conversation-driven long-term memory.

Proves the headline behavior of Task #37 — the assistant remembers what you told
it in an EARLIER chat session and folds it back into the prompt in a LATER one,
with NO LLM and NO API key.

Scenario:
  Session 1 (first run)
    1. User states a durable preference in chat.
    2. The write path (Core's source→observation→memory_candidate pipeline plus
       chat_memory_proposer) creates candidates; candidate_evaluator accepts;
       memory_writer persists a memory_item to a SQLite memory FILE.
  ── simulate a restart ──
    3. close_all_backends() closes the SQLite connections but keeps the file,
       and the session/identity registries are cleared. A brand new Runtime is
       built with a FRESH graph but pointed at the SAME memory file.
  Session 2 (second run, fresh graph)
    4. User asks a returning question whose keywords overlap the stored memory.
    5. chat_memory_context retrieves it (lexical Jaccard, default) and attaches a
       memory_context object to the message BEFORE the responder runs.

Verifies: the recalled memory_context exists in session 2 and contains the
preference text written in session 1 — i.e. cross-session recall works.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from bundles import build_assistant
from packs.chat import ChatSettings
from packs.chat.behaviors import clear_session_registry
from packs.chat.llm import MockChatProvider
from packs.chat.tools import submit_chat_input_fn
from packs.communication.behaviors import clear_thread_registry
from packs.identity_auth.behaviors import clear_principal_registry
from packs.memory_gateway import MemoryGatewaySettings
from packs.memory_gateway.backend import (
    clear_all_backends,
    close_all_backends,
    get_backend,
)

STORED_PREFERENCE = "I always prefer dark mode and concise answers."
RETURNING_QUERY = "What are my dark mode preferences?"


def _clear_registries() -> None:
    """Reset all module-level dedup registries (simulates a new process)."""
    clear_session_registry()
    clear_principal_registry()
    clear_thread_registry()


def _build_session(mem_path: str):
    """Build an assistant runtime whose memory read+write target *mem_path*."""
    return build_assistant(
        memory_gateway_settings=MemoryGatewaySettings(backend_url=mem_path),
        chat_settings=ChatSettings(memory_backend_url=mem_path),
        llm_provider=MockChatProvider(),
    )


def run_cross_session_memory() -> dict:
    """Write a preference in session 1, recall it in a fresh session 2."""
    # Start from a totally clean slate (no leftover in-memory backends).
    clear_all_backends()
    _clear_registries()

    tmpdir = tempfile.mkdtemp(prefix="ag_xsession_mem_")
    mem_path = str(Path(tmpdir) / "memory.sqlite")

    # ── Session 1: state a durable preference ────────────────────────────────
    rt1 = _build_session(mem_path)
    submit_chat_input_fn(rt1.graph, user_ref="alice", content=STORED_PREFERENCE)
    rt1.run_until_idle()

    stored_count = get_backend(mem_path).count()
    assert stored_count >= 1, (
        f"session 1 should have persisted >=1 memory_item, got {stored_count}"
    )

    # ── Simulate a restart: close connections (keep the file), drop registries.
    close_all_backends()
    _clear_registries()

    # ── Session 2: fresh graph, SAME memory file, a returning question ────────
    rt2 = _build_session(mem_path)

    # The fresh graph must NOT already contain the memory (it lives only in the
    # backend file, recall must fetch it across the session boundary).
    pre_items = list(rt2.graph.objects(type="memory_item"))
    assert not pre_items, (
        f"session 2 graph should start empty of memory_item, got {len(pre_items)}"
    )

    submit_chat_input_fn(rt2.graph, user_ref="alice", content=RETURNING_QUERY)
    rt2.run_until_idle()

    contexts = list(rt2.graph.objects(type="memory_context"))
    assert contexts, "session 2 should have created a memory_context on recall"

    summaries = [c.data.get("summary", "") for c in contexts]
    recalled = any("dark mode" in s.lower() for s in summaries)
    assert recalled, (
        "recalled memory_context should contain the session-1 preference; "
        f"summaries={summaries!r}"
    )

    total_recalled = sum(c.data.get("item_count", 0) for c in contexts)

    # Cleanup connections (file is in a temp dir, OK to leave on disk).
    close_all_backends()
    clear_all_backends()
    _clear_registries()

    return {
        "stored_count": stored_count,
        "contexts": len(contexts),
        "recalled_items": total_recalled,
        "summaries": summaries,
    }


def main() -> int:
    print("=" * 70)
    print("CROSS-SESSION LONG-TERM MEMORY FIXTURE")
    print("=" * 70)
    try:
        result = run_cross_session_memory()
    except AssertionError as exc:
        print(f"\nFAIL: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"\nFAIL: unexpected error: {exc!r}")
        return 1

    print(f"\nSession 1 stored {result['stored_count']} memory item(s).")
    print(f"Session 2 created {result['contexts']} memory_context object(s) "
          f"recalling {result['recalled_items']} item(s).")
    for s in result["summaries"]:
        print(f"  - {s!r}")
    print("\nPASS: preference written in session 1 was recalled in session 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
