from __future__ import annotations

from backend.models.schemas import DiagnosisItem, IntakePayload, RecommendationPlan, RiskAssessmentResult, TriageAssessment
from backend.services.clinical_rules import monitoring_guidance, suggested_tests
from backend.services.llm_service import LLMService


class RecommendationLLMOutput(RecommendationPlan):
    pass


SYSTEM_PROMPT = "Suggest safe next steps for emergency care triage with realistic tests and monitoring advice. Return JSON only."


def _base_recommendation(
    intake: IntakePayload,
    triage: TriageAssessment,
    diagnoses: list[DiagnosisItem],
    risk: RiskAssessmentResult,
) -> RecommendationPlan:
    tests = suggested_tests(intake.symptoms, triage.triage_level)
    monitoring = monitoring_guidance(triage.triage_level, intake.symptoms)
    differential_names = ", ".join(item.condition for item in diagnoses[:3])

    if triage.triage_level == "Critical":
        return RecommendationPlan(
            recommended_action="Immediate ER admission and physician evaluation with continuous monitoring.",
            tests=tests,
            urgency="Immediate",
            monitoring_advice=monitoring,
            notes=(
                f"High-acuity presentation with concern for {differential_names}. "
                "Activate emergency response pathways and do not delay escalation."
            ),
        )

    if triage.triage_level == "Urgent":
        return RecommendationPlan(
            recommended_action="Prompt doctor assessment today with targeted diagnostic testing.",
            tests=tests,
            urgency="Same day",
            monitoring_advice=monitoring,
            notes=(
                f"Moderate-to-high risk presentation with possible {differential_names}. "
                "Escalate sooner if symptoms worsen, new chest pain develops, or breathing status changes."
            ),
        )

    return RecommendationPlan(
        recommended_action="Supportive home care with close symptom monitoring and follow-up if symptoms persist.",
        tests=tests[:2],
        urgency="Routine follow-up",
        monitoring_advice=monitoring,
        notes=(
            f"Current risk is {risk.risk_level.lower()} based on available information. "
            "Seek urgent care if red-flag symptoms such as chest pain, shortness of breath, confusion, or severe bleeding occur."
        ),
    )


def run_recommendation_agent(
    intake: IntakePayload,
    triage: TriageAssessment,
    diagnoses: list[DiagnosisItem],
    risk: RiskAssessmentResult,
    llm_service: LLMService,
) -> tuple[RecommendationPlan, str | None]:
    baseline_plan = _base_recommendation(intake, triage, diagnoses, risk)

    user_prompt = (
        f"Patient age: {intake.age}\n"
        f"Symptoms: {', '.join(intake.symptoms)}\n"
        f"Triage level: {triage.triage_level}\n"
        f"Risk score: {risk.risk_score}\n"
        f"Likely diagnoses: {', '.join(item.condition for item in diagnoses)}\n"
        f"Rule-based recommendation: {baseline_plan.recommended_action}\n"
        f"Suggested tests: {', '.join(baseline_plan.tests) if baseline_plan.tests else 'none'}\n"
        f"Monitoring advice: {', '.join(baseline_plan.monitoring_advice) if baseline_plan.monitoring_advice else 'none'}\n\n"
        "Return JSON with recommended_action, tests, urgency, monitoring_advice, and notes."
    )

    llm_output, fallback_reason = llm_service.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema_model=RecommendationLLMOutput,
    )

    if llm_output is not None:
        merged_tests = baseline_plan.tests[:]
        for test in llm_output.tests:
            if test not in merged_tests:
                merged_tests.append(test)

        merged_monitoring = baseline_plan.monitoring_advice[:]
        for item in llm_output.monitoring_advice:
            if item not in merged_monitoring:
                merged_monitoring.append(item)

        return (
            RecommendationPlan(
                recommended_action=llm_output.recommended_action,
                tests=merged_tests[:6],
                urgency=llm_output.urgency,
                monitoring_advice=merged_monitoring[:4],
                notes=llm_output.notes,
            ),
            None,
        )

    return baseline_plan, fallback_reason
