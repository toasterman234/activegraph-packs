"""Research Bundle — research assistant for paper processing and hypothesis generation.

A focused bundle for research workflows. Lighter than the VC Bundle —
intentionally excludes agent_profile, identity_auth, and secrets since
research pipelines often run headlessly.

Packs included:
  core             — universal primitives
  tool_gateway     — capability execution for external API calls
  memory_gateway   — memory for research context and findings
  communication    — channel-neutral messaging
  chat             — chat adapter for interactive research queries
  research         — paper ingestion, claim extraction, idea atoms, hypothesis generation
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings
from packs.tool_gateway import pack as tool_gateway_pack, ToolGatewaySettings
from packs.memory_gateway import pack as memory_gateway_pack, MemoryGatewaySettings
from packs.communication import pack as communication_pack, CommunicationSettings
from packs.chat import pack as chat_pack, ChatSettings
from packs.research import pack as research_pack, ResearchSettings


RESEARCH_BUNDLE = [
    core_pack,
    tool_gateway_pack,
    memory_gateway_pack,
    communication_pack,
    chat_pack,
    research_pack,
]

# Alias for backward compatibility
RESEARCH_PACK_LIST = RESEARCH_BUNDLE


def build_research_assistant(
    *,
    core_settings: CoreSettings | None = None,
    tool_gateway_settings: ToolGatewaySettings | None = None,
    memory_gateway_settings: MemoryGatewaySettings | None = None,
    communication_settings: CommunicationSettings | None = None,
    chat_settings: ChatSettings | None = None,
    research_settings: ResearchSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the Research Bundle loaded.

    Headless-friendly: no identity or secrets packs, so it works without
    owner configuration. Add identity_auth manually if user-facing.

    Args:
        core_settings: Override CoreSettings.
        tool_gateway_settings: Override ToolGatewaySettings.
        memory_gateway_settings: Override MemoryGatewaySettings.
        communication_settings: Override CommunicationSettings.
        chat_settings: Override ChatSettings.
        research_settings: Override ResearchSettings.
        llm_provider: LLM provider (recommended for research LLM behaviors).

    Returns:
        A configured Runtime ready for research workflows.
    """
    graph = Graph()
    kwargs = {}
    if llm_provider is not None:
        kwargs["llm_provider"] = llm_provider

    rt = Runtime(graph, **kwargs)

    rt.load_pack(core_pack, settings=core_settings or CoreSettings())
    rt.load_pack(tool_gateway_pack, settings=tool_gateway_settings or ToolGatewaySettings())
    rt.load_pack(memory_gateway_pack, settings=memory_gateway_settings or MemoryGatewaySettings())
    rt.load_pack(communication_pack, settings=communication_settings or CommunicationSettings())
    rt.load_pack(chat_pack, settings=chat_settings or ChatSettings())
    rt.load_pack(research_pack, settings=research_settings or ResearchSettings())

    return rt


if __name__ == "__main__":
    print("Building research assistant bundle...")
    rt = build_research_assistant()
    print(f"Loaded {len(RESEARCH_BUNDLE)} packs:")
    for p in RESEARCH_BUNDLE:
        print(f"  - {p.name} v{p.version}")
