import asyncio
from typing import Any

from backend.orchestrator_api.logging_utils import get_logger

logger = get_logger(__name__)

_DB: dict[str, dict[str, Any]] = {}


async def _ensure_patient(pid: str) -> dict[str, Any]:
    await asyncio.sleep(0)
    if pid not in _DB:
        _DB[pid] = {"events": []}
    return _DB[pid]


async def save_event(pid: str, event_type: str, data: dict[str, Any]) -> None:
    sess = await _ensure_patient(pid)
    sess["events"].append({"type": event_type, "data": data})
    logger.info("saved event type=%s", event_type)


async def get_recent_data(pid: str, _scope: str = "last_30_days") -> dict[str, Any]:
    sess = await _ensure_patient(pid)
    return {"events": list(sess["events"])}


async def query_cohort(criteria: dict[str, Any]) -> list[dict[str, Any]]:
    pid = criteria.get("patient_id")
    if pid and pid in _DB:
        return [{"patient_id": pid, "events": list(_DB[pid]["events"])}]
    return [{"patient_id": k, "events": list(v["events"])} for k, v in _DB.items()]
