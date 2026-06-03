---
name: ActiveGraph Relation API field names
description: The Relation object returned by graph.relations() has counterintuitive field names; source=relation_type, target=source_obj_id, type=target_obj_id.
---

# ActiveGraph Relation Object Field Names

## The rule
`graph.relations()` returns `Relation` objects with these fields:
- `r.source` = the **relation type name** (e.g. `"grounds"`, `"produces"`)
- `r.target` = the **source object ID** (the left node)
- `r.type`   = the **target object ID** (the right node)

To get all relation type names in a graph:
```python
relation_types = {r.source for r in graph.relations()}
```

**Why:** Field names are counterintuitive — `source` holds a string type name, not an object reference. Confirmed by inspection of `activegraph==1.0.5.post2`.

**How to apply:** Any code that reads relation metadata must use `r.source` for the type name, not `r.type`. Applies to fixture runners, behavior maps, graph queries, and any code that introspects relations.
