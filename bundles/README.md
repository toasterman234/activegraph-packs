# ActiveGraph Bundles

Bundles are pre-assembled collections of packs for common assistant configurations.

## What is a Bundle?

A bundle is **not a pack**. It has no new object types, behaviors, or ontology.
It is simply:
1. A list of packs to load
2. A factory function that creates a configured Runtime with all packs loaded
3. Default settings appropriate for the bundle's use case

Use a bundle when you want a working assistant with a specific capability set
without manually loading each pack.

## Available Bundles

### Assistant Bundle (`bundles/assistant.py`)
The base bundle for any interactive assistant.

Packs: `core`, `tool_gateway`, `secrets`, `memory_gateway`, `agent_profile`, `identity_auth`, `communication`, `chat`

```python
from bundles.assistant import build_assistant
rt = build_assistant()
rt.run_goal("Help me with...")
```

### Email Assistant Bundle (`bundles/email_assistant.py`)
Adds email processing, entity tracking, and CRM capabilities.

Packs: *assistant bundle* + `email`, `entity`

```python
from bundles.email_assistant import build_email_assistant
rt = build_email_assistant()
rt.run_goal("Review my email from the founder.")
```

### VC Bundle (`bundles/vc_bundle.py`)
Full venture capital assistant with diligence, founder tracking, and meeting ingestion.

Packs: *email assistant bundle* + `diligence`, `diligence_core_bridge`, `vc`, `meeting`

```python
from bundles.vc_bundle import build_vc_assistant
rt = build_vc_assistant()
rt.run_goal("Diligence: Northwind Robotics")
```

### Research Bundle (`bundles/research_bundle.py`)
Research assistant for paper processing and hypothesis generation.

Packs: `core`, `tool_gateway`, `memory_gateway`, `communication`, `chat`, `research`

```python
from bundles.research_bundle import build_research_assistant
rt = build_research_assistant()
rt.run_goal("Research: Transformer attention mechanisms")
```

## Customizing a Bundle

Bundles are starting points. Add or remove packs as needed:

```python
from activegraph import Runtime, Graph
from bundles.assistant import ASSISTANT_PACK_LIST
from packs.codebase import pack as codebase_pack
from packs.codebase import CodebaseSettings

# Start from the assistant bundle and add codebase
all_packs = ASSISTANT_PACK_LIST + [codebase_pack]

rt = Runtime(Graph())
for p in all_packs:
    rt.load_pack(p)
rt.load_pack(codebase_pack, settings=CodebaseSettings())
rt.run_goal("Review the latest PR.")
```

## When NOT to Use Bundles

- If you're building a focused domain tool that only needs 2-3 packs, load them directly
- If you need fine-grained control over settings per pack, don't use the factory functions
- Bundles are for getting started fast, not for production tuning

## Bundle Compatibility Matrix

| Pack | Assistant | Email Asst | VC | Research |
|------|-----------|------------|-------|----------|
| core | ✅ | ✅ | ✅ | ✅ |
| tool_gateway | ✅ | ✅ | ✅ | ✅ |
| secrets | ✅ | ✅ | ✅ | ❌ |
| memory_gateway | ✅ | ✅ | ✅ | ✅ |
| agent_profile | ✅ | ✅ | ✅ | ❌ |
| identity_auth | ✅ | ✅ | ✅ | ❌ |
| communication | ✅ | ✅ | ✅ | ✅ |
| chat | ✅ | ✅ | ✅ | ✅ |
| email | ❌ | ✅ | ✅ | ❌ |
| entity | ❌ | ✅ | ✅ | ❌ |
| diligence | ❌ | ❌ | ✅ | ❌ |
| vc | ❌ | ❌ | ✅ | ❌ |
| meeting | ❌ | ❌ | ✅ | ❌ |
| research | ❌ | ❌ | ❌ | ✅ |
