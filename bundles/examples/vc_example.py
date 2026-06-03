"""VC Bundle example.

Demonstrates the full VC assistant bundle:
  - Founder email → diligence document → investment memo
  - Diligence-Core bridge maps diligence objects to Core primitives
  - VC Pack creates CompanyProfile, InvestmentMemo, Followup
  - Meeting Pack ingests team call transcript

Run with:
    python bundles/examples/vc_example.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packs.core import CoreSettings
from packs.identity_auth import IdentitySettings
from packs.vc import VCSettings
from packs.meeting import MeetingSettings
from bundles.vc_bundle import build_vc_assistant


def main():
    print("=" * 60)
    print("VC Bundle — demo")
    print("=" * 60)

    rt = build_vc_assistant(
        identity_settings=IdentitySettings(
            owner_identifiers=["partner@benchmark.vc"],
            default_external_role="external",
        ),
        vc_settings=VCSettings(
            owner_firm_name="Benchmark Capital",
            auto_draft_memo=True,
            auto_create_followup_task=True,
        ),
        meeting_settings=MeetingSettings(
            auto_create_tasks_from_action_items=True,
        ),
    )

    graph = rt._graph  # type: ignore[attr-defined]
    loaded = [p.name for p in rt._loaded_packs]  # type: ignore[attr-defined]
    print(f"\nPacks loaded ({len(loaded)}): {loaded}")

    # ── Step 1: Ingest a founder email ──────────────────────────────────────
    print("\n[1] Ingesting founder email…")
    from packs.vc.tools import ingest_founder_email_fn
    ingest_founder_email_fn(
        graph,
        sender_ref="ceo@northwind-robotics.ai",
        content=(
            "Hi, we're Northwind Robotics — building autonomous material handling "
            "for factory floors. Raised $2M seed from YC. ARR $600k, growing 22% MoM. "
            "Looking to raise our Series A. Would love to connect."
        ),
        subject="Northwind Robotics — Series A",
        channel="email",
    )
    rt.run_until_idle()

    companies = [o for o in graph.objects() if o.type == "company_profile"]
    memos = [o for o in graph.objects() if o.type == "investment_memo"]
    core_sources = [o for o in graph.objects() if o.type == "source"]

    print(f"  company_profiles:  {len(companies)}")
    for c in companies:
        d = c.data or {}
        print(f"    [{c.id[:8]}] {d.get('name')!r} stage={d.get('stage')}")
    print(f"  investment_memos:  {len(memos)}")
    for m in memos:
        d = m.data or {}
        print(f"    [{m.id[:8]}] {d.get('title')!r} status={d.get('status')}")
    print(f"  core sources:      {len(core_sources)}")

    # ── Step 2: Add a diligence document (bridge maps it to Core source) ────
    print("\n[2] Adding Diligence document (bridge test)…")
    from activegraph.packs import load_by_name
    company_id = companies[0].id if companies else "unknown"

    doc = graph.add_object("document", {
        "title": "Northwind Robotics — Technical Due Diligence",
        "url": "https://docs.benchmark.vc/northwind-dd.pdf",
        "company_id": company_id,
        "summary": "Strong CV pipeline. 3 ex-Boston Dynamics engineers. Weak supply chain integration.",
        "published_at": "2026-06-03",
    })
    rt.run_until_idle()

    bridge_sources = [
        o for o in graph.objects()
        if o.type == "source"
        and (o.data or {}).get("metadata", {}).get("bridge") == "diligence_core"
    ]
    print(f"  bridge sources (document→source): {len(bridge_sources)}")
    for s in bridge_sources:
        d = s.data or {}
        print(f"    [{s.id[:8]}] kind={d.get('kind')} "
              f"meta.title={d.get('metadata', {}).get('title', '')!r}")

    # ── Step 3: Ingest a meeting transcript ─────────────────────────────────
    print("\n[3] Ingesting team call transcript…")
    from packs.meeting.tools import ingest_transcript_fn
    ingest_transcript_fn(
        graph,
        title="Northwind Robotics — Initial Partner Call",
        content=(
            "Alice: We decided to proceed with a deeper technical diligence on Northwind.\n"
            "Bob: I'll reach out to our robotics advisor for a technical review by next week.\n"
            "Alice: Also, we should get the financial model by end of month.\n"
            "Carol: I'll schedule the follow-up call with the CEO this Friday."
        ),
        date="2026-06-03",
        participants=["Alice", "Bob", "Carol"],
        platform="zoom",
    )
    rt.run_until_idle()

    meetings = [o for o in graph.objects() if o.type == "meeting"]
    decisions = [o for o in graph.objects() if o.type == "meeting_decision"]
    action_items = [o for o in graph.objects() if o.type == "meeting_action_item"]
    all_tasks = [o for o in graph.objects() if o.type == "task"]

    print(f"  meetings:        {len(meetings)}")
    print(f"  decisions:       {len(decisions)}")
    print(f"  action_items:    {len(action_items)}")
    print(f"  core tasks:      {len(all_tasks)}")

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n── Graph summary ──────────────────────────────")
    type_counts: dict[str, int] = {}
    for obj in graph.objects():
        type_counts[obj.type] = type_counts.get(obj.type, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")

    print("\nDone.")


if __name__ == "__main__":
    main()
