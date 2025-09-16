from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass(frozen=True)
class McpToolPaths:
    base_url: str
    aip_to_asd_path: str
    asd_to_aiper_path: str
    patient_to_clinician_path: str | None = None
    clinician_to_physio_path: str | None = None
    physio_to_patient_path: str | None = None

    def aip_to_asd_url(self) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", self.aip_to_asd_path.lstrip("/"))

    def asd_to_aiper_url(self) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", self.asd_to_aiper_path.lstrip("/"))

    def patient_to_clinician_url(self) -> str | None:
        return (
            urljoin(self.base_url.rstrip("/") + "/", self.patient_to_clinician_path.lstrip("/"))
            if self.patient_to_clinician_path
            else None
        )

    def clinician_to_physio_url(self) -> str | None:
        return (
            urljoin(self.base_url.rstrip("/") + "/", self.clinician_to_physio_path.lstrip("/"))
            if self.clinician_to_physio_path
            else None
        )

    def physio_to_patient_url(self) -> str | None:
        return (
            urljoin(self.base_url.rstrip("/") + "/", self.physio_to_patient_path.lstrip("/"))
            if self.physio_to_patient_path
            else None
        )


def resolve_tool_paths(
    base_url: str | None = None,
    *,
    default_base: str = "http://localhost:3000",
    default_aip_to_asd_path: str = "/echo",
    default_asd_to_aiper_path: str = "/echo",
) -> McpToolPaths:
    """Resolve MCP tool endpoint paths.

    Values can be overridden using environment variables:
      - MCP_BASE_URL
      - MCP_TOOL_AIP_TO_ASD_PATH
      - MCP_TOOL_ASD_TO_AIPER_PATH

    Defaults intentionally point to an echo endpoint to avoid
    accidental coupling to a specific server during early iterations.
    """
    base = base_url or os.getenv("MCP_BASE_URL") or default_base
    aip_to_asd = os.getenv("MCP_TOOL_AIP_TO_ASD_PATH", default_aip_to_asd_path)
    asd_to_aiper = os.getenv("MCP_TOOL_ASD_TO_AIPER_PATH", default_asd_to_aiper_path)

    # Optional MAS endpoints; default to echo to avoid tight coupling
    p2c = os.getenv("MCP_TOOL_PATIENT_TO_CLINICIAN_PATH")
    c2p = os.getenv("MCP_TOOL_CLINICIAN_TO_PHYSIO_PATH")
    p2p = os.getenv("MCP_TOOL_PHYSIO_TO_PATIENT_PATH")

    return McpToolPaths(
        base_url=base,
        aip_to_asd_path=aip_to_asd,
        asd_to_aiper_path=asd_to_aiper,
        patient_to_clinician_path=p2c or default_aip_to_asd_path,
        clinician_to_physio_path=c2p or default_aip_to_asd_path,
        physio_to_patient_path=p2p or default_aip_to_asd_path,
    )
