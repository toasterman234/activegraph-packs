"""Team/Ops Pack settings — v0.1."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamOpsSettings(BaseModel):
    auto_assign_tasks: bool = Field(
        default=False,
        description="When True, assignment_suggester creates Assignment objects automatically.",
    )
    default_capacity_hours_per_week: float = Field(
        default=40.0,
        description="Default weekly capacity hours per person for workload estimation.",
    )
    task_candidate_hint: str = Field(
        default="task_candidate",
        description="Observation category hint that triggers task_triager.",
    )
    overload_threshold_pct: float = Field(
        default=90.0,
        description="Workload percentage above which a person is considered overloaded.",
    )
    milestone_warning_days: int = Field(
        default=7,
        description="Warn when a milestone is within this many days of its target date.",
    )
    require_review_for_critical_tasks: bool = Field(
        default=True,
        description="Automatically create ReviewRequest for tasks with priority=critical.",
    )
