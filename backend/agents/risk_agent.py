from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from backend.models.schemas import DiagnosisItem, IntakePayload, RiskAssessmentResult, RiskFactorBreakdown, TriageAssessment
from backend.services.clinical_rules import SEVERE_SYMPTOM_KEYWORDS, find_matching_keywords
from backend.services.llm_service import LLMService


class RiskNarrative(BaseModel):
    justification: str
    risk_interpretation: str


SYSTEM_PROMPT = (
    "Act as an emergency physician. Explain why this patient is high, medium, or low risk clinically. "
    "Use concise professional language and return JSON only."
)


def _risk_level(score: int) -> Literal["Low", "Medium", "High"]:
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def _weighted_score(intake: IntakePayload, triage: TriageAssessment) -> RiskFactorBreakdown:
    severe_hits = find_matching_keywords(intake.symptoms, SEVERE_SYMPTOM_KEYWORDS)

    baseline = 10
    red_flag_points = 40 if triage.red_flags else 0
    age_points = 10 if intake.age > 50 else 0
    severe_points = 20 if severe_hits else 0
    triage_points = {"Critical": 30, "Urgent": 25, "Normal": 0}[triage.triage_level]
    symptom_burden_points = min(max(len(intake.symptoms) - 1, 0) * 5, 10)
    total = min(100, baseline + red_flag_points + age_points + severe_points + triage_points + symptom_burden_points)

    return RiskFactorBreakdown(
        baseline=baseline,
        red_flags=red_flag_points,
        age=age_points,
        severe_symptoms=severe_points,
        triage=triage_points,
        symptom_burden=symptom_burden_points,
        total=total,
    )


def run_risk_agent(
    intake: IntakePayload,
    triage: TriageAssessment,
    diagnoses: list[DiagnosisItem],
    llm_service: LLMService,
) -> tuple[RiskAssessmentResult, str | None]:
    factors = _weighted_score(intake, triage)
    risk_score = factors.total
    risk_level = _risk_level(risk_score)

    user_prompt = (
        f"Patient age: {intake.age}\n"
        f"Symptoms: {', '.join(intake.symptoms)}\n"
        f"Triage level: {triage.triage_level}\n"
        f"Red flags: {', '.join(triage.red_flags) if triage.red_flags else 'none'}\n"
        f"Likely diagnoses: {', '.join(item.condition for item in diagnoses)}\n"
        f"Weighted score: {risk_score}/100\n"
        f"Weighted factors: baseline {factors.baseline}, red flags {factors.red_flags}, age {factors.age}, "
        f"severe symptoms {factors.severe_symptoms}, triage {factors.triage}, symptom burden {factors.symptom_burden}\n\n"
        "Return JSON with justification and risk_interpretation only."
    )

    llm_output, fallback_reason = llm_service.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema_model=RiskNarrative,
    )

    if llm_output is not None:
        return (
            RiskAssessmentResult(
                risk_score=risk_score,
                risk_level=risk_level,
                justification=llm_output.justification,
                risk_interpretation=llm_output.risk_interpretation,
                weighted_factors=factors,
            ),
            None,
        )

    justification = (
        f"This patient scored {risk_score}/100 using weighted emergency triage factors. "
        f"Red flags contributed {factors.red_flags} points, age contributed {factors.age}, "
        f"severe symptom burden contributed {factors.severe_symptoms}, triage severity contributed {factors.triage}, "
        f"and overall symptom burden contributed {factors.symptom_burden}."
    )
    interpretation = (
        f"Overall clinical risk is {risk_level.lower()} because the presentation is {triage.triage_level.lower()} acuity "
        f"with {'documented red flags' if triage.red_flags else 'no rule-based red flags'}."
    )
    return (
        RiskAssessmentResult(
            risk_score=risk_score,
            risk_level=risk_level,
            justification=justification,
            risk_interpretation=interpretation,
            weighted_factors=factors,
        ),
        fallback_reason,
    )
