"""VC Pack object and relation types — v0.1."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from activegraph.packs import ObjectType, RelationType


class CompanyProfile(BaseModel):
    name: str
    description: str = Field(default="")
    stage: Literal["pre-seed", "seed", "series-a", "series-b", "growth", "public", "unknown"] = Field(default="unknown")
    sector: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    founded_year: Optional[int] = Field(default=None)
    hq_location: Optional[str] = Field(default=None)
    entity_id: Optional[str] = Field(default=None, description="Link to Entity Pack entity.")
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FounderProfile(BaseModel):
    name: str
    email: Optional[str] = Field(default=None)
    linkedin_url: Optional[str] = Field(default=None)
    background_summary: str = Field(default="")
    company_id: Optional[str] = Field(default=None)
    entity_id: Optional[str] = Field(default=None)
    principal_ref: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DealRound(BaseModel):
    company_id: str
    round_type: Literal["pre-seed", "seed", "series-a", "series-b", "growth", "bridge", "other"] = Field(default="seed")
    target_amount: Optional[float] = Field(default=None, description="Target raise in USD.")
    committed_amount: Optional[float] = Field(default=None)
    status: Literal["prospecting", "diligence", "term_sheet", "closing", "closed", "passed"] = Field(default="prospecting")
    lead_investor: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TractionMetric(BaseModel):
    company_id: str
    metric_name: str = Field(description="E.g. 'ARR', 'MRR', 'DAU', 'NPS'.")
    value: float
    unit: str = Field(default="USD", description="Unit of measurement.")
    period: Optional[str] = Field(default=None, description="E.g. '2026-Q1'.")
    growth_rate: Optional[float] = Field(default=None, description="MoM or YoY growth rate.")
    source_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestmentMemo(BaseModel):
    company_id: str
    title: str
    content: str = Field(default="")
    thesis_summary: str = Field(default="")
    key_risks: list[str] = Field(default_factory=list)
    status: Literal["draft", "proposed", "approved", "rejected"] = Field(default="draft")
    artifact_id: Optional[str] = Field(default=None, description="Link to Core Artifact.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvestmentThesis(BaseModel):
    title: str
    summary: str
    sectors: list[str] = Field(default_factory=list)
    stage_focus: list[str] = Field(default_factory=list)
    key_signals: list[str] = Field(default_factory=list, description="Signals to look for.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class DealRisk(BaseModel):
    company_id: str
    risk_text: str
    category: Literal["market", "team", "product", "financial", "legal", "technical", "other"] = Field(default="other")
    severity: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    mitigation: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Followup(BaseModel):
    company_id: str
    description: str
    due_at: Optional[str] = Field(default=None)
    status: Literal["pending", "done", "cancelled"] = Field(default="pending")
    task_id: Optional[str] = Field(default=None, description="Link to Core Task.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class LPUpdate(BaseModel):
    title: str
    content: str = Field(default="")
    period: Optional[str] = Field(default=None)
    deal_ids: list[str] = Field(default_factory=list)
    status: Literal["draft", "approved", "sent"] = Field(default="draft")
    artifact_id: Optional[str] = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


OBJECT_TYPES = [
    ObjectType(name="company_profile", schema=CompanyProfile,
               description="A startup or company being evaluated for investment."),
    ObjectType(name="founder_profile", schema=FounderProfile,
               description="A founder associated with a company under evaluation."),
    ObjectType(name="deal_round", schema=DealRound,
               description="A fundraising round in progress or under evaluation."),
    ObjectType(name="traction_metric", schema=TractionMetric,
               description="A reported business metric (ARR, DAU, NPS, etc.)."),
    ObjectType(name="investment_memo", schema=InvestmentMemo,
               description="A structured investment memorandum for a company."),
    ObjectType(name="investment_thesis", schema=InvestmentThesis,
               description="The investor's thesis: sectors, stages, and key signals."),
    ObjectType(name="deal_risk", schema=DealRisk,
               description="A risk identified during evaluation of a deal."),
    ObjectType(name="followup", schema=Followup,
               description="A follow-up item for a company or founder."),
    ObjectType(name="lp_update", schema=LPUpdate,
               description="A portfolio update drafted for limited partners."),
]

RELATION_TYPES = [
    RelationType(name="founded_by", source_types=("company_profile",), target_types=("founder_profile",),
                 description="Company was founded by a Founder."),
    RelationType(name="raised_in", source_types=("company_profile",), target_types=("deal_round",),
                 description="Company is raising in a DealRound."),
    RelationType(name="reports_metric", source_types=("company_profile",), target_types=("traction_metric",),
                 description="Company reports a TractionMetric."),
    RelationType(name="memo_for", source_types=("investment_memo",), target_types=("company_profile",),
                 description="InvestmentMemo is for a Company."),
    RelationType(name="risk_in", source_types=("deal_risk",), target_types=("company_profile",),
                 description="DealRisk identified in a Company evaluation."),
    RelationType(name="followup_for", source_types=("followup",), target_types=("company_profile",),
                 description="Followup item associated with a Company."),
    RelationType(name="founder_outreach_source", source_types=("founder_profile",), target_types=("source",),
                 description="FounderProfile derived from a communication Source."),
    RelationType(name="derived_from_comm", source_types=("company_profile", "founder_profile"),
                 target_types=("source",),
                 description="Profile derived from a communication source."),
]
