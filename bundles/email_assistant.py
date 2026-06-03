"""Email Assistant Bundle.

Extends the Assistant Bundle with email processing and entity tracking.

Packs included (beyond Assistant Bundle):
  email   — email ingestion, drafting, approval-gated send (planned)
  entity  — canonical people/organizations with dedupe (planned)

Note: email and entity packs are planned for Task #3 and #4.
This file defines the bundle structure and factory function.
"""

from __future__ import annotations

from activegraph import Graph, Runtime

from packs.core import pack as core_pack, CoreSettings

# from packs.email import pack as email_pack, EmailSettings    # Task #4
# from packs.entity import pack as entity_pack, EntitySettings  # Task #3

from bundles.assistant import ASSISTANT_PACK_LIST, build_assistant


EMAIL_ASSISTANT_PACK_LIST = ASSISTANT_PACK_LIST + [
    # email_pack,   # Task #4
    # entity_pack,  # Task #3
]


def build_email_assistant(
    *,
    core_settings: CoreSettings | None = None,
    # email_settings: EmailSettings | None = None,
    # entity_settings: EntitySettings | None = None,
    llm_provider=None,
) -> Runtime:
    """Create a Runtime with the Email Assistant Bundle loaded.

    Includes the full Assistant Bundle plus email and entity packs.

    Args:
        core_settings: Override CoreSettings.
        llm_provider: LLM provider for LLM-backed behaviors.

    Returns:
        A configured Runtime ready to process emails.
    """
    rt = build_assistant(core_settings=core_settings, llm_provider=llm_provider)

    # Additional packs will be loaded here as implemented:
    # rt.load_pack(entity_pack, settings=entity_settings or EntitySettings())
    # rt.load_pack(email_pack, settings=email_settings or EmailSettings())

    return rt
