# Tests

This directory contains the pytest-discoverable test suite for `activegraph-packs`.

## How the tests work

The repo ships excellent integration-level coverage in each pack's
`fixtures/run_fixtures.py` (plus three cross-pack scripts in
`packs/fixtures/`). The files here are **thin wrappers** — they run those
scripts as subprocesses and assert exit code 0, making them discoverable by
`pytest` without rewriting any fixture logic.

```
tests/
├── conftest.py                  # shared helper: run_fixture_script, assert_fixture_passed
├── test_pack_fixtures.py        # one parametrized test per pack (16 packs)
├── test_cross_pack_fixtures.py  # one test per cross-pack integration (3 scenarios)
└── README.md                    # this file
```

## Running the tests

```bash
# Run everything
pytest

# Verbose (shows each test name)
pytest -v

# Collect only — see all test IDs without running
pytest --co -q

# Run a single pack
pytest -v -k core

# Run only cross-pack tests
pytest -v tests/test_cross_pack_fixtures.py
```

## Adding tests for a new pack

1. Add a `fixtures/run_fixtures.py` to your pack directory.  
   - Exit code **0** = all assertions pass.  
   - Exit code **1** = one or more assertions failed.  
   - See any existing pack (e.g. `packs/core/fixtures/run_fixtures.py`) for the
     pattern.

2. Add the pack name to the `PACKS` list in `tests/test_pack_fixtures.py`:

   ```python
   PACKS = [
       ...
       "my_new_pack",   # ← add here
   ]
   ```

That's it — `pytest` will discover and run it automatically.

## CI integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs `pytest` as
part of the test job.  All 19 tests (16 pack + 3 cross-pack) must pass for
CI to be green.
