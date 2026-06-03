"""Codebase Pack settings — v0.1."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CodebaseSettings(BaseModel):
    auto_create_issues_as_tasks: bool = Field(
        default=True,
        description="When True, issue_tracker creates a Core task for each open issue.",
    )
    adr_path_patterns: list[str] = Field(
        default_factory=lambda: ["adr/", "docs/adr", "decisions/", "doc/arch"],
        description="Path prefixes that indicate a file is an Architecture Decision Record.",
    )
    vulnerability_severity_threshold: str = Field(
        default="medium",
        description="Minimum severity for dependency_auditor to flag a vulnerability ('low','medium','high','critical').",
    )
    max_files_per_repo: int = Field(
        default=500,
        description="Maximum CodeFile objects to create per repo ingestion.",
    )
    supported_languages: list[str] = Field(
        default_factory=lambda: ["python", "typescript", "javascript", "go", "rust", "java"],
        description="Languages to process during repo ingestion.",
    )
    github_webhook_events: list[str] = Field(
        default_factory=lambda: ["issues", "pull_request", "push", "create"],
        description="GitHub webhook event types to handle.",
    )
