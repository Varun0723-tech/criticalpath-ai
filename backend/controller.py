from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from backend.agents.diagnosis_agent import run_diagnosis_agent
from backend.agents.intake_agent import run_intake_agent
from backend.agents.recommendation_agent import run_recommendation_agent
from backend.agents.report_agent import build_fhir_report
from backend.agents.risk_agent import run_risk_agent
from backend.agents.triage_agent import run_triage_agent
from backend.models.exceptions import AgentProcessingError
from backend.models.schemas import AgentLog, PatientInput, PatientReport
from backend.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize_fallback_reason(reason: str | None) -> str:
    if not reason:
        return "AI reasoning unavailable, using safe fallback."

    normalized = reason.lower()
    if "insufficient_quota" in normalized or "quota" in normalized or "billing" in normalized:
        return "OpenAI quota is unavailable for the configured key, using safe fallback."
    if "invalid_api_key" in normalized or "incorrect api key" in normalized or "401" in normalized:
        return "The configured OpenAI API key was rejected, using safe fallback."
    if "timeout" in normalized or "timed out" in normalized:
        return "OpenAI reasoning timed out, using safe fallback."
    if "connection" in normalized or "dns" in normalized or "network" in normalized:
        return "OpenAI reasoning is temporarily unreachable, using safe fallback."
    return "AI reasoning unavailable, using safe fallback."


def process_patient(data: dict[str, Any] | PatientInput) -> PatientReport:
    try:
        patient_input = data if isinstance(data, PatientInput) else PatientInput.model_validate(data)
        llm_service = get_llm_service()
        agent_logs: list[AgentLog] = []
        system_notices: list[str] = []
        ai_fallback_used = False

        def add_notice(message: str) -> None:
            nonlocal ai_fallback_used
            ai_fallback_used = True
            if message not in system_notices:
                system_notices.append(message)

        def add_log(agent: str, message: str, status: str = "completed", details: str | None = None) -> None:
            entry = AgentLog(agent=agent, message=message, status=status, details=details, timestamp=_timestamp())
            agent_logs.append(entry)
            logger.info("%s | %s", agent, message)

        if not llm_service.available:
            add_notice(_summarize_fallback_reason(llm_service.unavailable_reason))

        add_log("Intake Agent", "Validating patient intake.", status="processing")
        intake = run_intake_agent(patient_input)
        add_log(
            "Intake Agent",
            "Validated patient input and normalized symptoms.",
            status="completed",
            details=f"Age {intake.age}; symptoms: {', '.join(intake.symptoms)}",
        )

        add_log("Triage Agent", "Reviewing acuity and red flags.", status="processing")
        triage, triage_fallback = run_triage_agent(intake, llm_service)
        add_log("Triage Agent", f"Final severity set to {triage.triage_level}.", status="completed", details=triage.reasoning)
        if triage_fallback:
            add_notice(_summarize_fallback_reason(triage_fallback))
            add_log(
                "Triage Agent",
                "AI triage reasoning unavailable; conservative fallback applied.",
                status="fallback",
                details=_summarize_fallback_reason(triage_fallback),
            )

        add_log("Diagnosis Agent", "Generating differential diagnosis.", status="processing")
        diagnoses, diagnosis_fallback = run_diagnosis_agent(intake, triage, llm_service)
        add_log(
            "Diagnosis Agent",
            "Generated differential diagnosis shortlist.",
            status="completed",
            details=", ".join(item.condition for item in diagnoses),
        )
        if diagnosis_fallback:
            add_notice(_summarize_fallback_reason(diagnosis_fallback))
            add_log(
                "Diagnosis Agent",
                "AI differential unavailable; evidence-based fallback applied.",
                status="fallback",
                details=_summarize_fallback_reason(diagnosis_fallback),
            )

        add_log("Risk Agent", "Calculating weighted clinical risk.", status="processing")
        risk, risk_fallback = run_risk_agent(intake, triage, diagnoses, llm_service)
        add_log(
            "Risk Agent",
            f"Assigned risk score {risk.risk_score}/100 ({risk.risk_level}).",
            status="completed",
            details=risk.justification,
        )
        if risk_fallback:
            add_notice(_summarize_fallback_reason(risk_fallback))
            add_log(
                "Risk Agent",
                "AI risk reasoning unavailable; weighted rules-based score applied.",
                status="fallback",
                details=_summarize_fallback_reason(risk_fallback),
            )

        add_log("Recommendation Agent", "Preparing disposition and next steps.", status="processing")
        recommendation, recommendation_fallback = run_recommendation_agent(intake, triage, diagnoses, risk, llm_service)
        add_log(
            "Recommendation Agent",
            "Generated patient disposition and next-step plan.",
            status="completed",
            details=recommendation.recommended_action,
        )
        if recommendation_fallback:
            add_notice(_summarize_fallback_reason(recommendation_fallback))
            add_log(
                "Recommendation Agent",
                "AI recommendations unavailable; safe fallback guidance applied.",
                status="fallback",
                details=_summarize_fallback_reason(recommendation_fallback),
            )

        add_log("Report Agent", "Assembling structured FHIR report.", status="processing")
        report = build_fhir_report(
            intake,
            triage,
            diagnoses,
            risk,
            recommendation,
            agent_logs,
            system_notices=system_notices,
            ai_fallback_used=ai_fallback_used,
        )
        add_log("Report Agent", "FHIR report completed.", status="completed", details=report.summary)
        return report.model_copy(update={"agentLogs": agent_logs})
    except Exception as exc:
        if isinstance(exc, (ValueError, AgentProcessingError)):
            raise
        logger.exception("Unexpected processing error")
        raise AgentProcessingError("Unable to complete the emergency care workflow.") from exc
