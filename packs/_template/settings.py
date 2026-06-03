"""Settings for the template pack.

All fields must have defaults — packs should work with zero configuration.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TemplateSettings(BaseModel):
    """Configuration for the template pack.

    Replace with your actual settings.
    """

    enabled: bool = True
    max_objects_per_run: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum objects this pack will create in a single run.",
    )
