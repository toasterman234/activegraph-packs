# Contributing to activegraph-packs

This is an open-source library of [ActiveGraph](https://pypi.org/project/activegraph/) packs. The best packs from this repo are candidates for upstreaming into the activegraph package itself.

Before contributing, read the design philosophy in [activegraph-direction-report.md](activegraph-direction-report.md). The short version: packs coordinate through graph-visible behavior outputs, not function calls and not a central coordinator.

---

## Adding a new pack

### 1. Copy the template scaffold

```bash
cp -r packs/_template packs/my_pack
```

The template gives you the required file layout. Do not skip files — all of them are required.

### 2. Implement the pack

Every pack has exactly these source files:

```
packs/my_pack/
  __init__.py        # Exports `pack` and `MyPackSettings`
  object_types.py    # Pydantic schemas + ObjectType/RelationType lists
  behaviors.py       # @behavior, @llm_behavior, @relation_behavior handlers
  tools.py           # @tool decorated functions (may be empty if pack has none)
  settings.py        # Pydantic settings — all fields must have defaults
  prompts/           # .md prompt files with TOML frontmatter (LLM behaviors only)
  fixtures/          # .yaml scenario files for testing without an LLM or API key
  README.md          # Required: behavior map, object types table, usage examples
  CHANGELOG.md       # Required: starts at v0.1.0
```

### 3. Define object and relation types

In `object_types.py`, define Pydantic schemas and register them with `ObjectType` and `RelationType`:

```python
from pydantic import BaseModel
from activegraph import ObjectType, RelationType

class MyObject(BaseModel):
    name: str
    description: str = ""
    metadata: dict = {}

MY_OBJECT_TYPE = ObjectType(
    name="my_pack/my_object",
    schema=MyObject,
    description="A one-sentence description of what this object represents.",
)
```

### 4. Write behaviors

In `behaviors.py`, use `@behavior` for deterministic handlers and `@llm_behavior` for LLM-backed ones:

```python
from activegraph import behavior

@behavior(
    name="my_extractor",
    on=["object.created"],
    where={"object.type": "source"},
    creates=["my_pack/my_object"],
    description="Extracts my_objects from incoming sources.",
)
def my_extractor(self, graph, obj):
    data = obj.data
    result = graph.add_object("my_pack/my_object", {
        "name": data.get("content", "")[:80],
        "metadata": {},
    })
```

Every behavior **must** declare `name`, `on`, `where`, `creates`, and `description`. LLM behaviors must also declare `output_schema`, `tools`, and `deterministic=True` for fixture runs.

### 5. Write at least one fixture

Fixtures live in `packs/my_pack/fixtures/` as YAML files. They must run without any LLM or API key:

```yaml
description: |
  Basic scenario: a source arrives and my_extractor creates a my_object.
objects:
  - type: source
    data:
      kind: email
      content: "Example content to extract from."
      sender_ref: "user@example.com"
      channel: email
      metadata: {}
expected_outputs:
  my_objects:
    min_count: 1
```

Copy the fixture runner from another pack and adjust the imports.

### 6. Register the pack

Add an entry to `pyproject.toml`:

```toml
[project.entry-points."activegraph.packs"]
my_pack = "packs.my_pack:pack"
```

Reinstall: `pip install -e ".[dev]"`.

### 7. Verify before submitting

```bash
# Run your pack's fixture suite
python packs/my_pack/fixtures/run_fixtures.py

# Run the cross-pack integration suites to make sure you haven't broken anything
python packs/fixtures/cross_pack_integration.py
python packs/fixtures/comm_chat_email_integration.py
python packs/fixtures/identity_profile_entity_integration.py
```

All fixture runners exit with code 0 on success, 1 on failure. CI runs all of them.

---

## Open-source hygiene checklist

Before opening a PR, confirm every item:

- [ ] `README.md` exists with behavior map, object types table, relation types table, dependency declarations, and 2+ usage examples
- [ ] `CHANGELOG.md` exists starting at v0.1.0
- [ ] `fixtures/` contains at least one scenario fixture
- [ ] All behaviors have `description` strings
- [ ] All object types have `description` strings in `ObjectType(...)`
- [ ] `settings.py` — all fields have defaults (no required fields without defaults)
- [ ] Pack fixture runner passes (`python packs/<pack_name>/fixtures/run_fixtures.py`)
- [ ] No secrets, credentials, or API keys are hardcoded anywhere
- [ ] `pyproject.toml` entry point is registered

---

## Behavior specification rules

Every behavior must declare:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Unique within the pack, `snake_case` |
| `on` | yes | List of event types that trigger it (e.g. `["object.created"]`) |
| `where` | yes | Filter dict narrowing which events qualify |
| `creates` | yes | List of object types this behavior produces |
| `description` | yes | One sentence explaining what it does and why |

LLM behaviors additionally require:

| Field | Description |
|-------|-------------|
| `output_schema` | Pydantic model for structured output |
| `tools` | List of tools the behavior may call (empty list if none) |
| `deterministic=True` | Always set for fixture-backed behaviors (required for CI) |

---

## Inter-pack dependency rules

- **`requires`** — hard dependencies; the runtime will refuse to load without them
- **`integrates_with`** — optional packs that improve behavior; the pack must work without them
- Never put a domain concept in a pack just because it's convenient — it belongs in the most specific pack that truly owns it
- Do not duplicate object types across packs — use relations to connect objects from different packs
- Core Pack objects (`source`, `observation`, `task`, `action`, `artifact`, `memory_candidate`, `evaluation`) are the universal lingua franca — domain packs should map their outputs to Core types

---

## Design rules

These rules reflect the core philosophy of the ActiveGraph architecture. Violating them will require changes before a PR can merge.

- Do **not** build a central coordinator or orchestration manager — coordination is emergent from graph-visible behavior outputs
- Do **not** let chat own the assistant loop — communication is just one channel
- Do **not** put context assembly in a global blob — each behavior gets a behavior-specific view
- Do **not** refactor existing packs (e.g. Diligence) — add bridges instead
- Do **not** add `context_requirement` objects yet — use behavior view specs instead
- Do **not** put person/company/claim/evidence in Core — those belong in Entity/domain packs

---

## Submitting a pack for upstream consideration

A pack may be a candidate for upstreaming into the [activegraph](https://pypi.org/project/activegraph/) repository itself. The bar is:

1. **Deterministic behaviors** — all behaviors work in fixture mode without an API key
2. **Clean README with behavior map** — a clear text or Mermaid diagram of the behavior chain
3. **Fixture coverage** — at least one fixture per significant behavior
4. **No hardcoded secrets** — credentials are declared as `credential_ref` objects and injected by the Secrets pack
5. **Channel-agnostic** (for domain packs) — the pack works whether the triggering input came from chat, email, SMS, API, or a scheduled workflow
6. **General-purpose** — useful to many ActiveGraph users, not specific to a single organization or use case

If you believe your pack meets this bar, open a PR and note "upstream candidate" in the description. We will coordinate with the ActiveGraph maintainers.

---

## Naming conventions

| Element | Convention | Example |
|---------|------------|---------|
| Pack directory | `snake_case` | `tool_gateway`, `agent_profile` |
| Pack name in code | matches directory | `Pack(name="tool_gateway", ...)` |
| Object types | `snake_case` nouns | `memory_candidate`, `comm_message` |
| Relation types | `snake_case` verbs/prepositions | `grounds`, `produces`, `derived_from` |
| Behaviors | `snake_case` verb phrases | `observation_extractor`, `entity_resolver` |
| Settings classes | `PascalCase` + `Settings` | `CoreSettings`, `EmailSettings` |

---

## Development setup

```bash
# Install all packs in editable mode + dev dependencies
pip install -e ".[dev]"

# After adding a new pack, reinstall to register the entry point
pip install -e ".[dev]"

# Run a single pack's fixture suite
python packs/<pack_name>/fixtures/run_fixtures.py

# Run all cross-pack integration suites
python packs/fixtures/cross_pack_integration.py
python packs/fixtures/comm_chat_email_integration.py
python packs/fixtures/identity_profile_entity_integration.py
```

No API key is needed for any of the above.
