# Chat Pack Changelog

## v0.1.0 — Initial release (2026-06-03)

### Added
- 3 object types: `chat_input`, `chat_session`, `chat_turn`
- 3 relation types: `session_contains_turn`, `turn_from_input`, `session_has_thread`
- 3 behaviors:
  - `chat_ingester` — on `chat_input.created`: resolves or creates `ChatSession`, creates `source(kind=chat_message)` + `comm_message(channel=chat, inbound)` + `chat_turn`; maintains `_SESSION_REGISTRY` for per-user session continuity without `graph.objects()` scans
  - `chat_llm_responder` — on `comm_message.created (channel=chat, inbound)`: assembles context (prior turns, profile view, memory), generates response via LLM or deterministic mock stub, creates `comm_response_candidate(channel=chat, status=approved)`
  - `chat_responder` — on `comm_response_candidate.created (channel=chat, status=approved)`: patches `chat_turn.assistant_message` and `chat_turn.response_candidate_id`
- `ChatSettings` with `llm_provider`, `model`, `system_prompt_override`, `max_context_messages`, `include_memory`, `include_profile`, `auto_approve_responses`
- Tool functions: `submit_chat_input_fn`
- `llm_provider="mock"` deterministic stub for fixture runs (no API key required)
- Fixture scenarios: 3-turn conversation, session continuity, mock LLM
- Full README with behavior map and session continuity docs

### Design decisions
- `chat_llm_responder` fires on `comm_message.created` (not `chat_turn.created`) so the Communication Pack's `intent_detector` and `thread_tracker` always run first
- Session continuity uses `_SESSION_REGISTRY` keyed by `user_ref` (or explicit `session_id`) — safe for re-entrant behavior context
- `chat_responder` patches the turn rather than creating a new object — the turn is the canonical request-response unit
- Clear between tests: `clear_session_registry()`, `reset_mock_response_idx()`
