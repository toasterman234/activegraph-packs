"""Settings for Secrets Pack."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecretsSettings(BaseModel):
    """Configuration for Secrets Pack v0.1.

    Controls how credential references are resolved and usage is recorded.
    All fields have safe defaults.
    """

    env_prefix: str = Field(
        default="",
        description=(
            "Optional prefix prepended to credential names when looking up "
            "environment variables. Example: prefix='MYAPP_' means credential "
            "'OPENAI_KEY' resolves env var 'MYAPP_OPENAI_KEY'."
        ),
    )

    record_usage_events: bool = Field(
        default=True,
        description=(
            "If True, every credential resolution creates a SecretUsageEvent "
            "in the graph for auditability."
        ),
    )

    fail_on_missing: bool = Field(
        default=False,
        description=(
            "If True, raise ValueError when a credential cannot be resolved. "
            "If False, return None and let the calling behavior handle the gap."
        ),
    )
