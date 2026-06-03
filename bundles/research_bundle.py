"""Research Bundle — research assistant for paper processing and hypothesis generation.

A lighter-weight bundle than the VC Bundle. Focused on research workflows:
paper ingestion, claim extraction, idea atoms, and hypothesis generation.

Packs included:
  core             — universal primitives
  tool_gateway     — capability execution (planned)
  memory_gateway   — memory for research context (planned)
  communication    — channel-neutral messaging (planned)
  chat             — chat adapter (planned)
  research         — paper, method, idea atom, hypothesis, experiment (planned)

Intentionally excludes: agent_profile, identity_auth, secrets.
Research workflows often run headlessly without user interaction.
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings

# from packs.tool_gateway import pack as tool_gateway_pack, ToolGatewaySettings  # Task #2
# from packs.memory_gateway import pack as memory_gateway_pack, MemoryGatewaySettings  # Task #2
# from packs.communication import pack as comm_pack, CommunicationSettings  # Task #4
# from packs.chat import pack as chat_pack, ChatSettings  # Task #4
# from packs.research import pack as research_pack, ResearchSettings  # Task #5

RESEARCH_PACK_LIST = [
    core_pack,
    # tool_gateway_pack,   # Task #2
    # memory_gateway_pack, # Task #2
    # comm_pack,           # Task #4
    # chat_pack,           # Task #4
    # research_pack,       # Task #5
]


def build_research_assistant(
    *,
    core_settings: CoreSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the Research Bundle loaded.

    Args:
        core_settings: Override CoreSettings.
        llm_provider: LLM provider (required for research LLM behaviors).

    Returns:
        A configured Runtime ready for research workflows.
    """
    graph = Graph()

    kwargs = {}
    if llm_provider is not None:
        kwargs["llm_provider"] = llm_provider

    rt = Runtime(graph, **kwargs)
    rt.load_pack(core_pack, settings=core_settings or CoreSettings())

    # Additional packs will be loaded here as implemented:
    # rt.load_pack(tool_gateway_pack, settings=ToolGatewaySettings())
    # rt.load_pack(memory_gateway_pack, settings=MemoryGatewaySettings())
    # rt.load_pack(comm_pack, settings=CommunicationSettings())
    # rt.load_pack(chat_pack, settings=ChatSettings())
    # rt.load_pack(research_pack, settings=research_settings or ResearchSettings())

    return rt
