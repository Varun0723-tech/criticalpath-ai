from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from backend.controller import process_patient
from backend.models.exceptions import AgentProcessingError, InputValidationError
from backend.models.schemas import PatientInput, PatientReport

router = APIRouter(tags=["triage"])
logger = logging.getLogger(__name__)


@router.post("/triage", response_model=PatientReport)
async def triage_patient(payload: PatientInput) -> PatientReport:
    try:
        return process_patient(payload)
    except InputValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AgentProcessingError as exc:
        logger.exception("Workflow processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

