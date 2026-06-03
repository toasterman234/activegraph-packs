"""Codebase Pack object and relation types — v0.1."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


class Repo(BaseModel):
    name: str
    full_name: str = Field(default="", description="owner/repo format.")
    description: str = Field(default="")
    url: Optional[str] = Field(default=None)
    default_branch: str = Field(default="main")
    language: Optional[str] = Field(default=None)
    stars: int = Field(default=0)
    open_issues_count: int = Field(default=0)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeFile(BaseModel):
    repo_id: str
    path: str = Field(description="File path within the repo.")
    language: Optional[str] = Field(default=None)
    line_count: int = Field(default=0)
    content_summary: str = Field(default="")
    last_modified_at: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeFunction(BaseModel):
    file_id: str
    name: str
    signature: str = Field(default="")
    docstring: str = Field(default="")
    line_start: Optional[int] = Field(default=None)
    line_end: Optional[int] = Field(default=None)
    complexity_score: Optional[float] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Dependency(BaseModel):
    repo_id: str
    name: str
    version: Optional[str] = Field(default=None)
    kind: Literal["direct", "transitive", "dev", "peer"] = Field(default="direct")
    ecosystem: str = Field(default="", description="E.g. 'npm', 'pypi', 'maven'.")
    has_known_vulnerability: bool = Field(default=False)
    vulnerability_summary: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Issue(BaseModel):
    repo_id: str
    issue_number: int
    title: str
    body: str = Field(default="")
    state: Literal["open", "closed"] = Field(default="open")
    labels: list[str] = Field(default_factory=list)
    author_ref: Optional[str] = Field(default=None)
    assignee_refs: list[str] = Field(default_factory=list)
    created_at: Optional[str] = Field(default=None)
    closed_at: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    task_id: Optional[str] = Field(default=None, description="Link to Core Task.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PullRequest(BaseModel):
    repo_id: str
    pr_number: int
    title: str
    body: str = Field(default="")
    state: Literal["open", "closed", "merged"] = Field(default="open")
    author_ref: Optional[str] = Field(default=None)
    base_branch: str = Field(default="main")
    head_branch: str = Field(default="")
    labels: list[str] = Field(default_factory=list)
    created_at: Optional[str] = Field(default=None)
    merged_at: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArchitectureDecision(BaseModel):
    repo_id: str
    title: str
    context: str = Field(default="")
    decision: str = Field(default="")
    consequences: str = Field(default="")
    status: Literal["proposed", "accepted", "deprecated", "superseded"] = Field(default="proposed")
    adr_number: Optional[int] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeChange(BaseModel):
    repo_id: str
    summary: str
    files_changed: list[str] = Field(default_factory=list)
    lines_added: int = Field(default=0)
    lines_removed: int = Field(default=0)
    commit_sha: Optional[str] = Field(default=None)
    pr_id: Optional[str] = Field(default=None)
    author_ref: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    repo_id: str
    suite_name: str
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    skipped: int = Field(default=0)
    coverage_pct: Optional[float] = Field(default=None)
    run_at: Optional[str] = Field(default=None)
    commit_sha: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


OBJECT_TYPES = [
    ObjectType(name="repo", schema=Repo, description="A code repository."),
    ObjectType(name="code_file", schema=CodeFile, description="A file within a repo."),
    ObjectType(name="code_function", schema=CodeFunction, description="A function or method within a file."),
    ObjectType(name="dependency", schema=Dependency, description="A package dependency declared in a repo."),
    ObjectType(name="issue", schema=Issue, description="A GitHub/GitLab issue."),
    ObjectType(name="pull_request", schema=PullRequest, description="A pull request."),
    ObjectType(name="architecture_decision", schema=ArchitectureDecision,
               description="An Architecture Decision Record (ADR)."),
    ObjectType(name="code_change", schema=CodeChange, description="A code change (commit or PR diff summary)."),
    ObjectType(name="test_result", schema=TestResult, description="A test run result."),
]

RELATION_TYPES = [
    RelationType(name="file_in_repo", source_types=("code_file",), target_types=("repo",),
                 description="File belongs to a Repo."),
    RelationType(name="function_in_file", source_types=("code_function",), target_types=("code_file",),
                 description="Function defined in a CodeFile."),
    RelationType(name="repo_depends_on", source_types=("repo",), target_types=("dependency",),
                 description="Repo declares a Dependency."),
    RelationType(name="issue_in_repo", source_types=("issue",), target_types=("repo",),
                 description="Issue belongs to a Repo."),
    RelationType(name="pr_in_repo", source_types=("pull_request",), target_types=("repo",),
                 description="PR belongs to a Repo."),
    RelationType(name="adr_in_repo", source_types=("architecture_decision",), target_types=("repo",),
                 description="ADR belongs to a Repo."),
    RelationType(name="change_in_repo", source_types=("code_change",), target_types=("repo",),
                 description="CodeChange belongs to a Repo."),
    RelationType(name="test_for_repo", source_types=("test_result",), target_types=("repo",),
                 description="TestResult belongs to a Repo."),
]
