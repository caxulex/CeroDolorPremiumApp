import json as _json
import os
from typing import Any


def _analyze_with_mistral(patient_id: str, data: dict) -> dict[str, Any] | None:
    """Try to analyze using Mistral AI if API key is available; else None.

    No network calls will occur without MISTRAL_API_KEY.
    """
    result: dict[str, Any] | None = None
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    if use_adapters:
        try:
            from integrations.mistral import MistralClient, MistralConfig  # type: ignore[import-not-found]  # noqa: I001

            client = MistralClient(MistralConfig(api_key=os.getenv("MISTRAL_API_KEY")))  # type: ignore[misc]
            text = (
                "Resumir patrones y banderas de riesgo desde datos de paciente. "
                f"ID: {patient_id}. Datos: {data}."
            )
            extracted = client.extract(text)
            result = {
                "patterns_detected": extracted.get("triggers", []),
                "trend_analysis": "stable",
                "risk_flags": [],
            }
        except Exception:  # noqa: BLE001
            result = None

    if result is None and os.getenv("USE_MISTRAL") and os.getenv("MISTRAL_API_KEY"):
            try:
                # Lazy import to avoid hard dependency and allow tests without network
                from mistralai import Mistral  # type: ignore[import-not-found]
                client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
                prompt = (
                    "Eres un asistente de análisis de dolor crónico. Resume patrones, tendencias, "
                    "y posibles banderas de riesgo a partir del siguiente JSON de datos del paciente. "
                    f"ID paciente: {patient_id}. JSON: {data}. Responde en JSON con las claves: "
                    "patterns_detected (lista), trend_analysis (string), risk_flags (lista)."
                )
                resp = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}],
                )
                content = (
                    getattr(resp.choices[0].message, "content", "{}")
                    if getattr(resp, "choices", None)
                    else "{}"
                )
                parsed = _json.loads(content)
                if isinstance(parsed, dict):
                    result = {
                        "patterns_detected": parsed.get("patterns_detected", []),
                        "trend_analysis": parsed.get("trend_analysis", "stable"),
                        "risk_flags": parsed.get("risk_flags", []),
                    }
            except Exception:  # noqa: BLE001
                result = None

    return result


def analyze_data(patient_id: str, data: dict) -> dict:
    # Prefer Mistral if available; otherwise fallback deterministic placeholder
    analyzed = _analyze_with_mistral(patient_id, data)
    if analyzed is not None:
        return analyzed
    _ = (patient_id, data)
    return {
        "patterns_detected": ["placeholder"],
        "trend_analysis": "stable",
        "risk_flags": [],
    }
