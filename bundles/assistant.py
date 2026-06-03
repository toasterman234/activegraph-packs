"""Assistant Bundle — the base bundle for any interactive assistant.

Packs included:
  core             — universal primitives
  tool_gateway     — capability execution (planned)
  secrets          — credential management (planned)
  memory_gateway   — memory lifecycle (planned)
  agent_profile    — agent goals, personality, preferences (planned)
  identity_auth    — principal resolution, roles (planned)
  communication    — channel-neutral messaging (planned)
  chat             — chat adapter (planned)

Note: Only `core` is implemented in v0.1. The remaining packs are stubbed
and will be activated as they are implemented in subsequent tasks.
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings


# The full pack list (packs will be imported and added as implemented)
ASSISTANT_PACK_LIST = [
    core_pack,
    # tool_gateway_pack,   # Task #2
    # secrets_pack,        # Task #2
    # memory_gateway_pack, # Task #2
    # agent_profile_pack,  # Task #3
    # identity_auth_pack,  # Task #3
    # communication_pack,  # Task #4
    # chat_pack,           # Task #4
]


def build_assistant(
    *,
    core_settings: CoreSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the Assistant Bundle loaded.

    Args:
        core_settings: Override CoreSettings. Defaults to CoreSettings().
        llm_provider: LLM provider for LLM-backed behaviors. Not required
            for v0.1 (Core Pack behaviors are deterministic).

    Returns:
        A configured Runtime ready to run goals.
    """
    graph = Graph()

    kwargs = {}
    if llm_provider is not None:
        kwargs["llm_provider"] = llm_provider

    rt = Runtime(graph, **kwargs)

    rt.load_pack(core_pack, settings=core_settings or CoreSettings())

    # Additional packs will be loaded here as implemented:
    # rt.load_pack(tool_gateway_pack, settings=ToolGatewaySettings())
    # rt.load_pack(secrets_pack, settings=SecretsSettings())
    # rt.load_pack(memory_gateway_pack, settings=MemoryGatewaySettings())
    # rt.load_pack(agent_profile_pack, settings=AgentProfileSettings())
    # rt.load_pack(identity_auth_pack, settings=IdentitySettings())
    # rt.load_pack(communication_pack, settings=CommunicationSettings())
    # rt.load_pack(chat_pack, settings=ChatSettings())

    return rt


if __name__ == "__main__":
    print("Building assistant with Core Pack...")
    rt = build_assistant()
    print("Runtime created. Loaded packs:", [p.name for p in ASSISTANT_PACK_LIST])
    print("Run a goal with: rt.run_goal('...')")
