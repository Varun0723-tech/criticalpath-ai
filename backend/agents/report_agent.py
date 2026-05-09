from __future__ import annotations

from datetime import datetime, timezone

from backend.models.schemas import AgentLog, DiagnosisItem, ExplainabilitySummary, ExplanationDetails, IntakePayload, PatientReport, RecommendationPlan, RiskAssessmentResult, TriageAssessment


def _build_summary(
    intake: IntakePayload,
    triage: TriageAssessment,
    diagnoses: list[DiagnosisItem],
    risk: RiskAssessmentResult,
    recommendation: RecommendationPlan,
) -> str:
    lead_conditions = ", ".join(item.name for item in diagnoses[:2])
    return (
        f"Clinical impression: {intake.age}-year-old patient with {', '.join(intake.symptoms)} triaged as "
        f"{triage.triage_level}. Leading considerations are {lead_conditions}. "
        f"Overall risk is {risk.risk_score}/100 ({risk.risk_level}). "
        f"Recommended disposition: {recommendation.recommended_action}"
    )


def _clinical_impression(triage: TriageAssessment, diagnoses: list[DiagnosisItem]) -> str:
    lead_conditions = ", ".join(item.name for item in diagnoses[:3])
    return (
        f"Presentation is assessed as {triage.triage_level.lower()} acuity. "
        f"Most relevant differential diagnoses include {lead_conditions}."
    )


def _risk_factors(intake: IntakePayload, triage: TriageAssessment, risk: RiskAssessmentResult) -> list[str]:
    factors: list[str] = []

    if triage.red_flags:
        factors.append(f"Red flags present: {', '.join(triage.red_flags)}")
    if intake.age > 50:
        factors.append("Age over 50 increased the weighted risk score.")
    if risk.weighted_factors.severe_symptoms:
        factors.append("Severe symptom pattern contributed additional risk weight.")
    if risk.weighted_factors.symptom_burden:
        factors.append("Multiple active symptoms increased overall acuity.")
    factors.append(f"Triage severity was classified as {triage.triage_level}.")
    return factors


def build_fhir_report(
    intake: IntakePayload,
    triage: TriageAssessment,
    diagnoses: list[DiagnosisItem],
    risk: RiskAssessmentResult,
    recommendation: RecommendationPlan,
    agent_logs: list[AgentLog],
    *,
    system_notices: list[str],
    ai_fallback_used: bool,
) -> PatientReport:
    timestamp = datetime.now(timezone.utc).isoformat()
    alerts: list[str] = []

    if triage.triage_level == "Critical":
        alerts.append("High Risk Patient - Immediate Attention Required")
    if triage.red_flags:
        alerts.append(f"Red flags detected: {', '.join(triage.red_flags)}")

    return PatientReport(
        patient={
            "resourceType": "Patient",
            "age": intake.age,
        },
        observation={
            "resourceType": "Observation",
            "symptoms": intake.symptoms,
        },
        triage=triage,
        condition=diagnoses,
        riskAssessment=risk,
        carePlan=recommendation,
        timestamp=timestamp,
        summary=_build_summary(intake, triage, diagnoses, risk, recommendation),
        clinicalImpression=_clinical_impression(triage, diagnoses),
        riskInterpretation=risk.risk_interpretation,
        alerts=alerts,
        systemNotices=system_notices,
        aiFallbackUsed=ai_fallback_used,
        explanation=ExplanationDetails(
            red_flags=triage.red_flags,
            reasoning=triage.reasoning,
            risk_factors=_risk_factors(intake, triage, risk),
        ),
        explainability=ExplainabilitySummary(
            triage_decision=triage.reasoning,
            diagnostic_rationale="; ".join(
                f"{item.name} ({item.confidence}% confidence): {item.reason}" for item in diagnoses[:3]
            ),
            risk_rationale=risk.justification,
            recommendation_rationale=recommendation.notes,
        ),
        agentLogs=agent_logs,
    )
