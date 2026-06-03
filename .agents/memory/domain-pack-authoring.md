---
name: Domain pack authoring patterns
description: Key invariants and patterns for authoring domain packs (Research, VC, Codebase, Team/Ops, Meeting) in this codebase.
---

## Registry pattern
- Every pack that creates "canonical" objects uses a module-level dict registry to avoid duplicates.
- Pattern: `_THING_REGISTRY: dict[str, str] = {}` — key is unique source identifier, value is graph object id.
- Always call `clear_*_registry()` at the top of each fixture function.
- Never use `graph.objects(type=...)` inside behaviors — use `graph.get_object(id)` with registry-stored ids.

## Tool wrapper pattern
- `@tool` decorator produces a non-callable Tool object. Always define a `_fn` variant for fixture/test use.
- Pattern: define `my_fn(graph, ...)`, then `@tool(...) def my_tool(graph, ...) -> return my_fn(graph, ...)`.
- Fixtures import `*_fn` functions directly, NOT the `@tool` wrappers.

## Behavior constraints
- Behaviors only fire on `object.created` — `patch_object` does NOT re-trigger behaviors.
- No `graph.objects()` calls inside behaviors — use module-level registries instead.
- Function signature: `(event, graph, ctx, *, settings: SettingsType)`.
- Event payload access: `obj = event.payload.get("object", {})` → `obj.get("id")`, `obj.get("data", {})`.

## Source → behavior routing pattern
- Domain packs detect their source type via `data.get("kind")` on source objects.
- Common kinds used: `research_paper`, `github_webhook`, `repo_file`, `repo_manifest`, `issue`, `meeting_transcript`, `email`.
- comm_message routing: check `data.get("direction") == "inbound"` and `data.get("channel")`.

## LLM behaviors in v0.1
- All LLM-powered behaviors are mock stubs in v0.1 — deterministic, keyword/template-based.
- Mark clearly in docstring: "v0.1: mock extraction — real LLM in v0.2".

## Fixture structure
- Two fixtures per pack is the standard.
- Fixture 1: main ingestion pipeline (source → all downstream objects).
- Fixture 2: secondary workflow (cross-pack integration or alternate entry point).
- Always check relation types using `{r.source for r in graph.relations()}` — NOT r.type (see relation API quirk).

**Why:**
Learned through building all 5 domain packs (research, vc, codebase, team_ops, meeting). All 10 fixtures pass with these patterns.
