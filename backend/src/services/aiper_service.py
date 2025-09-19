import os
from typing import Any, Dict, Optional, TypedDict, Union


class Intervention(TypedDict):
    suggestion: str
    intervention_type: str
    details: Dict[str, Any]


StatsDict = Dict[str, Any]
MoodSleepDict = Dict[str, Any]


def _last_pain_stats(pid: str) -> StatsDict:
    """Lightweight extraction of recent pain stats from persistence store.

    Returns keys: last, prev, delta, mean3, anomaly(bool), count, severity_trend
    (Graceful fallbacks if store not available.)
    """
    try:  # local import to avoid circular issues in tests without persistence
        from backend.src.utils.persistence import store  # type: ignore
    except Exception:  # noqa: BLE001
        store = None  # type: ignore
    if not store:
        return {}
    try:
        sess = store.get(pid)
    except Exception:  # noqa: BLE001
        return {}
    pains = []
    for ev in sess.events:  # type: ignore[attr-defined]
        if ev.get("type") == "pain_registration":
            data = (ev.get("data") or {}).get("pain") if isinstance(ev.get("data"), dict) else None
            if isinstance(data, dict):
                lvl = data.get("level") or data.get("pain_level") or data.get("value")
                if isinstance(lvl, (int, float)):
                    pains.append(int(lvl))
    if not pains:
        return {}
    last = pains[-1]
    prev = pains[-2] if len(pains) > 1 else last
    delta = last - prev
    mean3 = sum(pains[-3:]) / min(len(pains), 3)
    anomaly = abs(delta) >= 3
    if len(pains) >= 3:
        seq = pains[-3:]
        if seq[0] < seq[1] < seq[2]:
            trend = "up"
        elif seq[0] > seq[1] > seq[2]:
            trend = "down"
        else:
            trend = "flat"
    else:
        trend = "flat"
    return {
        "last": last,
        "prev": prev,
        "delta": delta,
        "mean3": round(mean3, 2),
        "anomaly": anomaly,
        "count": len(pains),
        "severity_trend": trend,
    }


def _recent_mood_sleep(pid: str) -> MoodSleepDict:
    try:
        from backend.src.utils.persistence import store  # type: ignore
    except Exception:  # noqa: BLE001
        store = None  # type: ignore
    if not store:
        return {}
    try:
        sess = store.get(pid)
    except Exception:  # noqa: BLE001
        return {}
    for ev in reversed(sess.events):  # type: ignore[attr-defined]
        if ev.get("type") == "mood_sleep":
            ms = (ev.get("data") or {}).get("mood_sleep") if isinstance(ev.get("data"), dict) else None
            if isinstance(ms, dict):
                return ms
    return {}


def _choose_local_heuristic(pid: str) -> Intervention:
    stats = _last_pain_stats(pid)
    ms = _recent_mood_sleep(pid)
    pain_level = stats.get("last")
    delta = stats.get("delta")
    anomaly = stats.get("anomaly")
    trend = stats.get("severity_trend")
    mood = (ms.get("mood") or "").lower() if isinstance(ms.get("mood"), str) else ""
    sleep = (ms.get("sleep") or "").lower() if isinstance(ms.get("sleep"), str) else ""

    # Heuristic priority order
    rationale = []
    if anomaly or (isinstance(pain_level, int) and pain_level >= 7):
        suggestion = "Realiza 5 minutos de respiración diafragmática lenta (4-2-6) en posición cómoda."
        return {
            "suggestion": suggestion,
            "intervention_type": "breathing",
            "details": {"duration_min": 5, "rationale": "Dolor alto o cambio brusco"},
        }
    if trend == "up" and isinstance(pain_level, int) and pain_level <= 7:
        return {
            "suggestion": "Haz 6-8 minutos de movilidad suave de columna y caderas (sin dolor agudo).",
            "intervention_type": "movement",
            "details": {"duration_min": 8, "rationale": "Tendencia ascendente leve/moderada"},
        }
    if any(x in mood for x in ["depri", "trist", "ans", "estrés", "estres", "irrita"]):
        return {
            "suggestion": "Toma 3 minutos para un escaneo corporal breve y anota una cosa positiva de hoy.",
            "intervention_type": "mindfulness",
            "details": {"duration_min": 3, "rationale": "Ánimo bajo detectado"},
        }
    if "mal" in sleep or "pobre" in sleep:
        return {
            "suggestion": "Prueba higiene de sueño: evita pantallas brillantes 30 min antes de dormir hoy.",
            "intervention_type": "education",
            "details": {"topic": "sleep_hygiene", "rationale": "Sueño deficiente reciente"},
        }
    if isinstance(delta, int) and delta < 0:
        return {
            "suggestion": "Refuerza lo que ayudó hoy: repite la actividad que alivió (manteniendo intensidad moderada).",
            "intervention_type": "reinforcement",
            "details": {"rationale": "Mejora reciente (delta negativo)"},
        }
    # General fallback
    return {
        "suggestion": "Haz una pausa breve: 2 minutos de respiración nasal + estiramiento suave de cuello y hombros.",
        "intervention_type": "mixed",
        "details": {"rationale": "Fallback genérico"},
    }


def _suggest_with_mistral(patient_id: str) -> Optional[str]:
    suggestion: str | None = None
    use_adapters = os.getenv("USE_ADAPTERS", "false").lower() == "true"
    if use_adapters:
        try:
            from integrations.mistral import MistralClient, MistralConfig  # type: ignore[import-not-found]  # noqa: I001
            client = MistralClient(MistralConfig(api_key=os.getenv("MISTRAL_API_KEY")))  # type: ignore[misc]
            msg = (
                "Eres un coach de empatía para dolor crónico. Sugiere una intervención breve, segura y práctica "
                f"para el paciente {patient_id}. Responde en 1 frase."
            )
            resp = client.chat([{"role": "user", "content": msg}])
            choice = (resp.get("choices", [{}]) or [{}])[0]
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, str):
                suggestion = content.strip()
        except Exception:  # noqa: BLE001
            suggestion = None

    if suggestion is None:
        use_mistral = os.getenv("USE_MISTRAL")
        api_key = os.getenv("MISTRAL_API_KEY")
        if use_mistral and api_key:
            try:
                from mistralai import Mistral  # type: ignore[import-not-found]
                client = Mistral(api_key=api_key)
                prompt = (
                    "Eres un coach de empatía para dolor crónico. Sugiere una intervención breve, "
                    f"segura y práctica para el paciente {patient_id}. Responde en 1 frase."
                )
                resp = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}],
                )
                content2 = (
                    getattr(resp.choices[0].message, "content", None)
                    if getattr(resp, "choices", None)
                    else None
                )
                if content2 and isinstance(content2, str):
                    suggestion = content2.strip()
            except Exception:  # noqa: BLE001
                suggestion = None

    return suggestion


def generate_intervention(patient_id: str) -> Intervention:
    """Return structured multi-modal intervention suggestion.

    Structure: {suggestion:str, intervention_type:str, details:dict}
    Falls back to local heuristic if no model suggestion.
    """
    model_suggestion = _suggest_with_mistral(patient_id)
    if model_suggestion:
        # Wrap model output as generic coaching text
        return {
            "suggestion": model_suggestion,
            "intervention_type": "llm_suggestion",
            "details": {"source": "mistral|adapter"},
        }
    return _choose_local_heuristic(patient_id)
