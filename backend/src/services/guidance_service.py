"""Adaptive guided question service.

Heuristics-driven selection of the next most informative question for the
patient based on:
- Pain stats (trend, anomaly)
- Transcript summary (mood_hint, sleep_quality, location_keywords, triggers, aggravators, improvement)
- Adherence (simple percentage)
- Already asked categories (avoid repetition)

Return structure (dict):
{
  "question": str,
  "category": str,
  "reason": str,
  "priority": int
}
If no further question is needed, returns {"question": "", "category": "done", "reason": "completed", "priority": 999}.

Design notes:
- Priority: lower number = higher priority.
- Deterministic & side-effect free (pure function) so it's easy to test.
- Categories: anomaly, trend, mood_sleep, location, trigger_followup, adherence, fallback.

Edge cases handled gracefully (None inputs, missing keys).
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence, Set, TypedDict, List

NEG_MOOD = {"deprimido", "triste", "ansioso", "irritable", "estresado", "ansiedad", "depre"}


def _contains_negative_mood(mood_hint: Optional[str]) -> bool:
    if not mood_hint:
        return False
    m = mood_hint.lower()
    return any(tok in m for tok in NEG_MOOD)


class GuidedQuestion(TypedDict):
    question: str
    category: str
    reason: str
    priority: int


def next_guided_question(
    *,
    patient_id: str,
    asked_categories: Iterable[str] | None,
    stats: Optional[Dict],
    summary: Optional[Dict],
    adherence: Optional[float],
    max_questions: int = 5,
) -> GuidedQuestion:
    """Select next guided question.

    Parameters
    ----------
    patient_id: str
        Patient unique id (unused now but future personalization)
    asked_categories: Iterable[str] | None
        Categories already asked in current session (avoid duplicates)
    stats: Optional[Dict]
        Output of _session_pain_stats: may include anomaly, severity_trend, last, delta_last
    summary: Optional[Dict]
        Transcript summary dict.
    adherence: Optional[float]
        Simple adherence % estimate.
    max_questions: int
        Upper bound for total guided questions this run.
    """
    asked: Set[str] = set(asked_categories or [])
    if len(asked) >= max_questions:
        return {"question": "", "category": "done", "reason": "max reached", "priority": 999}

    anomaly = bool(stats.get("anomaly")) if stats else False
    sev_trend = (stats or {}).get("severity_trend") or "flat"
    delta_last = (stats or {}).get("delta_last")
    last_level = (stats or {}).get("last")

    mood_hint = (summary or {}).get("mood_hint")
    sleep_quality = (summary or {}).get("sleep_quality")
    loc_keywords = (summary or {}).get("location_keywords") or []
    triggers = (summary or {}).get("triggers") or []
    aggravators = (summary or {}).get("aggravators") or []
    improvement = (summary or {}).get("improvement")

    # Priority queue construction (lower=better)
    candidates: List[GuidedQuestion] = []

    def add(priority: int, category: str, question: str, reason: str) -> None:  # helper closure
        if category not in asked:
            candidates.append({
                "priority": priority,
                "category": category,
                "question": question,
                "reason": reason,
            })

    # 1. Anomaly follow-up
    if anomaly:
        add(
            1,
            "anomaly",
            "Notamos un cambio marcado en tu dolor. ¿Hubo algo diferente hoy (actividad, estrés, postura)?",
            "Anomalía detectada en la serie de dolor",
        )

    # 2. Upward trend
    if sev_trend == "up":
        add(
            2,
            "trend",
            "Tu dolor ha ido subiendo recientemente. ¿Has modificado ejercicio, medicación o descanso?",
            "Tendencia ascendente reciente",
        )

    # 3. Mood / Sleep influence
    if (sleep_quality in {"bad", "poor"} or _contains_negative_mood(mood_hint)):
        add(
            3,
            "mood_sleep",
            "Parece que el sueño o el ánimo podrían influir. ¿Notas que cuando duermes mejor el dolor cambia?",
            "Indicadores de sueño/ánimo subóptimos",
        )

    # 4. Location deepening
    if loc_keywords:
        loc_list = ", ".join(sorted(set(loc_keywords)))[:80]
        add(
            4,
            "location",
            f"Mencionaste la zona {loc_list}. ¿El dolor se irradia o cambia de lugar durante el día?",
            "Palabras clave de localización en transcripción",
        )

    # 5. Trigger / Aggravators follow-up
    if triggers or aggravators:
        add(
            5,
            "trigger_followup",
            "Comentaste factores que influyen (actividad o postura). ¿Hay algo nuevo que lo alivie o lo empeore?",
            "Se detectaron desencadenantes o agravantes",
        )

    # 6. Adherence low
    if adherence is not None and adherence < 50:
        add(
            6,
            "adherence",
            "Has registrado en pocos días recientes. ¿Hay alguna barrera para seguir las recomendaciones o registrar más a menudo?",
            "Adherencia baja (<50%)",
        )

    # 7. Improvement consolidation
    if (improvement and isinstance(improvement, str)) and delta_last is not None and delta_last < 0:
        add(
            7,
            "improvement",
            "Parece haber una pequeña mejora. ¿Qué crees que ayudó más hoy?",
            "Indicador textual de mejora y delta negativo",
        )

    # 8. Fallback
    add(
        90,
        "fallback",
        "¿Cómo impacta tu dolor en tus actividades diarias más importantes?",
        "Pregunta de contexto funcional general",
    )

    if not candidates:
        return {"question": "", "category": "done", "reason": "no candidates", "priority": 999}

    # Select minimal priority; stable by insertion order
    chosen = min(candidates, key=lambda c: c["priority"])  # stable select
    return chosen


__all__ = ["next_guided_question"]
