# Chat Adapter Pack v0.1

Translates interactive chat input into channel-neutral CommMessage objects.

## Purpose

Chat Pack is the adapter between a chat interface and the Communication Pack's
semantic layer. It handles session continuity, per-turn context assembly, and
LLM-based response generation. With `llm_provider="mock"`, it runs entirely
without API keys (useful for fixtures and tests).

## Object Types

| Type | Description |
|---|---|
| `chat_input` | Raw input from chat interface. Entry point for the adapter. |
| `chat_session` | Persistent session grouping multiple ChatTurns |
| `chat_turn` | Single request-response exchange (user_message + assistant_message) |

## Relation Types

| Relation | Source → Target | Description |
|---|---|---|
| `session_contains_turn` | chat_session → chat_turn | Session contains a turn |
| `turn_from_input` | chat_turn → chat_input | Turn created from input |
| `session_has_thread` | chat_session → comm_thread | Session linked to CommThread |

## Behavior Map

```
chat_input.created
  → chat_ingester
      resolves/creates ChatSession (by user_ref or session_id)
      creates: source(kind=chat_message), comm_message(channel=chat, inbound)
      creates: chat_turn(user_message=content, turn_number=N)
      relations: derived_from_source, session_contains_turn, turn_from_input
      → (triggers thread_tracker in Communication Pack → CommThread)

comm_message.created [channel=chat, direction=inbound]
  → chat_llm_responder
      assembles context: prior turns, profile view, memory (when loaded)
      if llm_provider="mock": deterministic stub response
      creates: comm_response_candidate(channel=chat, status=approved*)
      relations: response_to
      * auto_approve_responses=True by default

comm_response_candidate.created [channel=chat, status=approved]
  → chat_responder
      patches: chat_turn.assistant_message = content
      patches: chat_turn.response_candidate_id = candidate.id

  → response_dispatcher (Communication Pack)
      patches: comm_response_candidate.status = "sent"
```

## Session Continuity

`chat_ingester` maintains `_SESSION_REGISTRY` (user_ref → session state):

1. First message for a `user_ref`: creates new `ChatSession` + `CommThread`
2. Subsequent messages (same `user_ref`): resumes existing session, increments `turn_number`
3. Explicit `session_id` in `ChatInput`: always resumes that exact session

## Settings

```python
ChatSettings(
    llm_provider="mock",           # "mock" | "openai" | "anthropic" | "openrouter"
    model="gpt-4o-mini",           # Ignored for mock
    system_prompt_override=None,   # Override AgentProfile system prompt
    max_context_messages=10,       # Prior turns in LLM context
    include_memory=True,           # Include Memory Gateway context (if loaded)
    include_profile=True,          # Include AgentProfile context (if loaded)
    auto_approve_responses=True,   # Auto-approve chat responses (no owner gate)
)
```

## Demo: 3-Turn Conversation

```python
from activegraph import Runtime, Graph
from packs.core import pack as core_pack
from packs.communication import pack as comm_pack
from packs.chat import pack as chat_pack, ChatSettings
from packs.chat.tools import submit_chat_input_fn

g = Graph()
rt = Runtime(g)
rt.load_pack(core_pack)
rt.load_pack(comm_pack)
rt.load_pack(chat_pack, settings=ChatSettings(llm_provider="mock"))

# Turn 1
submit_chat_input_fn(g, user_ref="alice@example.com", content="What is the status of the deal?")
rt.run_until_idle()

# Turn 2 (auto-resumes by user_ref)
submit_chat_input_fn(g, user_ref="alice@example.com", content="Please draft a summary.")
rt.run_until_idle()

# Turn 3
submit_chat_input_fn(g, user_ref="alice@example.com", content="What are the next steps?")
rt.run_until_idle()

# Inspect turns
turns = list(g.objects(type="chat_turn"))
for t in turns:
    print(f"Turn {t.data['turn_number']}:")
    print(f"  User: {t.data['user_message']}")
    print(f"  Assistant: {t.data['assistant_message']}")
```

## Composes With

- **Core Pack** (required): source creation
- **Communication Pack** (required): CommMessage, CommThread, intent_detector, thread_tracker
- **Identity Pack** (optional): source.sender_ref triggers principal_resolver
- **Agent Profile Pack** (optional): ProfileContextView in LLM context when `include_profile=True`
- **Memory Gateway Pack** (optional): memory retrieval when `include_memory=True`

## Notes

- `clear_session_registry()` and `clear_thread_registry()` between test fixtures
- `reset_mock_response_idx()` for reproducible mock responses
- Real LLM integration is wired but requires API key and non-mock provider setting
