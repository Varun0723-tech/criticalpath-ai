from __future__ import annotations

from backend.models.exceptions import InputValidationError
from backend.models.schemas import IntakePayload, PatientInput
from backend.services.clinical_rules import normalize_symptom


def run_intake_agent(data: PatientInput) -> IntakePayload:
    if data.age <= 0:
        raise InputValidationError("Age must be greater than 0.")

    normalized_symptoms: list[str] = []
    for symptom in data.symptoms:
        normalized = normalize_symptom(symptom)
        if normalized and normalized not in normalized_symptoms:
            normalized_symptoms.append(normalized)

    if not normalized_symptoms:
        raise InputValidationError("At least one symptom is required.")

    return IntakePayload(age=data.age, symptoms=normalized_symptoms)

