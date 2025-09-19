from typing import Any

from backend.orchestrator_api.agents.investigator import InvestigatorAgent
from backend.orchestrator_api.agents.patient_interface import PatientInterfaceAgent
from backend.orchestrator_api.agents.personalized_intervention import (
    PersonalizedInterventionAgent,
)
from backend.orchestrator_api.config import settings
from backend.orchestrator_api.logging_utils import get_logger
from backend.orchestrator_api.models import CheckinRequest
from backend.orchestrator_api.services.db import save_event
from backend.orchestrator_api.services.elevenlabs_client import ElevenLabsClient
from backend.orchestrator_api.services.mistral_client import MistralClient

logger = get_logger(__name__)


async def run_checkin_flow(req: CheckinRequest, *, mistral: MistralClient | None = None, tts: ElevenLabsClient | None = None) -> dict[str, Any]:
    mistral = mistral or MistralClient()
    tts = tts or ElevenLabsClient()

    # Save initial event
    await save_event(req.patient_id, "checkin_received", req.model_dump())

    investigator = InvestigatorAgent(mistral, settings.agent_investigator_id or "investigator")
    patient_ui = PatientInterfaceAgent(mistral, settings.agent_patient_interface_id or "patient_ui")
    intervention = PersonalizedInterventionAgent(mistral, settings.agent_personalized_intervention_id or "intervention")

    # 1) Investigator analyzes input
    inv_payload = {
        "input": f"Pain level: {req.pain_level}. Description: {req.description}. Transcript: {req.transcript or ''}. Mood: {req.mood or ''}. Sleep: {req.sleep or ''}",
        "response_format": {"type": "json_object"},
    }
    inv_res = await investigator.invoke(inv_payload)

    # 2) Patient interface generates empathetic message
    ui_payload = {
        "input": f"Provide empathetic guidance for pain level {req.pain_level} based on analysis: {inv_res}",
        "response_format": {"type": "text"},
    }
    ui_res = await patient_ui.invoke(ui_payload)

    # 3) Personalized intervention
    int_payload = {
        "input": f"Create a short, actionable intervention for pain level {req.pain_level}, context: {inv_res}",
        "response_format": {"type": "json_object"},
    }
    int_res = await intervention.invoke(int_payload)

    # Persist summary event
    summary = {"analysis": inv_res, "message": ui_res, "intervention": int_res}
    await save_event(req.patient_id, "checkin_processed", summary)

    audio_b64: str | None = None
    if req.use_tts:
        text = str(ui_res)
        audio_b64 = await tts.synthesize(text)

    return {"summary": summary, "audio_b64": audio_b64}
