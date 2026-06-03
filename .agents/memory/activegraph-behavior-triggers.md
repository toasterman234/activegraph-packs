---
name: How ActiveGraph behaviors trigger (Runtime + Graph integration)
description: Behaviors fire automatically when objects are added to a Graph that has a Runtime attached. Call run_until_idle() to let cascading behavior chains complete.
---

# ActiveGraph Behavior Trigger Pattern

## The rule
When a `Runtime` is attached to a `Graph`, behaviors fire automatically as objects are added via `graph.add_object()`. The runtime hooks into the graph's event system.

To ensure all cascading behavior chains complete (e.g. observation_extractor fires → creates observation → memory_candidate_proposer fires):
```python
graph.add_object("source", {...})
rt.run_until_idle()  # drains the event queue
```

There is **no** `rt.emit_event()` public method. The correct way to trigger behaviors is to add objects to the graph, then call `run_until_idle()`.

**Why:** Runtime subscribes to graph events internally. `run_until_idle()` processes the full cascade.

**How to apply:** Fixture runners, integration tests, and demo scripts must follow: add objects → `run_until_idle()` → inspect graph state.
