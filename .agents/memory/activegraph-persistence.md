---
name: ActiveGraph persistence & resume
description: How ActiveGraph's built-in event-sourced store works and the resume-time gotchas when leveraging it.
---

# ActiveGraph persistence is built in (do not claim otherwise)

ActiveGraph (PyPI v1.0.5.post2) ships a durable, event-sourced persistence layer
in `activegraph/store/` with pluggable backends: `SQLiteEventStore` and
`PostgresEventStore`. An earlier builder report wrongly claimed "no persistence /
purely in-memory" — that was false. Verify before repeating such a claim.

## API
- Fresh run: `Runtime(graph, persist_to="path.sqlite")` (also accepts `sqlite:///...`
  / `postgres://...` URLs). Events are appended to the store as behaviors cascade.
- Resume: `Runtime.load(path, run_id=None)` resumes the most-recent run by
  **replaying the event log** to rebuild the graph projection.
- `SQLiteEventStore.most_recent_run_id(path)` → None if no run exists (use to gate
  fresh-seed vs resume).
- `rt.save_state()` flushes on demand. `rt.graph.store.close()` releases the handle.

## Critical gotcha: replay does NOT fire behaviors
Replay rebuilds objects/relations directly; it does **not** re-run `@behavior`
handlers. So any state your packs keep **outside the graph** (module-level dedup
registries, memory backends, caches) is NOT repopulated on resume. You must rebuild
it from the replayed objects yourself, or you get duplicates / lost dedup.
**Why:** the demo's identity pack keeps an in-process principal registry; without a
rebuild step, resuming then receiving a known sender created duplicate principals.
**How to apply:** after `Runtime.load(...)`, re-register packs AND walk the replayed
graph to repopulate any in-process registries before serving new events.

## Reset / wipe correctness
To truly reset a persisted demo: close the graph store, clear in-process registries,
**close** any other SQLite connections (e.g. memory backend — clearing rows is not
enough, the open handle blocks file deletion on some OSes), then delete the `.sqlite`
plus its `-wal` and `-shm` sidecars. Surface deletion failures instead of swallowing
them, or `/reset` can report success while stale data survives.

## Relation field layout is counterintuitive
`activegraph.core.graph.Relation` dataclass has fields `source`, `target`, `type`
(no `source_id`/`target_id`). They are used as:
- `rel.source` = relation type label (e.g. "grounds", "resolves_to")
- `rel.target` = source object id
- `rel.type`   = target object id
Verified empirically. Serialize as: type←source, source_id←target, target_id←type.

## add_relation() call signature is (source, target, type) — easy to invert
`graph.add_relation(source_id, target_id, type_label)` takes the two object ids
FIRST and the type label LAST. Calling it as `(type, source, target)` is silently
accepted: it builds a relation whose `source` is the type *string*, so
`graph.relations(type=...)`, `neighborhood()`, and views find nothing and the
failure surfaces far away (e.g. a context/assembler behavior "sees no neighbors").
**Why:** an entire pack was written with the args inverted; views silently returned
empty and the bug looked like a traversal/depth problem, not a bad write.
**How to apply:** when a view/neighborhood is unexpectedly empty, first verify the
relation was written with object ids in the first two positions — assert
`rel.source`/`rel.target` are real object ids, not a type label.

## SQLite single-writer caveat
The SQLite backend is single-writer; multiple processes writing the same DB file is
unsafe. Fine for a single-process demo server, not for multi-writer deployment.
