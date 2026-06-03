# Meeting Pack — v0.1

Meeting ingestion, transcript processing, decision extraction, and action item creation for ActiveGraph.

## Overview

The Meeting Pack processes meeting transcripts into a structured graph of decisions, action items, and summaries. It handles both structured (`Speaker: text`) and plain-text transcript formats, flags decision and action-item segments with keyword matching, and automatically creates Core tasks from action items.

All behaviors in v0.1 use deterministic keyword-based processing — no LLM API key required.

## Object Types

| Name | Description |
|---|---|
| `meeting` | Meeting with participants, platform, and source reference |
| `transcript_segment` | One speaker turn in a transcript |
| `meeting_decision` | A decision made during a meeting |
| `meeting_action_item` | An action item with a linked Core task |
| `meeting_note` | Meeting summary or notes |

## Behaviors

| Name | Trigger | Creates |
|---|---|---|
| `transcript_ingester` | `source.created` (kind=`meeting_transcript`) | `meeting`, `transcript_segment` |
| `decision_extractor` | `transcript_segment.created` (is_decision=True) | `meeting_decision` |
| `action_item_extractor` | `transcript_segment.created` (is_action_item=True) | `meeting_action_item`, `task` |
| `meeting_summarizer` | `meeting.created` | `meeting_note` |

## Transcript Format

**Structured** (preferred — auto-detected):
```
Alice: We decided to adopt feature flags going forward.
Bob: I'll set up the integration by Thursday.
```

**Plain text** (falls back to sentence splitting):
```
The team agreed to use PostgreSQL 16. Alice will update the migration guide by Friday.
```

## Tools

- `ingest_transcript` — Ingest a meeting transcript
- `create_meeting` — Create a meeting record without a transcript
- `add_decision` — Manually add a decision to a meeting
- `add_action_item` — Manually add an action item (creates Core task)

## Quick Start

```python
from activegraph import Runtime, Graph
from packs.core import pack as core_pack, CoreSettings
from packs.meeting import pack as meeting_pack, MeetingSettings

graph = Graph()
rt = Runtime(graph)
rt.load_pack(core_pack, settings=CoreSettings())
rt.load_pack(meeting_pack, settings=MeetingSettings(
    auto_create_tasks_from_action_items=True,
))

from packs.meeting.tools import ingest_transcript_fn
ingest_transcript_fn(
    graph,
    title="Sprint Review",
    content="Alice: We decided to move to PostgreSQL 16.\nBob: I'll write the migration runbook by Friday.",
    date="2026-06-03",
    participants=["Alice", "Bob"],
    platform="zoom",
)
rt.run_until_idle()

decisions = list(graph.objects(type="meeting_decision"))
tasks = list(graph.objects(type="task"))
```

## Running Fixtures

```bash
python packs/meeting/fixtures/run_fixtures.py
```

## Composing With Other Packs

- **Core Pack** (required): tasks from action items, artifacts for notes
- **Team/Ops Pack** (optional): tasks from action items flow into milestones/assignments
- **Communication Pack** (optional): meeting as a communication channel
- **Identity Pack** (optional): resolve participant refs to principals
