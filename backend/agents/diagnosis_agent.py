from __future__ import annotations

from backend.models.schemas import DiagnosisBundle, DiagnosisItem, IntakePayload, TriageAssessment
from backend.services.clinical_rules import confidence_from_overlap, shortlist_conditions
from backend.services.llm_service import LLMService


SYSTEM_PROMPT = (
    "Act as an ER doctor performing differential diagnosis. Return the top 3 likely conditions only. "
    "Prioritize common, clinically relevant emergency differentials and concise professional reasoning."
)


def _fallback_diagnoses(intake: IntakePayload, triage: TriageAssessment) -> list[DiagnosisItem]:
    diagnoses: list[DiagnosisItem] = []

    for profile, score, hits in shortlist_conditions(intake.symptoms):
        evidence = ", ".join(hits) if hits else "the available symptom pattern"
        diagnoses.append(
            DiagnosisItem(
                name=profile.name,
                condition=profile.name,
                confidence=confidence_from_overlap(score, triage.triage_level, len(triage.red_flags)),
                reason=f"{profile.rationale} Supporting features include {evidence}.",
            )
        )

    return diagnoses[:3]


def run_diagnosis_agent(
    intake: IntakePayload,
    triage: TriageAssessment,
    llm_service: LLMService,
) -> tuple[list[DiagnosisItem], str | None]:
    user_prompt = (
        f"Patient age: {intake.age}\n"
        f"Symptoms: {', '.join(intake.symptoms)}\n"
        f"Triage level: {triage.triage_level}\n"
        f"Red flags: {', '.join(triage.red_flags) if triage.red_flags else 'none'}\n\n"
        "Return JSON with a diagnoses array of exactly 3 objects. "
        "Each object must include name, condition, confidence, and reason. "
        "Set name and condition to the same diagnosis label. Confidence must be an integer from 0 to 100."
    )

    llm_output, fallback_reason = llm_service.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema_model=DiagnosisBundle,
    )

    if llm_output is not None and llm_output.diagnoses:
        normalized = [
            item.model_copy(
                update={
                    "name": item.name or item.condition,
                    "condition": item.condition or item.name,
                }
            )
            for item in llm_output.diagnoses[:3]
        ]
        return normalized, None

    return _fallback_diagnoses(intake, triage), fallback_reason
