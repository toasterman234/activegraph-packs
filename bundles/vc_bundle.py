"""VC Bundle — full venture capital assistant.

Extends the Email Assistant Bundle with investment diligence,
founder relationship management, and meeting ingestion.

Packs included (beyond Email Assistant Bundle):
  diligence             — investment diligence (bundled with activegraph)
  diligence_core_bridge — maps diligence objects to Core primitives
  vc                    — founder tracking, deal rounds, investment memos
  meeting               — meeting ingestion, transcript, decisions, action items

This is the most feature-complete bundle and the reference implementation
for how domain packs compose through shared graph state.
"""

from __future__ import annotations

from activegraph import Pack, Runtime
from activegraph.packs import load_by_name

from packs.bridges import pack as diligence_core_bridge_pack, DiligenceCoreBridgeSettings
from packs.vc import pack as vc_pack, VCSettings
from packs.meeting import pack as meeting_pack, MeetingSettings

from bundles.email_assistant import (
    EMAIL_ASSISTANT_BUNDLE,
    build_email_assistant,
    CoreSettings,
    ToolGatewaySettings,
    SecretsSettings,
    MemoryGatewaySettings,
    AgentProfileSettings,
    IdentitySettings,
    CommunicationSettings,
    ChatSettings,
    EntitySettings,
    EmailSettings,
)


# ---------------------------------------------------------------------------
# Compatibility shim for Diligence pack
# ---------------------------------------------------------------------------

def _load_compat_diligence_pack() -> Pack | None:
    """Load the bundled Diligence pack, stripping relation types that conflict
    with Core Pack (specifically `derived_from`, which both declare).

    Returns a new Pack instance with the conflicting relation type removed, or
    None if the Diligence pack is not available.
    """
    try:
        d = load_by_name("diligence")
    except Exception:
        return None

    # Build a compat copy that omits Core-owned relation types so Core + Diligence
    # can co-exist in the same Runtime without a PackConflictError.
    _CORE_OWNED_RELATIONS = {"derived_from"}
    return Pack(
        name=d.name,
        version=d.version,
        description=d.description,
        object_types=d.object_types,
        relation_types=tuple(
            r for r in d.relation_types if r.name not in _CORE_OWNED_RELATIONS
        ),
        behaviors=d.behaviors,
        tools=d.tools,
        policies=d.policies,
        prompts=d.prompts,
        settings_schema=d.settings_schema,
    )


_compat_diligence_pack = _load_compat_diligence_pack()
_HAS_DILIGENCE = _compat_diligence_pack is not None


VC_BUNDLE = EMAIL_ASSISTANT_BUNDLE + [
    p for p in [
        _compat_diligence_pack if _HAS_DILIGENCE else None,
        diligence_core_bridge_pack,
        vc_pack,
        meeting_pack,
    ]
    if p is not None
]

VC_PACK_LIST = VC_BUNDLE


def build_vc_assistant(
    *,
    core_settings: CoreSettings | None = None,
    tool_gateway_settings: ToolGatewaySettings | None = None,
    secrets_settings: SecretsSettings | None = None,
    memory_gateway_settings: MemoryGatewaySettings | None = None,
    agent_profile_settings: AgentProfileSettings | None = None,
    identity_settings: IdentitySettings | None = None,
    communication_settings: CommunicationSettings | None = None,
    chat_settings: ChatSettings | None = None,
    entity_settings: EntitySettings | None = None,
    email_settings: EmailSettings | None = None,
    vc_settings: VCSettings | None = None,
    meeting_settings: MeetingSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the VC Bundle loaded.

    The most feature-complete bundle. Combines email processing, entity
    tracking, investment diligence, founder CRM, and meeting ingestion.

    The Diligence pack is loaded via a compatibility shim that strips its
    `derived_from` relation declaration (already owned by Core Pack), allowing
    both to co-exist in the same Runtime without a PackConflictError.

    The diligence-core bridge ensures that Diligence pack outputs (documents,
    claims, memos, risks) appear as Core primitives (sources, observations,
    artifacts, evaluations) alongside VC Pack outputs in the same graph.

    Args:
        core_settings: Override CoreSettings.
        tool_gateway_settings: Override ToolGatewaySettings.
        secrets_settings: Override SecretsSettings.
        memory_gateway_settings: Override MemoryGatewaySettings.
        agent_profile_settings: Override AgentProfileSettings.
        identity_settings: Override IdentitySettings.
        communication_settings: Override CommunicationSettings.
        chat_settings: Override ChatSettings.
        entity_settings: Override EntitySettings.
        email_settings: Override EmailSettings.
        vc_settings: Override VCSettings.
        meeting_settings: Override MeetingSettings.
        llm_provider: LLM provider (recommended for VC LLM behaviors).

    Returns:
        A configured Runtime ready for VC workflows.
    """
    rt = build_email_assistant(
        core_settings=core_settings,
        tool_gateway_settings=tool_gateway_settings,
        secrets_settings=secrets_settings,
        memory_gateway_settings=memory_gateway_settings,
        agent_profile_settings=agent_profile_settings,
        identity_settings=identity_settings,
        communication_settings=communication_settings,
        chat_settings=chat_settings,
        entity_settings=entity_settings,
        email_settings=email_settings,
        llm_provider=llm_provider,
    )

    if _HAS_DILIGENCE and _compat_diligence_pack is not None:
        try:
            from activegraph.packs.diligence import DiligenceSettings
            rt.load_pack(_compat_diligence_pack, settings=DiligenceSettings())
        except Exception:
            rt.load_pack(_compat_diligence_pack)

    rt.load_pack(diligence_core_bridge_pack, settings=DiligenceCoreBridgeSettings())
    rt.load_pack(vc_pack, settings=vc_settings or VCSettings())
    rt.load_pack(meeting_pack, settings=meeting_settings or MeetingSettings())

    return rt


if __name__ == "__main__":
    print("Building VC assistant bundle...")
    rt = build_vc_assistant()
    print(f"Loaded {len(VC_BUNDLE)} packs:")
    for p in VC_BUNDLE:
        print(f"  - {p.name} v{p.version}")
