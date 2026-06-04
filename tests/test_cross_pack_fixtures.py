"""pytest wrapper for the three cross-pack integration fixtures.

Each test runs one of the scripts in ``packs/fixtures/`` as a subprocess
and asserts exit code 0.  Individual test names match the integration
scenario so failures are immediately identifiable in CI output.

Cross-pack fixtures covered:
  - test_tool_gateway_core_memory      → packs/fixtures/cross_pack_integration.py
  - test_comm_chat_email_integration   → packs/fixtures/comm_chat_email_integration.py
  - test_identity_profile_entity       → packs/fixtures/identity_profile_entity_integration.py
"""

from __future__ import annotations

from conftest import assert_fixture_passed, run_fixture_script


def test_tool_gateway_core_memory() -> None:
    """Tool Gateway → Core → Memory Gateway end-to-end pipeline."""
    result = run_fixture_script("packs/fixtures/cross_pack_integration.py")
    assert_fixture_passed(result)


def test_comm_chat_email_integration() -> None:
    """Communication + Chat + Email + Identity + Core full stack."""
    result = run_fixture_script("packs/fixtures/comm_chat_email_integration.py")
    assert_fixture_passed(result)


def test_identity_profile_entity() -> None:
    """Identity/Auth + Agent Profile + Entity composition."""
    result = run_fixture_script("packs/fixtures/identity_profile_entity_integration.py")
    assert_fixture_passed(result)


def test_chat_memory_cross_session() -> None:
    """Chat long-term memory: preference written in session 1, recalled in session 2."""
    result = run_fixture_script("packs/fixtures/chat_memory_cross_session.py")
    assert_fixture_passed(result)
