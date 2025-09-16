from __future__ import annotations

from backend.src.mcp.mapping import resolve_tool_paths
from backend.src.mcp.validation import validate_aip_to_asd, validate_asd_to_aiper


def test_resolve_tool_paths_defaults():
    paths = resolve_tool_paths()
    assert paths.base_url.startswith("http")
    assert paths.aip_to_asd_path
    assert paths.asd_to_aiper_path
    # url join sanity
    assert paths.aip_to_asd_url().startswith(paths.base_url)
    assert paths.asd_to_aiper_url().startswith(paths.base_url)


def test_resolve_tool_paths_env_override(monkeypatch):
    monkeypatch.setenv("MCP_BASE_URL", "http://example.local:9999")
    monkeypatch.setenv("MCP_TOOL_AIP_TO_ASD_PATH", "/aip-asd")
    monkeypatch.setenv("MCP_TOOL_ASD_TO_AIPER_PATH", "/asd-aiper")
    paths = resolve_tool_paths()
    assert paths.base_url == "http://example.local:9999"
    assert paths.aip_to_asd_url().endswith("/aip-asd")
    assert paths.asd_to_aiper_url().endswith("/asd-aiper")


def test_validate_aip_to_asd_happy():
    errs = validate_aip_to_asd(
        {
            "message_type": "pain_submission",
            "patient_id": "p1",
            "timestamp": "2025-09-15T10:00:00Z",
            "pain_data": {"level": 5, "description": "dolor", "mood": "ok", "sleep_quality": "ok"},
        }
    )
    assert errs == []


def test_validate_asd_to_aiper_happy():
    errs = validate_asd_to_aiper(
        {
            "message_type": "insights",
            "patient_id": "p1",
            "timestamp": "2025-09-15T10:00:00Z",
            "insights": {"patterns_detected": ["p"], "trend_analysis": "t", "risk_flags": []},
        }
    )
    assert errs == []


def test_validate_contracts_errors():
    assert validate_aip_to_asd({"foo": "bar"})  # not empty -> has errors
    assert validate_asd_to_aiper({"foo": "bar"})
