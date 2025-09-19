from typing import Any

from pydantic import BaseModel, Field, conint, field_validator


class Envelope(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class CheckinRequest(BaseModel):
    patient_id: str
    pain_level: conint(ge=1, le=10)
    description: str
    transcript: str | None = None
    mood: str | None = None
    sleep: str | None = None
    use_tts: bool = False

    MAX_DESC_LEN = 5000

    @field_validator("description", "transcript")
    def limit_len(self, v: str | None) -> str | None:
        if v and len(v) > CheckinRequest.MAX_DESC_LEN:
            return v[: CheckinRequest.MAX_DESC_LEN]
        return v


class ClinicianRequest(BaseModel):
    patient_id: str
    clinician_id: str
    scope: str = "last_30_days"
    require_blockchain_anchor: bool = False


class ResearcherRequest(BaseModel):
    study_id: str
    criteria: dict[str, Any] = Field(default_factory=dict)
    anonymization_level: str = "safe-default"
    require_blockchain_anchor: bool = False
