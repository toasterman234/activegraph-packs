"""Assistant Bundle — the base bundle for any interactive assistant.

Packs included:
  core             — universal primitives (source, observation, task, action, artifact, memory_candidate, evaluation)
  tool_gateway     — capability execution with policy checks and credential injection
  secrets          — credential reference management (secrets never enter model context)
  memory_gateway   — memory lifecycle: candidate → evaluation → storage → retrieval
  agent_profile    — agent goals, personality, standing instructions, preferences
  identity_auth    — principal resolution, role-based permission checking
  communication    — channel-neutral messaging (CommThread, CommMessage, CommIntent)
  chat             — chat adapter (chat_input → CommMessage → ChatTurn)
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings
from packs.tool_gateway import pack as tool_gateway_pack, ToolGatewaySettings
from packs.secrets import pack as secrets_pack, SecretsSettings
from packs.memory_gateway import pack as memory_gateway_pack, MemoryGatewaySettings
from packs.agent_profile import pack as agent_profile_pack, AgentProfileSettings
from packs.identity_auth import pack as identity_auth_pack, IdentitySettings
from packs.communication import pack as communication_pack, CommunicationSettings
from packs.chat import pack as chat_pack, ChatSettings


ASSISTANT_BUNDLE = [
    core_pack,
    tool_gateway_pack,
    secrets_pack,
    memory_gateway_pack,
    agent_profile_pack,
    identity_auth_pack,
    communication_pack,
    chat_pack,
]

# Alias for backward compatibility
ASSISTANT_PACK_LIST = ASSISTANT_BUNDLE


def build_assistant(
    *,
    core_settings: CoreSettings | None = None,
    tool_gateway_settings: ToolGatewaySettings | None = None,
    secrets_settings: SecretsSettings | None = None,
    memory_gateway_settings: MemoryGatewaySettings | None = None,
    agent_profile_settings: AgentProfileSettings | None = None,
    identity_settings: IdentitySettings | None = None,
    communication_settings: CommunicationSettings | None = None,
    chat_settings: ChatSettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the Assistant Bundle loaded.

    This is the base bundle for any interactive assistant. It provides
    the full infrastructure stack: identity, memory, tool execution,
    communication, and chat.

    Args:
        core_settings: Override CoreSettings. Defaults to CoreSettings().
        tool_gateway_settings: Override ToolGatewaySettings.
        secrets_settings: Override SecretsSettings.
        memory_gateway_settings: Override MemoryGatewaySettings.
        agent_profile_settings: Override AgentProfileSettings.
        identity_settings: Override IdentitySettings.
        communication_settings: Override CommunicationSettings.
        chat_settings: Override ChatSettings.
        llm_provider: LLM provider for LLM-backed behaviors (optional in v0.1).

    Returns:
        A configured Runtime ready to run goals.
    """
    graph = Graph()
    kwargs = {}
    if llm_provider is not None:
        kwargs["llm_provider"] = llm_provider

    rt = Runtime(graph, **kwargs)

    rt.load_pack(core_pack, settings=core_settings or CoreSettings())
    rt.load_pack(tool_gateway_pack, settings=tool_gateway_settings or ToolGatewaySettings())
    rt.load_pack(secrets_pack, settings=secrets_settings or SecretsSettings())
    rt.load_pack(memory_gateway_pack, settings=memory_gateway_settings or MemoryGatewaySettings())
    rt.load_pack(agent_profile_pack, settings=agent_profile_settings or AgentProfileSettings())
    rt.load_pack(identity_auth_pack, settings=identity_settings or IdentitySettings())
    rt.load_pack(communication_pack, settings=communication_settings or CommunicationSettings())
    rt.load_pack(chat_pack, settings=chat_settings or ChatSettings())

    return rt


if __name__ == "__main__":
    print("Building assistant bundle...")
    rt = build_assistant()
    print(f"Loaded {len(ASSISTANT_BUNDLE)} packs:")
    for p in ASSISTANT_BUNDLE:
        print(f"  - {p.name} v{p.version}")
