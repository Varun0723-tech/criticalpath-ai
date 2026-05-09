from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatientInput(BaseSchema):
    age: int = Field(..., description="Patient age in years.")
    symptoms: list[str] = Field(default_factory=list, description="Free-text symptom list.")


class IntakePayload(BaseSchema):
    age: int
    symptoms: list[str]


class TriageAssessment(BaseSchema):
    triage_level: Literal["Critical", "Urgent", "Normal"]
    red_flags: list[str] = Field(default_factory=list)
    reasoning: str


class DiagnosisItem(BaseSchema):
    name: str
    condition: str
    confidence: int = Field(..., ge=0, le=100)
    reason: str


class DiagnosisBundle(BaseSchema):
    diagnoses: list[DiagnosisItem]


class RiskFactorBreakdown(BaseSchema):
    baseline: int
    red_flags: int
    age: int
    severe_symptoms: int
    triage: int
    symptom_burden: int
    total: int


class RiskAssessmentResult(BaseSchema):
    risk_score: int
    risk_level: Literal["Low", "Medium", "High"]
    justification: str
    risk_interpretation: str
    weighted_factors: RiskFactorBreakdown


class RecommendationPlan(BaseSchema):
    recommended_action: str
    tests: list[str] = Field(default_factory=list)
    urgency: str
    monitoring_advice: list[str] = Field(default_factory=list)
    notes: str


class ExplainabilitySummary(BaseSchema):
    triage_decision: str
    diagnostic_rationale: str
    risk_rationale: str
    recommendation_rationale: str


class ExplanationDetails(BaseSchema):
    red_flags: list[str] = Field(default_factory=list)
    reasoning: str
    risk_factors: list[str] = Field(default_factory=list)


class AgentLog(BaseSchema):
    agent: str
    message: str
    timestamp: str
    status: Literal["processing", "completed", "fallback"]
    details: str | None = None


class PatientReport(BaseSchema):
    resourceType: Literal["Bundle"] = "Bundle"
    patient: dict[str, Any]
    observation: dict[str, Any]
    triage: TriageAssessment
    condition: list[DiagnosisItem]
    riskAssessment: RiskAssessmentResult
    carePlan: RecommendationPlan
    timestamp: str
    summary: str
    clinicalImpression: str
    riskInterpretation: str
    alerts: list[str] = Field(default_factory=list)
    systemNotices: list[str] = Field(default_factory=list)
    aiFallbackUsed: bool = False
    explanation: ExplanationDetails
    explainability: ExplainabilitySummary
    agentLogs: list[AgentLog] = Field(default_factory=list)
