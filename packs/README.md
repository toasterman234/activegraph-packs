# ActiveGraph Packs

A modular, open-source collection of ActiveGraph packs for building auditable, event-sourced assistants.

## What is a Pack?

A pack is a bundle of object types, behaviors, tools, prompts, and policies for a specific domain. Packs compose through shared graph state — behaviors emit events that trigger other behaviors, with no direct inter-pack function calls.

## Pack Index

| Pack | Status | Description |
|------|--------|-------------|
| [`core`](core/) | ✅ v0.1 | Universal primitives: source, observation, task, action, artifact, memory_candidate, evaluation |
| [`tool_gateway`](tool_gateway/) | 🚧 planned | Normalizes, authorizes, and records all external capability calls |
| [`secrets`](secrets/) | 🚧 planned | Credential references, scopes, and runtime injection (secrets never enter model context) |
| [`memory_gateway`](memory_gateway/) | 🚧 planned | Memory candidate acceptance, item storage, retrieval, and ranking |
| [`agent_profile`](agent_profile/) | 🚧 planned | Agent goals, personality, standing instructions, owner preferences |
| [`identity_auth`](identity_auth/) | 🚧 planned | Principal resolution, roles, permissions, auth context |
| [`entity`](entity/) | 🚧 planned | Canonical people, organizations, projects with dedupe and merge |
| [`communication`](communication/) | 🚧 planned | Channel-neutral thread/message/intent/response primitives |
| [`chat`](chat/) | 🚧 planned | Chat adapter — translates chat input into comm_message |
| [`email`](email/) | 🚧 planned | Email adapter — ingest, draft, and approval-gated send |
| [`research`](research/) | 🚧 planned | Paper, method, idea atom, hypothesis, experiment tracking |
| [`vc`](vc/) | 🚧 planned | Founder relationships, deal tracking, investment memos |
| [`codebase`](codebase/) | 🚧 planned | Repo, file, issue, PR, architecture decision tracking |
| [`team_ops`](team_ops/) | 🚧 planned | Projects, assignments, milestones extending Core task |
| [`meeting`](meeting/) | 🚧 planned | Meeting ingestion, transcript, decisions, action items |

## Pack Dependency Graph

```
kernel (activegraph runtime)
└── core                          # Universal primitives
    ├── tool_gateway              # Capability execution
    ├── secrets                   # Credential management
    ├── memory_gateway            # Memory lifecycle
    ├── agent_profile             # Agent identity
    ├── identity_auth             # Principal resolution
    ├── entity                    # Entity deduplication
    ├── communication             # Channel-neutral messaging
    │   ├── chat                  # Chat adapter
    │   └── email                 # Email adapter
    ├── research                  # Research domain
    ├── vc                        # VC/investment domain
    ├── codebase                  # Codebase domain
    ├── team_ops                  # Team/Ops domain
    └── meeting                   # Meeting domain
```

## Standard Pack Layout

```
packs/<pack_name>/
  __init__.py          # Exports `pack` and `<Name>Settings`
  object_types.py      # Pydantic schemas + ObjectType/RelationType lists
  behaviors.py         # @behavior, @llm_behavior decorators
  tools.py             # @tool decorated functions
  settings.py          # Pydantic settings (all fields have defaults)
  prompts/             # .md files with TOML frontmatter
  fixtures/            # .yaml/.json scenario fixtures
  README.md            # Behavior map, object types, usage examples
  CHANGELOG.md         # Version history starting at v0.1.0
```

Copy `_template/` to start a new pack:

```bash
cp -r packs/_template packs/my_pack
```

## Key Design Rules

1. Packs compose through **graph state**, not function calls
2. **Core stays small** — only 7 universal primitives
3. **Behavior-local context** — no global prompt blobs
4. **Secrets never enter model context**
5. **Domain packs are channel-agnostic**
6. Every pack must include **fixtures** (demo without API keys)
7. Every pack must include a **behavior map** in its README

See `replit.md` for the full Core Rules.
