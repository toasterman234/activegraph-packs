---
name: New pack proposal
about: Propose a new pack for this library
labels: new-pack
---

## Pack name

<!-- snake_case directory name, e.g. `calendar`, `crm`, `invoice` -->

## Domain

<!-- One sentence: what real-world domain or problem does this pack cover? -->

## Object types

<!-- List the object types the pack would own. Each should be a noun in snake_case.
     Reference Core types (source, observation, task, action, artifact, memory_candidate, evaluation)
     rather than duplicating them. -->

| Type | Description |
|------|-------------|
| `my_object` | ... |

## Behaviors

<!-- List the behaviors, including what triggers each one and what it creates.
     Format: trigger_object → behavior_name → output_object -->

```
source.created (kind=email)
  → my_extractor
      creates my_object
```

## Dependencies

- **requires:** <!-- hard dependencies (pack names) -->
- **integrates_with:** <!-- optional packs that improve behavior -->

## Why it belongs here vs. a separate repo

<!-- This library is for packs that are general-purpose enough to be useful to many
     ActiveGraph users and could eventually be upstreamed into the activegraph package.
     Explain why this pack meets that bar. -->

## Upstream candidate?

<!-- Do you think this pack is a candidate for upstreaming into the activegraph repo?
     If yes, briefly explain why. -->

- [ ] Yes, I believe this pack is upstream-ready
- [ ] No, it's too domain-specific for upstream

## Fixture

<!-- Can you include or sketch a fixture scenario that runs without an API key?
     This is a requirement before the pack can be merged. -->

```yaml
description: |
  Example scenario for my_pack.
objects:
  - type: source
    data:
      kind: email
      content: "..."
expected_outputs:
  my_objects:
    min_count: 1
```
