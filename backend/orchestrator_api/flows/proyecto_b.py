from typing import Any

from backend.orchestrator_api.agents.clinician import ClinicianAgent
from backend.orchestrator_api.agents.clinician_report import ClinicianReportAgent
from backend.orchestrator_api.agents.data_synthesis import DataSynthesisAgent
from backend.orchestrator_api.agents.investigator import InvestigatorAgent
from backend.orchestrator_api.config import settings
from backend.orchestrator_api.logging_utils import get_logger
from backend.orchestrator_api.models import ClinicianRequest, ResearcherRequest
from backend.orchestrator_api.services.anonymization import anonymize_sessions
from backend.orchestrator_api.services.consent import (
    has_clinician_consent,
    has_research_consent,
)
from backend.orchestrator_api.services.db import get_recent_data, query_cohort
from backend.orchestrator_api.services.mistral_client import MistralClient
from backend.orchestrator_api.services.solana_client import SolanaService

logger = get_logger(__name__)


async def run_clinician_flow(req: ClinicianRequest, *, mistral: MistralClient | None = None, solana: SolanaService | None = None) -> dict[str, Any]:
    mistral = mistral or MistralClient()
    solana = solana or SolanaService()

    if not await has_clinician_consent(req.patient_id, req.clinician_id, req.scope):
        return {"error": "no_consent"}

    inv = InvestigatorAgent(mistral, settings.agent_investigator_id or "investigator")
    clin = ClinicianAgent(mistral, settings.agent_clinician_id or "clinician")
    report = ClinicianReportAgent(mistral, settings.agent_clinician_report_id or "clinician_report")

    # fetch data and analyze
    data = await get_recent_data(req.patient_id, req.scope)
    inv_res = await inv.invoke({"input": f"Analyze patient data and summarize risks: {data}", "response_format": {"type": "json_object"}})
    clin_res = await clin.invoke({"input": f"Draft clinician guidance based on analysis: {inv_res}", "response_format": {"type": "text"}})
    report_res = await report.invoke({"input": f"Produce a concise structured report with recommendations from: {clin_res}", "response_format": {"type": "json_object"}})

    anchor_tx: str | None = None
    if req.require_blockchain_anchor:
        payload_hash = hex(abs(hash(str(report_res))))
        anchor_tx = await solana.anchor_hash(payload_hash)

    return {"analysis": inv_res, "guidance": clin_res, "report": report_res, "anchor_tx": anchor_tx}


async def run_researcher_flow(req: ResearcherRequest, *, mistral: MistralClient | None = None, solana: SolanaService | None = None) -> dict[str, Any]:
    mistral = mistral or MistralClient()
    solana = solana or SolanaService()

    if not await has_research_consent(req.criteria):
        return {"error": "no_consent"}

    ds = DataSynthesisAgent(mistral, settings.agent_data_synthesis_id or "data_synthesis")

    cohort = await query_cohort(req.criteria)
    anon: list[dict[str, Any]] = anonymize_sessions(cohort, req.anonymization_level)
    synthesis = await ds.invoke({"input": f"Synthesize insights across cohort: {anon}", "response_format": {"type": "json_object"}})

    anchor_tx: str | None = None
    if req.require_blockchain_anchor:
        payload_hash = hex(abs(hash(str(synthesis))))
        anchor_tx = await solana.anchor_hash(payload_hash)

    return {"cohort_size": len(anon), "synthesis": synthesis, "anchor_tx": anchor_tx}
