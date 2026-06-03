"""VC Bundle — full venture capital assistant.

Extends the Email Assistant Bundle with investment diligence,
founder relationship management, and meeting ingestion.

Packs included (beyond Email Assistant Bundle):
  diligence             — investment diligence (bundled with activegraph)
  diligence_core_bridge — maps diligence objects to Core primitives (planned)
  vc                    — founder tracking, deal rounds, investment memos (planned)
  meeting               — meeting ingestion, transcript, decisions (planned)

This is the most feature-complete bundle and the reference implementation
for how domain packs compose through shared graph state.
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings
from bundles.email_assistant import EMAIL_ASSISTANT_PACK_LIST, build_email_assistant

# from packs.bridges.diligence_core import pack as bridge_pack   # Task #6
# from packs.vc import pack as vc_pack, VCSettings               # Task #5
# from packs.meeting import pack as meeting_pack, MeetingSettings # Task #5

# Try to load the bundled diligence pack
try:
    from activegraph.packs import load_by_name
    diligence_pack = load_by_name("diligence")
    _HAS_DILIGENCE = True
except Exception:
    diligence_pack = None
    _HAS_DILIGENCE = False


VC_PACK_LIST = EMAIL_ASSISTANT_PACK_LIST + [
    # diligence_pack if _HAS_DILIGENCE else None,  # bundled with activegraph
    # bridge_pack,   # Task #6
    # vc_pack,       # Task #5
    # meeting_pack,  # Task #5
]


def build_vc_assistant(
    *,
    core_settings: CoreSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the VC Bundle loaded.

    The strongest first demo: email review with CRM context, founder
    enrichment, and investment memo generation.

    Args:
        core_settings: Override CoreSettings.
        llm_provider: LLM provider (required for LLM-backed behaviors).

    Returns:
        A configured Runtime ready for VC workflows.
    """
    rt = build_email_assistant(
        core_settings=core_settings,
        llm_provider=llm_provider,
    )

    # Load diligence pack if available
    if _HAS_DILIGENCE and diligence_pack is not None:
        try:
            from activegraph.packs.diligence import DiligenceSettings
            rt.load_pack(diligence_pack, settings=DiligenceSettings())
            print(f"  Loaded diligence pack v{diligence_pack.version}")
        except Exception as e:
            print(f"  Warning: could not load diligence pack: {e}")

    # Additional packs will be loaded here as implemented:
    # rt.load_pack(bridge_pack)
    # rt.load_pack(vc_pack, settings=vc_settings or VCSettings())
    # rt.load_pack(meeting_pack, settings=meeting_settings or MeetingSettings())

    return rt
