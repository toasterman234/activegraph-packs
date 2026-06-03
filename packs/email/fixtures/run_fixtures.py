"""Email Pack fixtures.

Tests:
  1. Inbound email ingestion — email_message → Source + CommMessage + EmailThread
  2. Thread continuity — In-Reply-To links messages to existing EmailThread
  3. Email deduplication — same message_id not ingested twice
  4. Reply drafting — CommResponseCandidate → EmailDraft with proper headers
  5. Approval gate — external recipient triggers Action(approval_request, risk_class=high)
  6. Internal auto-approve — owner email bypasses approval gate
  7. Intent detection — email body classified by Communication Pack intent_detector
"""

from __future__ import annotations

import sys

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings
from packs.communication import pack as comm_pack, CommunicationSettings
from packs.communication.behaviors import clear_thread_registry
from packs.email import pack as email_pack, EmailSettings
from packs.email.behaviors import clear_email_registry
from packs.email.tools import create_email_response_fn, ingest_email_fn


def _make_runtime(
    owner_emails: list[str] | None = None,
    require_approval: bool = True,
    trusted_domains: list[str] | None = None,
) -> tuple:
    clear_thread_registry()
    clear_email_registry()

    g = Graph()
    rt = Runtime(g)
    rt.load_pack(core_pack, settings=CoreSettings())
    rt.load_pack(comm_pack, settings=CommunicationSettings())
    rt.load_pack(
        email_pack,
        settings=EmailSettings(
            owner_email_addresses=owner_emails or ["alice@example.com"],
            require_approval_for_external=require_approval,
            trusted_domains=trusted_domains or [],
        ),
    )
    return g, rt


def run_email_ingestion_fixture() -> dict:
    """Inbound founder email → Source + CommMessage + EmailThread."""
    g, rt = _make_runtime()

    ingest_email_fn(
        g,
        message_id="<msg001@mail.sequoia.com>",
        from_addr="sarah.thompson@sequoia.com",
        to_addrs=["alice@example.com"],
        subject="Investment interest in Northwind AI",
        body_text=(
            "Hi Alice,\n\n"
            "I'd love to schedule a call to discuss a potential investment in Northwind AI. "
            "Could you please share your latest deck and financials?\n\n"
            "Best,\nSarah"
        ),
        received_at="2026-06-03T09:00:00Z",
    )
    rt.run_until_idle()

    sources = list(g.objects(type="source"))
    comm_msgs = list(g.objects(type="comm_message"))
    email_threads = list(g.objects(type="email_thread"))
    intents = list(g.objects(type="comm_intent"))

    assert len(sources) == 1, f"Expected 1 source, got {len(sources)}"
    assert sources[0].data.get("kind") == "email"
    assert sources[0].data.get("channel") == "email"

    assert len(comm_msgs) == 1, f"Expected 1 comm_message, got {len(comm_msgs)}"
    assert comm_msgs[0].data.get("channel") == "email"
    assert comm_msgs[0].data.get("direction") == "inbound"
    assert comm_msgs[0].data.get("sender_ref") == "sarah.thompson@sequoia.com"

    assert len(email_threads) == 1, f"Expected 1 email_thread, got {len(email_threads)}"
    assert email_threads[0].data.get("subject") == "Investment interest in Northwind AI"

    assert len(intents) >= 1, "Expected >=1 comm_intent from intent_detector"

    return {
        "sources": len(sources),
        "comm_messages": len(comm_msgs),
        "email_threads": len(email_threads),
        "intent": intents[0].data.get("intent") if intents else None,
    }


def run_thread_continuity_fixture() -> dict:
    """In-Reply-To links follow-up emails to the same EmailThread."""
    g, rt = _make_runtime()

    # Original email
    ingest_email_fn(
        g,
        message_id="<original@mail.example.com>",
        from_addr="founder@startup.com",
        to_addrs=["alice@example.com"],
        subject="Partnership proposal",
        body_text="Hi Alice, interested in partnering with you.",
        received_at="2026-06-01T08:00:00Z",
    )
    rt.run_until_idle()

    threads_after_first = list(g.objects(type="email_thread"))
    assert len(threads_after_first) == 1

    # Reply email (In-Reply-To links to original)
    ingest_email_fn(
        g,
        message_id="<reply001@mail.example.com>",
        from_addr="alice@example.com",
        to_addrs=["founder@startup.com"],
        subject="Re: Partnership proposal",
        body_text="Hi, thanks for reaching out! Let's schedule a call.",
        in_reply_to="<original@mail.example.com>",
        thread_id="<original@mail.example.com>",
        received_at="2026-06-01T10:00:00Z",
    )
    rt.run_until_idle()

    threads_after_reply = list(g.objects(type="email_thread"))
    assert len(threads_after_reply) == 1, \
        f"Expected 1 thread (reply should join existing), got {len(threads_after_reply)}"

    thread = g.get_object(threads_after_reply[0].id)
    assert thread.data.get("message_count") == 2, \
        f"Expected message_count=2, got {thread.data.get('message_count')}"

    return {
        "email_threads": len(threads_after_reply),
        "message_count": thread.data.get("message_count"),
        "participants": thread.data.get("participant_addrs"),
    }


def run_dedup_fixture() -> dict:
    """Same message_id ingested twice should only produce 1 EmailMessage worth of objects."""
    g, rt = _make_runtime()

    for _ in range(2):
        ingest_email_fn(
            g,
            message_id="<dedup-test@mail.example.com>",
            from_addr="sender@example.com",
            to_addrs=["alice@example.com"],
            subject="Dedup test",
            body_text="This email arrives twice (webhook retry).",
        )
        rt.run_until_idle()

    sources = list(g.objects(type="source"))
    comm_msgs = list(g.objects(type="comm_message"))
    email_threads = list(g.objects(type="email_thread"))

    assert len(sources) == 1, f"Dedup: expected 1 source, got {len(sources)}"
    assert len(comm_msgs) == 1, f"Dedup: expected 1 comm_message, got {len(comm_msgs)}"
    assert len(email_threads) == 1, f"Dedup: expected 1 email_thread, got {len(email_threads)}"

    return {"sources": len(sources), "comm_messages": len(comm_msgs)}


def run_approval_gate_fixture() -> dict:
    """External recipient email → approval_request Action created, draft not auto-sent."""
    g, rt = _make_runtime(
        owner_emails=["alice@example.com"],
        require_approval=True,
    )

    # Inbound email from external founder
    ingest_email_fn(
        g,
        message_id="<founder-msg@mail.vc.com>",
        from_addr="investor@venturecap.com",
        to_addrs=["alice@example.com"],
        subject="Term sheet ready",
        body_text="Alice, we have a term sheet ready. Please review and respond.",
    )
    rt.run_until_idle()

    comm_msgs = list(g.objects(type="comm_message"))
    assert len(comm_msgs) == 1
    comm_msg_id = comm_msgs[0].id

    # Create a response candidate (triggers reply_drafter → send_approver)
    create_email_response_fn(
        g,
        comm_message_id=comm_msg_id,
        content="Thank you for the term sheet. I'll review it and get back to you shortly.",
    )
    rt.run_until_idle()

    email_drafts = list(g.objects(type="email_draft"))
    actions = list(g.objects(type="action"))

    assert len(email_drafts) == 1, f"Expected 1 email_draft, got {len(email_drafts)}"
    assert email_drafts[0].data.get("status") == "draft", \
        f"Draft should still be 'draft' (awaiting approval), got {email_drafts[0].data.get('status')}"
    assert email_drafts[0].data.get("requires_approval") is True

    approval_actions = [a for a in actions if a.data.get("kind") == "approval_request"]
    assert len(approval_actions) >= 1, \
        f"Expected >=1 approval_request action, got {len(approval_actions)}"
    assert approval_actions[0].data.get("risk_class") == "high"

    return {
        "draft_status": email_drafts[0].data.get("status"),
        "requires_approval": email_drafts[0].data.get("requires_approval"),
        "approval_actions_created": len(approval_actions),
        "approval_action_risk": approval_actions[0].data.get("risk_class"),
    }


def run_internal_auto_approve_fixture() -> dict:
    """Owner-to-owner email → auto-approved (no approval action created)."""
    g, rt = _make_runtime(
        owner_emails=["alice@example.com", "alice.internal@example.com"],
        require_approval=True,
    )

    # Inbound from owner's own address (self-email or internal test)
    ingest_email_fn(
        g,
        message_id="<internal-msg@example.com>",
        from_addr="alice.internal@example.com",
        to_addrs=["alice@example.com"],
        subject="Internal note",
        body_text="Alice, just a quick internal note.",
    )
    rt.run_until_idle()

    comm_msgs = list(g.objects(type="comm_message"))
    comm_msg_id = comm_msgs[0].id

    create_email_response_fn(
        g,
        comm_message_id=comm_msg_id,
        content="Got it, thanks.",
    )
    rt.run_until_idle()

    email_drafts = list(g.objects(type="email_draft"))
    approval_actions = [
        a for a in g.objects(type="action")
        if a.data.get("kind") == "approval_request"
    ]

    assert len(email_drafts) == 1, f"Expected 1 email_draft, got {len(email_drafts)}"
    # Internal replies go to the original sender (alice.internal@example.com — trusted)
    # send_approver should auto-approve
    draft_status = email_drafts[0].data.get("status")
    assert draft_status == "approved", \
        f"Internal draft should be auto-approved, got '{draft_status}'"
    assert len(approval_actions) == 0, \
        f"No approval_request actions expected for internal email, got {len(approval_actions)}"

    return {
        "draft_status": draft_status,
        "approval_actions": len(approval_actions),
    }


def run_all() -> bool:
    print("=" * 60)
    print("Email Pack Fixtures")
    print("=" * 60)
    all_pass = True

    tests = [
        ("[1] email ingestion", run_email_ingestion_fixture),
        ("[2] thread continuity", run_thread_continuity_fixture),
        ("[3] deduplication", run_dedup_fixture),
        ("[4] approval gate (external)", run_approval_gate_fixture),
        ("[5] internal auto-approve", run_internal_auto_approve_fixture),
    ]

    for label, fn in tests:
        print(f"\n{label}")
        try:
            result = fn()
            print(f"  PASS: {result}")
        except (AssertionError, Exception) as e:
            print(f"  FAIL: {e}")
            all_pass = False

    print(f"\n{'ALL PASS' if all_pass else 'SOME FAILURES'}")
    return all_pass


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
