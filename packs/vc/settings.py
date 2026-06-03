"""VC Pack settings — v0.1."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VCSettings(BaseModel):
    founder_email_keywords: list[str] = Field(
        default_factory=lambda: [
            "raise", "fundraise", "funding", "investor", "investment",
            "seed", "series", "deck", "pitch", "round", "term sheet",
            "lead", "check size", "partner", "vc", "venture",
            "intro", "warm intro", "backed by",
        ],
        description="Keywords that indicate an email is a founder outreach.",
    )
    auto_draft_memo: bool = Field(
        default=True,
        description="When True, memo_drafter fires automatically on founder outreach detection.",
    )
    require_approval_for_lp_updates: bool = Field(
        default=True,
        description="LP updates require approval before sending.",
    )
    followup_default_days: int = Field(
        default=7,
        description="Default follow-up window in days.",
    )
    owner_firm_name: Optional[str] = Field(
        default=None,
        description="Name of the VC firm (used in memo headers and LP updates).",
    )
    investment_stage_focus: list[str] = Field(
        default_factory=lambda: ["seed", "series-a"],
        description="Stages the fund focuses on (used for relevance scoring).",
    )
