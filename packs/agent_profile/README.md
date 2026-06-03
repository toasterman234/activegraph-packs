# Agent Profile Pack — v0.1

Owns the assistant's **goals, personality, style, and standing instructions**. Provides behavior-scoped context (not a global system prompt blob) filtered by channel and audience role.

---

## Object Types

| Type | Description |
|------|-------------|
| `agent_profile` | Name, mission, personality description. Root object — typically one per assistant |
| `goal` | Standing goal with priority, status, and domain |
| `standing_instruction` | Scoped instruction with `applies_to_channel` + `applies_to_audience_role` filters |
| `personality_profile` | Tone, verbosity, formality — optionally scoped per channel/role |
| `owner_preference` | Named key/value preference, domain + channel scoped |
| `profile_context_request` | Graph-visible trigger for context assembly |
| `profile_context_view` | Assembled context slice for a specific channel/role |

---

## Behavior Map

```
agent_profile.created     → profile_registry_recorder    (indexes in local registry)
goal.created              → goal_registry_recorder        (indexes in local registry)
standing_instruction.created → instruction_registry_recorder
personality_profile.created  → personality_registry_recorder
owner_preference.created     → preference_registry_recorder

profile_context_request.created
  → profile_context_provider
      Fetches AgentProfile via graph.get_object(profile_id)
      Reads goals/instructions/personality/preferences from local registry
      Filters by channel and audience_role
      Owner-facing: includes mission (unless expose_mission_to_external=True)
      External-facing: suppresses mission; applies external-scoped instructions
      Sorts instructions by priority (highest first)
      Creates: profile_context_view
      Creates: fulfilled_by_profile(request → view)
```

---

## Context Assembly Pattern

```python
# 1. Register profile objects
profile = register_profile_fn(graph, name="Aria", mission="Help Alice build her company.")

# 2. Add goals, instructions, personality, preferences (all indexed automatically)
graph.add_object("standing_instruction", {
    "text": "Be concise with external parties.",
    "applies_to_channel": "email",
    "applies_to_audience_role": "external",
    "profile_id": profile.id,
    "priority": 80,
    ...
})

# 3. Request context for a specific channel + role
request_profile_context_fn(graph, profile_id=profile.id, channel="email", audience_role="external")
rt.run_until_idle()

# 4. Read the assembled view
views = list(graph.objects(type="profile_context_view"))
```

---

## Settings

```python
AgentProfileSettings(
    default_agent_name="Assistant",
    default_mission="Help the owner accomplish their goals efficiently.",
    default_tone="neutral",          # neutral/warm/direct/formal/casual/technical
    default_verbosity="balanced",    # concise/balanced/detailed
    default_formality="neutral",     # informal/neutral/formal
    owner_name=None,
    expose_mission_to_external=False,
    max_standing_instructions=20,
    max_active_goals=10,
)
```

---

## Registry Pattern

Context assembly uses a **local in-memory registry** (module-level dict) populated by recorder behaviors. This avoids `graph.objects()` calls in behaviors, which are unsafe in the ActiveGraph behavior context.

The registry is keyed by `profile_id` and indexes all related objects by their `profile_id` field. Clear it between tests with `clear_profile_registry()`.

---

## Composes With

- **Identity Pack** — `audience_role` from `Principal.role` shapes the context slice (owner vs. external)
- **Core Pack** — `source.created` can carry channel context for profile filtering
- **Communication Packs** — `comm_message.created` provides channel + sender_role for request assembly

---

## Relation Types

| Relation | From → To | Meaning |
|----------|-----------|---------|
| `owns_goal` | agent_profile → goal | Profile owns a goal |
| `owns_instruction` | agent_profile → standing_instruction | Profile owns an instruction |
| `owns_preference` | agent_profile → owner_preference | Profile owns a preference |
| `fulfilled_by_profile` | profile_context_request → profile_context_view | Request fulfilled |
