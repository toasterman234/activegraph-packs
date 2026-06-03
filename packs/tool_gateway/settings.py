"""Settings for Tool Gateway Pack."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ToolGatewaySettings(BaseModel):
    """Configuration for Tool Gateway Pack v0.1.

    Controls how capability calls are policy-checked and recorded.
    """

    auto_approve_risk_classes: list[Literal["low", "medium", "high", "critical"]] = Field(
        default=["low"],
        description=(
            "Risk classes that are automatically approved without human review. "
            "All other risk classes require explicit approval via rt.approve(). "
            "Set to ['low', 'medium'] for a more permissive policy."
        ),
    )

    record_input_data: bool = Field(
        default=True,
        description=(
            "If True, capability call input_data is recorded in CapabilityCall. "
            "Set to False in production to avoid logging sensitive inputs."
        ),
    )

    record_output_data: bool = Field(
        default=True,
        description=(
            "If True, capability result output_data is recorded in CapabilityResult. "
            "Set to False in production to avoid logging sensitive outputs."
        ),
    )

    max_output_chars: int = Field(
        default=10000,
        ge=100,
        description="Maximum characters to store in CapabilityResult.output_data.",
    )

    create_source_from_result: bool = Field(
        default=True,
        description=(
            "If True, result_sourcer behavior creates a Core source object from "
            "each CapabilityResult so downstream behaviors can extract observations."
        ),
    )
