# Research Pack — v0.1

Paper/claim/method/idea discovery and hypothesis generation for ActiveGraph.

## Overview

The Research Pack provides a complete knowledge graph layer for academic and applied research workflows. It ingests research papers from structured sources, extracts claims as observations, distills atomic research ideas, and synthesizes research directions from converging idea atoms.

All behaviors in v0.1 use deterministic mock stubs — no LLM API key required.

## Object Types

| Name | Description |
|---|---|
| `paper` | Research paper with title, abstract, authors, venue, keywords |
| `author` | Research author with affiliation and paper list |
| `venue` | Publication venue: journal, conference, workshop, preprint |
| `method` | Research method or algorithm referenced in papers |
| `benchmark` | Benchmark task with SOTA metric tracking |
| `dataset` | Research dataset referenced in papers |
| `idea_atom` | Atomic research idea distilled from one or more papers |
| `research_direction` | Synthesized direction from multiple idea atoms |
| `experiment` | Proposed or running research experiment |

## Behaviors

| Name | Trigger | Creates |
|---|---|---|
| `paper_ingester` | `source.created` (kind=`research_paper`) | `paper`, `author`, `venue` |
| `claim_extractor` | `paper.created` | `observation` (claim sentences) |
| `idea_atom_extractor` | `paper.created` | `idea_atom` |
| `hypothesis_generator` | `idea_atom.created` (coherence ≥ threshold) | `research_direction` |
| `research_direction_synthesizer` | `idea_atom.created` | `research_direction` (cross-paper synthesis) |

## Tools

- `ingest_research_paper` — Create a research paper source
- `create_idea_atom` — Directly create an idea atom
- `create_experiment` — Create a research experiment linked to a direction

## Quick Start

```python
from activegraph import Runtime, Graph
from packs.core import pack as core_pack, CoreSettings
from packs.research import pack as research_pack, ResearchSettings

graph = Graph()
rt = Runtime(graph)
rt.load_pack(core_pack, settings=CoreSettings())
rt.load_pack(research_pack, settings=ResearchSettings(
    min_coherence_for_hypothesis=0.5,
    max_ideas_per_paper=5,
))

# Ingest a paper
from packs.research.tools import ingest_research_paper_fn
source = ingest_research_paper_fn(
    graph,
    title="Attention Is All You Need",
    abstract="We propose the Transformer architecture...",
    authors="Vaswani et al.",
    venue="NeurIPS 2017",
    year=2017,
    keywords=["attention", "transformer"],
)
rt.run_until_idle()

papers = list(graph.objects(type="paper"))
ideas = list(graph.objects(type="idea_atom"))
directions = list(graph.objects(type="research_direction"))
```

## Running Fixtures

```bash
python packs/research/fixtures/run_fixtures.py
```

## Relation Types

`cites`, `authored_by`, `published_in`, `uses_method`, `reports_benchmark`, `uses_dataset`, `proposes_idea`, `composes_direction`, `tests_direction`, `derived_from_source`

## Composing With Other Packs

- **Core Pack** (required): observations, tasks, artifacts, memory candidates
- **Entity Pack** (optional): resolve author names to canonical Entity objects
- **Memory Gateway Pack** (optional): promote key research claims to durable memory
