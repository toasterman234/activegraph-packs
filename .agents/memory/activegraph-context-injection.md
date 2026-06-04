---
name: ActiveGraph context-injection seam (chat)
description: How packs feed context into the chat LLM prompt, and the sync-vs-event-driven rule for same-cascade context.
---

# Chat context-injection seam

The chat LLM never sees a hand-written prompt — `chat_llm_responder` builds a
**depth-1 view** around the inbound `comm_message` and the runtime serializes that
view into the prompt. Anything linked to the message via `provides_context_for`
(a `chat_context`, a `profile_context_view`, etc.) is therefore captured
automatically. This is the seam every context-providing behavior reuses.

**Rule:** a behavior that wants its context in the *same* responder turn must run
BEFORE `chat_llm_responder` in the BEHAVIORS list AND assemble its view
**synchronously** (call a pure helper, not a request→view event).

**Why:** an event-driven request→view round-trip lands the view in a *later*
batch — too late for the responder firing in the same cascade. This is why
`chat_profile_context` calls `agent_profile.assemble_profile_view(...)` directly
instead of emitting a `profile_context_request`. The event-driven
`profile_context_request → profile_context_view` flow is still correct when
requester and reader are in different cascades.

# Registry rebuild after Runtime.load

`Runtime.load(...)` replay recreates graph objects but does NOT re-fire recorder
behaviors, so in-memory registries (principal dedup, profile, session, thread)
start empty on resume. Resume paths must call the pack's `rebuild_*_registry(graph)`
helper (e.g. `rebuild_profile_registry`, `rebuild_principal_registry`) which read
`graph.all_objects()` to repopulate. Pattern lives in `demo_server._build_runtime`.

**How to apply:** when adding a new pack with a module-level registry populated by
a `*_recorder` behavior, also add a `rebuild_*_registry` and call it on resume, or
the feature silently no-ops after a restart.
