# Core Pack Changelog

## v0.1.0 — Initial release (2026-06-03)

### Added
- 7 object types: `source`, `observation`, `task`, `action`, `artifact`, `memory_candidate`, `evaluation`
- 7 relation types: `grounds`, `produces`, `executes`, `generates`, `proposes`, `evaluates`, `derived_from`
- 3 deterministic behaviors:
  - `observation_extractor` — sentence splitting + heuristic scoring from sources
  - `task_linker` — Jaccard word-overlap linking of observations to open tasks
  - `memory_candidate_proposer` — proposes memory for high-confidence preference/decision/fact observations
- `CoreSettings` with configurable thresholds
- Fixture scenarios: `chat_observation_task`, `tool_result_source`, `artifact_generation`
- Full README with behavior map (Mermaid diagram)

### Design decisions
- Core is observation-first (not claim-first)
- No LLM in v0.1 — all behaviors are deterministic heuristics
- `task` is deliberately underpowered (Team/Ops Pack adds project management)
- `memory_candidate` only proposes — Memory Gateway decides acceptance
- `derived_from` relation enables bridge packs to connect domain objects to Core
