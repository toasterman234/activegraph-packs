# Documentation

Supporting docs for **activegraph-packs** — a prototyping ground and reference
showcase for how packs should be built and composed on top of
[ActiveGraph](https://pypi.org/project/activegraph/).

Start here, then follow links into the rest of the repo.

## Guides

- **[Concepts: Core and Layered Packs](concepts.md)** — the mental model. The
  event-sourced graph substrate, the split between the minimal **Core Pack** and the
  **layered (domain) packs** that build on it, how coordination emerges without an
  orchestrator, and the invariants that hold it together. **Read this first.**

- **[Architecture](architecture.md)** — the runnable demo stack (Inspector UI →
  API server → Python runtime), the demo server endpoints, frames vs. the trace, and
  a tour of the Inspector UI pages.

- **[Long-term memory](long-term-memory.md)** — a worked example of cross-pack
  composition: how the Chat Pack and Memory Gateway build durable, cross-session
  memory with no LLM or API key, and the swappable seams for ingestion, storage
  backend, and embedding-based retrieval.

## Reference

- **[Core Pack](../packs/core/README.md)** — the seven universal primitives and
  their relations, in detail.
- **[Pack index](../packs/README.md)** — every pack, its tier, and the dependency
  graph.
- **[Bundles](../bundles/README.md)** — preset pack collections with factory
  functions.
- **[Contributing](../CONTRIBUTING.md)** — how to author a new pack and the
  open-source hygiene checklist.

## Background reports

These are the original design documents that motivated the repo. They are narrative
and opinionated rather than reference material, but they capture the *why*.

- **[Direction report](../activegraph-direction-report.md)** — the full architecture
  rationale: kernel vs. Core Pack, behavior specs as the primary interface, frames
  instead of a turn coordinator, memory design, and the invariants.
- **[Builder report](../activegraph-builder-report.md)** — a field report from
  building this repo: what worked, what didn't, and rough edges in the ActiveGraph
  API worth knowing before you start.
