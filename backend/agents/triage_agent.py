from __future__ import annotations

from backend.models.schemas import IntakePayload, TriageAssessment
from backend.services.clinical_rules import RED_FLAG_KEYWORDS, find_matching_keywords, higher_acuity, infer_triage
from backend.services.llm_service import LLMService


class TriageLLMOutput(TriageAssessment):
    pass


SYSTEM_PROMPT = (
    "Act as a senior ER triage nurse. Prioritize patient safety. Explain clinical reasoning clearly. "
    "Use concise, professional language and return JSON only."
)


def run_triage_agent(intake: IntakePayload, llm_service: LLMService) -> tuple[TriageAssessment, str | None]:
    # Combine deterministic red-flag detection with model reasoning without ever lowering acuity.
    rule_red_flags = find_matching_keywords(intake.symptoms, RED_FLAG_KEYWORDS)
    rule_level, rule_reasoning = infer_triage(intake.symptoms, intake.age)

    user_prompt = (
        f"Patient age: {intake.age}\n"
        f"Symptoms: {', '.join(intake.symptoms)}\n"
        f"Rule-detected red flags: {', '.join(rule_red_flags) if rule_red_flags else 'none'}\n\n"
        "Return a conservative triage decision in JSON with keys triage_level, red_flags, and reasoning. "
        "Reasoning should be short but professional."
    )

    llm_output, fallback_reason = llm_service.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema_model=TriageLLMOutput,
    )

    if llm_output is not None:
        triage_level = higher_acuity(rule_level, llm_output.triage_level)
        merged_red_flags = sorted(set(rule_red_flags + llm_output.red_flags))
        reasoning = llm_output.reasoning

        if triage_level != llm_output.triage_level:
            reasoning = (
                f"{llm_output.reasoning} Safety rules kept the final triage level at {triage_level} "
                f"because concerning features were detected: {', '.join(rule_red_flags) if rule_red_flags else 'higher-acuity symptom burden'}."
            )

        return (
            TriageAssessment(
                triage_level=triage_level,
                red_flags=merged_red_flags,
                reasoning=reasoning,
            ),
            None,
        )

    return (
        TriageAssessment(
            triage_level=rule_level,
            red_flags=rule_red_flags,
            reasoning=rule_reasoning,
        ),
        fallback_reason,
    )
