from typing import Any


async def has_clinician_consent(_patient_id: str, _clinician_id: str, _scope: str) -> bool:
    return True


async def has_research_consent(criteria: dict[str, Any]) -> bool:
    return bool(criteria.get("consent", True))
