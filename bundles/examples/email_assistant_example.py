"""Email Assistant Bundle example.

Demonstrates the email assistant bundle:
  - Inbound email ingestion → Source + CommMessage + EmailThread
  - Identity resolution of sender → Principal
  - Intent detection: query / founder_outreach / etc.
  - Entity extraction from email content

Run with:
    python bundles/examples/email_assistant_example.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packs.identity_auth import IdentitySettings
from packs.email import EmailSettings
from packs.entity import EntitySettings
from bundles.email_assistant import build_email_assistant


def main():
    print("=" * 60)
    print("Email Assistant Bundle — demo")
    print("=" * 60)

    rt = build_email_assistant(
        identity_settings=IdentitySettings(
            owner_identifiers=["alice@example.com"],
            default_external_role="external",
        ),
        email_settings=EmailSettings(
            owner_email_addresses=["alice@example.com"],
            require_approval_for_external=True,
            trusted_domains=["example.com"],
        ),
        entity_settings=EntitySettings(
            auto_extract_entities=True,
            dedup_similarity_threshold=0.85,
        ),
    )

    graph = rt._graph  # type: ignore[attr-defined]
    loaded = [p.name for p in rt._loaded_packs]  # type: ignore[attr-defined]
    print(f"\nPacks loaded ({len(loaded)}): {loaded}")

    from packs.email.tools import ingest_email_fn

    print("\n[1] Ingesting inbound email from external founder…")
    ingest_email_fn(
        graph,
        message_id="<msg001@startup.io>",
        from_addr="founder@acme-startup.io",
        to_addrs=["alice@example.com"],
        subject="Partnership opportunity — Acme Startup",
        body_text=(
            "Hi Alice, I'm Sarah Chen, CEO of Acme Startup. We're building "
            "AI-powered supply chain optimization. We raised $3M seed from a16z "
            "and would love to explore a partnership or investment discussion. "
            "Let me know if you have 30 minutes this week."
        ),
        received_at="2026-06-03T10:00:00Z",
    )
    rt.run_until_idle()

    sources = [o for o in graph.objects() if o.type == "source"]
    messages = [o for o in graph.objects() if o.type == "comm_message"]
    threads = [o for o in graph.objects() if o.type == "email_thread"]
    intents = [o for o in graph.objects() if o.type == "comm_intent"]
    entities = [o for o in graph.objects() if o.type == "entity"]
    principals = [o for o in graph.objects() if o.type == "principal"]

    print(f"\n  sources:        {len(sources)}")
    print(f"  comm_messages:  {len(messages)}")
    print(f"  email_threads:  {len(threads)}")
    print(f"  comm_intents:   {len(intents)}")
    for i in intents:
        d = i.data or {}
        print(f"    [{i.id[:8]}] intent={d.get('intent')} conf={d.get('confidence')}")
    print(f"  entities:       {len(entities)}")
    for e in entities:
        d = e.data or {}
        print(f"    [{e.id[:8]}] kind={d.get('kind')} name={d.get('name')!r}")
    print(f"  principals:     {len(principals)}")
    for p in principals:
        d = p.data or {}
        print(f"    [{p.id[:8]}] role={d.get('role')} ref={d.get('identifier_ref')!r}")

    print("\nDone.")


if __name__ == "__main__":
    main()
