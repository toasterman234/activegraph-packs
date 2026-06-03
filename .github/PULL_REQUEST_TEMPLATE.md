## What this PR does

<!-- One paragraph. What changed and why. -->

## Pack hygiene checklist

If this PR adds or modifies a pack, confirm each item:

- [ ] `README.md` exists with behavior map, object types table, relation types table, dependency declarations, and 2+ usage examples
- [ ] `CHANGELOG.md` exists starting at v0.1.0 (or updated with this change)
- [ ] `fixtures/` contains at least one scenario fixture
- [ ] All behaviors have `description` strings
- [ ] All object types have `description` strings in `ObjectType(...)`
- [ ] `settings.py` — all fields have defaults (no required fields without defaults)
- [ ] Pack fixture runner passes (`python packs/<pack_name>/fixtures/run_fixtures.py`)
- [ ] No secrets, credentials, or API keys are hardcoded anywhere
- [ ] `pyproject.toml` entry point is registered (if this is a new pack)

## Design rules

- [ ] No central coordinator or orchestration manager — coordination is emergent from graph-visible behavior outputs
- [ ] Domain pack does not own communication, identity, or tool execution — only consumes those capabilities if available
- [ ] No direct inter-pack method calls — packs coordinate through graph state only

## Testing

<!-- How did you verify this? Include the fixture runner output or paste relevant lines. -->

```
python packs/<pack_name>/fixtures/run_fixtures.py
# Paste output here
```

## Notes for reviewers

<!-- Anything the reviewer needs to know that isn't obvious from the code. -->
