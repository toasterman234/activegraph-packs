# activegraph-packs [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source collection of [ActiveGraph](https://pypi.org/project/activegraph/) packs, bundles, a Python demo server, and a React Inspector UI. Two goals: (1) a working demo of what a multi-pack assistant substrate looks like out of the box, and (2) a pack library where the best packs can be upstreamed into the activegraph repository itself.

ActiveGraph is a reactive object-graph runtime for Python. You define objects (typed nodes), relations (typed edges), behaviors (reactive handlers that fire on mutation), and tools (callable capabilities). This repo shows how to compose 15 of those into a coherent, auditable assistant architecture — no central orchestrator, no monolithic pipeline.

---

## Quick Start

```bash
# 1. Install Python dependencies (activegraph + all packs in editable mode)
pip install -e ".[dev]"

# 2. Install Node dependencies
pnpm install

# 3. Start the API server — also launches the Python demo server as a subprocess
PORT=5000 pnpm --filter @workspace/api-server run dev

# 4. In a second terminal, start the Inspector UI
PORT=3000 pnpm --filter @workspace/activegraph-ui run dev
```

Once both are running, open `http://localhost:3000` for the Inspector UI. The API server is at `http://localhost:5000` and the Python demo server at `http://localhost:7788`.

No API key required. The demo server seeds the graph with fixture data from all loaded packs on startup and persists state to SQLite in `data/`.

To run just the demo server without the UI:

```bash
python packs/demo_server.py
# Listening on http://localhost:7788
```

---

## What's in the box

### Packs

| Pack | Description |
|------|-------------|
| `core` | Universal primitive layer: source, observation, task, action, artifact, memory_candidate, evaluation |
| `tool_gateway` | Capability execution gateway — normalizes, policy-checks, and records all external tool/API/MCP calls |
| `secrets` | Credential reference management — actual secrets never enter the model context or graph |
| `memory_gateway` | Full memory lifecycle: evaluates candidates, stores accepted items (SQLite), retrieval with keyword ranking |
| `identity_auth` | Identity resolution and permission checking — resolves sources to Principals, enforces role-based access |
| `agent_profile` | Assistant identity: goals, personality, standing instructions, scoped by channel and audience role |
| `entity` | Canonical extraction and deduplication for real-world entities (people, orgs, projects, products, repos) |
| `communication` | Channel-neutral semantic layer: threads, messages, intents, response candidates |
| `chat` | Chat adapter — translates interactive input into communication objects and manages LLM responses |
| `email` | Email adapter — threading, deduplication, draft formatting, approval-gated outbound sends |
| `research` | Knowledge tracking for academic and applied research: papers, claims, hypotheses |
| `vc` | Venture capital deal flow: founder outreach, company profiling, memo drafting, followup tracking |
| `codebase` | Engineering workflow tracking: repos, issues, PRs, architecture decisions, dependency auditing |
| `team_ops` | Project management layer extending Core tasks with assignments, milestones, workload estimation |
| `meeting` | Meeting processing: decision extraction, action item tracking, automated summarization |

Plus `packs/bridges/` — a Diligence-Core bridge that maps the bundled ActiveGraph Diligence pack outputs to Core objects (source, observation, artifact, evaluation).

### Bundles

| Bundle | Contents |
|--------|----------|
| `assistant` | core, tool_gateway, secrets, memory_gateway, agent_profile, identity_auth, communication, chat |
| `email_assistant` | assistant bundle + email, entity |
| `vc_bundle` | email_assistant bundle + diligence_core_bridge, vc, meeting |
| `research_bundle` | core, tool_gateway, memory_gateway, research |

A bundle is a preset list of packs with a factory function — not a new pack with its own ontology.

```python
from bundles import build_vc_assistant

rt = build_vc_assistant()
rt.run_goal("Diligence: Northwind Robotics")
```

---

## Architecture

The demo has three components:

```
Inspector UI (React + Vite)
       |
       |  REST (polls every 3s)
       v
API Server (Express, port 5000)
       |
       |  HTTP proxy  |  subprocess management
       v
Demo Server (Python, port 7788)
       |
       v
ActiveGraph Runtime
  ├─ 15 packs loaded
  ├─ SQLite event log     →  data/activegraph_demo.sqlite
  └─ SQLite memory store  →  data/activegraph_memory.sqlite
```

The demo server is a standalone Python HTTP server (`packs/demo_server.py`). The API server (Express) proxies requests from the React UI and manages the Python process as a subprocess — so starting the API server is enough to get the full stack running.

### Demo server endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /summary` | Object counts, pack counts, event counts |
| `GET /graph` | All objects and relations (filterable by pack) |
| `GET /trace` | Event log (supports limit, offset, pack, frame_id filters) |
| `GET /packs` | Loaded packs with their behaviors and object/relation types |
| `GET /frames` | Execution frames and their events |
| `POST /chat` | Inject a chat message into the graph |
| `POST /reset` | Wipe SQLite stores and re-seed from fixtures |

---

## Building a new pack

Copy the template scaffold:

```bash
cp -r packs/_template packs/my_pack
```

Every pack has five source files:

```
packs/my_pack/
  __init__.py        # Exports `pack` and `MyPackSettings`
  object_types.py    # Pydantic schemas, ObjectType/RelationType lists
  behaviors.py       # @behavior and @llm_behavior handlers
  tools.py           # @tool decorated functions (may be empty)
  settings.py        # Pydantic settings class (all fields must have defaults)
  prompts/           # .md prompt files with TOML frontmatter (LLM behaviors)
  fixtures/          # .yaml scenario files for testing without an API key
  README.md          # Behavior map, object types table, usage examples
  CHANGELOG.md       # Required; starts at v0.1.0
```

Register the pack in `pyproject.toml`:

```toml
[project.entry-points."activegraph.packs"]
my_pack = "packs.my_pack:pack"
```

Then reinstall: `pip install -e ".[dev]"`.

The design principle: packs coordinate by emitting graph-visible outputs that trigger other behaviors — not by calling each other directly and not through a central coordinator. See `activegraph-direction-report.md` for the full architecture rationale.

---

## Running fixtures

Each pack ships fixture scenarios in `fixtures/*.yaml` that run without an LLM or API key. All behaviors run in deterministic mode (`deterministic=True`), so no credentials are needed.

Run a single pack's fixture suite:

```bash
python packs/core/fixtures/run_fixtures.py
python packs/vc/fixtures/run_fixtures.py
python packs/memory_gateway/fixtures/run_fixtures.py
# pattern: python packs/<pack_name>/fixtures/run_fixtures.py
```

Run the cross-pack integration suites:

```bash
# Full cross-pack integration (all packs together)
python packs/fixtures/cross_pack_integration.py

# Communication + Chat + Email integration
python packs/fixtures/comm_chat_email_integration.py

# Identity + Profile + Entity integration
python packs/fixtures/identity_profile_entity_integration.py
```

The demo server also loads all fixture data on startup — `POST /reset` re-seeds from scratch if you want a clean run.

---

## Reports

- **[activegraph-builder-report.md](activegraph-builder-report.md)** — Honest field report from building this repo: what clicked, what didn't, rough edges in the ActiveGraph API, and notes for the ActiveGraph maintainers. Includes the confusing relation field naming, re-entrancy footgun, `@tool` callability issue, and a correction on the built-in persistence layer.

- **[activegraph-direction-report.md](activegraph-direction-report.md)** — 29-section architecture direction document covering the design philosophy behind this pack system: kernel vs. Core Pack, behavior specification as the primary developer interface, frames instead of a turn coordinator, memory design, Tool Gateway, pack dependencies, bundles, and the key invariants that should never be violated.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, the pack hygiene checklist, and the design rules that keep the codebase coherent.

The one-paragraph version: packs should degrade gracefully (hard-require only what they truly need), coordinate through graph-visible outputs rather than function calls, and ship fixtures that work without any API key.

---

## License

MIT. See [LICENSE](LICENSE).
