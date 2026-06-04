"""Tests for subject-scoped memory recall (multi-user isolation).

Memories are tagged with the user they are about (subject_ref). Recall on
behalf of one user must NOT return another user's memories, because the chat
read path folds recalled memory straight into the LLM prompt — unscoped recall
would be a cross-user data leak.

Covers both layers:
  - backend: retrieve_by_query(subject_scoped=True) and find_by_text scoping.
  - end-to-end: Alice states a private preference, Bob asks a related question,
    and Bob's chat turn does NOT receive Alice's memory.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from packs.memory_gateway.backend import (
    SqliteMemoryBackend,
    clear_all_backends,
    clear_embedder,
)


@pytest.fixture(autouse=True)
def _lexical_only():
    clear_embedder()
    yield
    clear_embedder()


# ───────────────────────────────── backend layer ──────────────────────────────


def test_scoped_retrieval_isolates_users():
    """subject_scoped recall returns only the asking user's memories."""
    b = SqliteMemoryBackend(":memory:")
    b.store_item("a1", "dark mode preference", category="preference", subject_ref="alice")
    b.store_item("b1", "dark mode preference", category="preference", subject_ref="bob")

    bob = b.retrieve_by_query("dark mode", subject_ref="bob", subject_scoped=True, min_score=0.0)
    ids = {r["item_id"] for r in bob}
    assert ids == {"b1"}, f"bob should only see his own memory, got {ids}"

    alice = b.retrieve_by_query("dark mode", subject_ref="alice", subject_scoped=True, min_score=0.0)
    assert {r["item_id"] for r in alice} == {"a1"}


def test_global_memories_visible_to_all_scoped_callers():
    """Subject-less (NULL) memories are global and visible to every scoped caller."""
    b = SqliteMemoryBackend(":memory:")
    b.store_item("g1", "the office closes at 5pm", subject_ref=None)
    b.store_item("a1", "office snacks preference", subject_ref="alice")

    bob = b.retrieve_by_query("office", subject_ref="bob", subject_scoped=True, min_score=0.0)
    ids = {r["item_id"] for r in bob}
    assert "g1" in ids, "global memory should be visible to bob"
    assert "a1" not in ids, "alice's memory must not leak to bob"


def test_anonymous_caller_sees_only_global():
    """A scoped caller with no subject sees only global memories, never users'."""
    b = SqliteMemoryBackend(":memory:")
    b.store_item("g1", "office closes at 5pm", subject_ref=None)
    b.store_item("a1", "office snacks", subject_ref="alice")

    res = b.retrieve_by_query("office", subject_ref=None, subject_scoped=True, min_score=0.0)
    assert {r["item_id"] for r in res} == {"g1"}


def test_unscoped_retrieval_returns_all():
    """Default (subject_scoped=False) is global recall — backward compatible."""
    b = SqliteMemoryBackend(":memory:")
    b.store_item("a1", "dark mode preference", subject_ref="alice")
    b.store_item("b1", "dark mode preference", subject_ref="bob")

    res = b.retrieve_by_query("dark mode", min_score=0.0)
    assert {r["item_id"] for r in res} == {"a1", "b1"}


def test_strict_scope_excludes_global_nulls():
    """include_global=False returns only the caller's own memories.

    Defends against untagged/legacy NULL rows leaking across users even though
    NULL is normally treated as a shared/global memory.
    """
    b = SqliteMemoryBackend(":memory:")
    b.store_item("g1", "office closes at 5pm", subject_ref=None)
    b.store_item("a1", "office snacks preference", subject_ref="alice")

    strict = b.retrieve_by_query(
        "office", subject_ref="alice", subject_scoped=True,
        include_global=False, min_score=0.0,
    )
    assert {r["item_id"] for r in strict} == {"a1"}, "global NULL row must be excluded"

    # Bob (strict) gets nothing — neither alice's nor the global row.
    bob = b.retrieve_by_query(
        "office", subject_ref="bob", subject_scoped=True,
        include_global=False, min_score=0.0,
    )
    assert bob == []


def test_find_by_text_is_subject_scoped():
    """Identical text from different users must NOT dedup together."""
    b = SqliteMemoryBackend(":memory:")
    b.store_item("a1", "I prefer dark mode", subject_ref="alice")

    # Bob's identical sentence is a different memory.
    assert b.find_by_text("I prefer dark mode", subject_ref="bob") is None
    # Alice's own duplicate collapses.
    assert b.find_by_text("I prefer dark mode", subject_ref="alice") == "a1"
    # A subject-less candidate (Core) matches Alice's via NULL wildcard.
    assert b.find_by_text("I prefer dark mode", subject_ref=None) == "a1"


def test_dedup_upgrades_null_survivor_to_subject():
    """A NULL-subject item that lands first is upgraded when the scoped duplicate
    arrives — so dedup never leaves a memory globally recallable by accident.

    Mirrors memory_writer's order-independent behavior: Core's subject-less
    candidate stores first, then the chat (scoped) candidate dedups onto it.
    """
    b = SqliteMemoryBackend(":memory:")
    b.store_item("x1", "I prefer dark mode", subject_ref=None)

    # Scoped duplicate matches the NULL survivor (NULL wildcard) → upgrade it.
    assert b.find_by_text("I prefer dark mode", subject_ref="alice") == "x1"
    assert b.get_subject("x1") is None
    b.set_subject("x1", "alice")
    assert b.get_subject("x1") == "alice"

    # After the upgrade, bob's strict recall cannot reach it.
    bob = b.retrieve_by_query(
        "dark mode", subject_ref="bob", subject_scoped=True,
        include_global=False, min_score=0.0,
    )
    assert bob == []
    alice = b.retrieve_by_query(
        "dark mode", subject_ref="alice", subject_scoped=True,
        include_global=False, min_score=0.0,
    )
    assert {r["item_id"] for r in alice} == {"x1"}


# ──────────────────────────────── derivation layer ────────────────────────────


def test_derive_subject_ref_from_source():
    """memory_writer can recover the author from a candidate's source object."""
    from packs.memory_gateway.behaviors import _derive_subject_ref

    class _Obj:
        def __init__(self, data):
            self.data = data

    class _Graph:
        def __init__(self, objs):
            self._objs = objs

        def get_object(self, oid):
            return self._objs.get(oid)

    g = _Graph({
        "src_alice": _Obj({"sender_ref": "alice", "content": "..."}),
        "src_none": _Obj({"content": "no sender"}),
    })

    assert _derive_subject_ref(g, ["src_alice"]) == "alice"
    # No author resolvable → stays subject-less (genuinely global).
    assert _derive_subject_ref(g, ["src_none"]) is None
    assert _derive_subject_ref(g, []) is None
    assert _derive_subject_ref(g, ["missing"]) is None


# ──────────────────────────────── end-to-end layer ────────────────────────────


def test_core_only_candidate_is_tagged_with_author():
    """An untagged (Core-path) candidate is tagged from its source — no leak.

    Core's generic source→observation→candidate path never sets subject_ref. If
    that NULL survived to the stored item, the memory would be globally
    recallable by every user. memory_writer must derive the subject from the
    candidate's source object so it stays isolated to its author.
    """
    from bundles import build_assistant
    from packs.chat import ChatSettings
    from packs.chat.behaviors import clear_session_registry
    from packs.chat.llm import MockChatProvider
    from packs.chat.tools import submit_chat_input_fn
    from packs.communication.behaviors import clear_thread_registry
    from packs.identity_auth.behaviors import clear_principal_registry
    from packs.memory_gateway import MemoryGatewaySettings

    clear_all_backends()
    clear_session_registry()
    clear_principal_registry()
    clear_thread_registry()

    tmpdir = tempfile.mkdtemp(prefix="ag_core_only_")
    mem_path = str(Path(tmpdir) / "memory.sqlite")

    rt = build_assistant(
        memory_gateway_settings=MemoryGatewaySettings(backend_url=mem_path),
        chat_settings=ChatSettings(memory_backend_url=mem_path),
        llm_provider=MockChatProvider(),
    )
    g = rt.graph

    # Drive a real chat turn so the ingester creates a schema-valid `source`
    # object tagged with alice as sender — the same object Core's candidates
    # reference.
    submit_chat_input_fn(g, user_ref="alice", content="Just sharing a status update.")
    rt.run_until_idle()
    sources = [s for s in g.objects(type="source") if s.data.get("sender_ref") == "alice"]
    assert sources, "chat ingester should have created a source for alice"
    src_id = sources[0].id

    # An UNTAGGED candidate referencing alice's source (mirrors Core's path, which
    # never sets subject_ref). High confidence so the acceptance threshold passes.
    g.add_object("memory_candidate", {
        "text": "The data warehouse migration finished in Q1.",
        "confidence": 0.9,
        "source_ids": [src_id],
        "observation_ids": [],
        "category": "fact",
        "subject_ref": None,
        "frame_id": None,
    })
    rt.run_until_idle()

    items = [it for it in g.objects(type="memory_item") if it.data.get("text", "").startswith("The data warehouse")]
    assert items, "candidate should have been promoted to a memory_item"
    assert items[0].data.get("subject_ref") == "alice", (
        "untagged candidate must be tagged with its source's author, not left global"
    )

    # And the backend row is isolated: bob (strict) can't see it.
    from packs.memory_gateway.backend import get_backend
    backend = get_backend(mem_path)
    bob = backend.retrieve_by_query(
        "data warehouse migration", subject_ref="bob",
        subject_scoped=True, include_global=False, min_score=0.0,
    )
    assert bob == [], "alice's memory must not leak to bob"

    clear_all_backends()
    clear_session_registry()
    clear_principal_registry()
    clear_thread_registry()


def test_chat_recall_does_not_leak_across_users():
    """Alice states a preference; Bob's related question must not recall it."""
    from bundles import build_assistant
    from packs.chat import ChatSettings
    from packs.chat.behaviors import clear_session_registry
    from packs.chat.llm import MockChatProvider
    from packs.chat.tools import submit_chat_input_fn
    from packs.communication.behaviors import clear_thread_registry
    from packs.identity_auth.behaviors import clear_principal_registry
    from packs.memory_gateway import MemoryGatewaySettings

    clear_all_backends()
    clear_session_registry()
    clear_principal_registry()
    clear_thread_registry()

    tmpdir = tempfile.mkdtemp(prefix="ag_iso_mem_")
    mem_path = str(Path(tmpdir) / "memory.sqlite")

    rt = build_assistant(
        memory_gateway_settings=MemoryGatewaySettings(backend_url=mem_path),
        chat_settings=ChatSettings(memory_backend_url=mem_path),
        llm_provider=MockChatProvider(),
    )
    g = rt.graph

    # Alice states a private preference.
    submit_chat_input_fn(
        g, user_ref="alice", content="I always prefer dark mode and concise answers."
    )
    rt.run_until_idle()

    # Bob asks a keyword-overlapping question.
    submit_chat_input_fn(g, user_ref="bob", content="What are my dark mode preferences?")
    rt.run_until_idle()

    # Any memory_context attached to Bob's turn must NOT contain Alice's text.
    leaked = [
        c for c in g.objects(type="memory_context")
        if "dark mode and concise" in (c.data.get("summary") or "")
    ]
    assert not leaked, "Bob received Alice's memory — cross-user leak"

    clear_all_backends()
    clear_session_registry()
    clear_principal_registry()
    clear_thread_registry()
