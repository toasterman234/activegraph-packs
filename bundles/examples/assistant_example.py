"""Assistant Bundle example.

Demonstrates the base interactive assistant bundle:
  - Chat input creates CommMessage, ChatSession, ChatTurn
  - Identity resolves sender_ref to a Principal
  - Memory candidates are evaluated and accepted
  - Agent profile scopes context

Run with:
    python bundles/examples/assistant_example.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from packs.core import CoreSettings
from packs.identity_auth import IdentitySettings
from packs.memory_gateway import MemoryGatewaySettings
from packs.chat import ChatSettings
from bundles.assistant import build_assistant


def main():
    print("=" * 60)
    print("Assistant Bundle — demo")
    print("=" * 60)

    rt = build_assistant(
        core_settings=CoreSettings(min_confidence=0.5),
        identity_settings=IdentitySettings(
            owner_identifiers=["alice@example.com"],
            default_external_role="external",
        ),
        memory_gateway_settings=MemoryGatewaySettings(
            acceptance_threshold=0.6,
            max_items=200,
        ),
        chat_settings=ChatSettings(llm_provider="mock"),
    )

    graph = rt.graph

    print(f"\nPacks loaded: {[p.name for p in rt.loaded_packs()]}")

    # Submit a chat message
    from packs.chat.tools import submit_chat_input_fn
    turn = submit_chat_input_fn(
        graph,
        user_ref="alice@example.com",
        content="I'd like to explore the new transformer paper. Can you help me research it?",
        session_id="session-demo-1",
    )
    rt.run_until_idle()

    sources = [o for o in graph.objects() if o.type == "source"]
    messages = [o for o in graph.objects() if o.type == "comm_message"]
    principals = [o for o in graph.objects() if o.type == "principal"]
    turns = [o for o in graph.objects() if o.type == "chat_turn"]

    print(f"\nAfter chat input:")
    print(f"  sources:        {len(sources)}")
    print(f"  comm_messages:  {len(messages)}")
    print(f"  principals:     {len(principals)}")
    for p in principals:
        d = p.data or {}
        print(f"    [{p.id[:8]}] role={d.get('role')} ref={d.get('identifier_ref')}")
    print(f"  chat_turns:     {len(turns)}")
    for t in turns:
        d = t.data or {}
        am = d.get("assistant_message") or "(pending)"
        print(f"    [{t.id[:8]}] user={d.get('user_message', '')[:40]!r}")
        print(f"             asst={am[:40]!r}")

    print("\nDone.")


if __name__ == "__main__":
    main()
