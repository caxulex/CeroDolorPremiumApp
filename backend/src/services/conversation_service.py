"""Conversation processing utilities.

Provides summarization of raw transcript text into structured fields:
- pain_location
- perceived_severity (low|moderate|high)
- trigger (short phrase or None)
- sleep_quality (good|regular|bad|unknown)
- mood_hint (positive|neutral|negative|unknown)
Deterministic heuristic implementation (regex & keyword maps) to stay offline-first.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Dict, Any

_LOCATION_WORDS = {
    "espalda": "espalda",
    "lumbar": "lumbar",
    "cabeza": "cabeza",
    "rodilla": "rodilla",
    "cuello": "cuello",
    "hombro": "hombro",
    "pierna": "pierna",
}

_SEVERITY_MAP = {
    "leve": "low",
    "ligero": "low",
    "moderado": "moderate",
    "media": "moderate",
    "fuerte": "high",
    "intenso": "high",
    "severo": "high",
    "alto": "high",
}

_SLEEP_MAP = {
    "bien": "good",
    "bueno": "good",
    "mal": "bad",
    "malo": "bad",
    "regular": "regular",
    "fatal": "bad",
}

_MOOD_POS = {"feliz", "tranquilo", "motivado", "contento", "bien"}
_MOOD_NEG = {"triste", "ansioso", "estresado", "deprimido", "irritable"}

_TRIGGER_PATTERNS = [
    re.compile(r"despues de ([a-záéíóúñ ]{3,40})"),
    re.compile(r"tras ([a-záéíóúñ ]{3,40})"),
    re.compile(r"al (?:hacer|levantar|subir) ([a-záéíóúñ ]{3,40})"),
]

@dataclass
class TranscriptSummary:
    pain_location: str | None
    perceived_severity: str | None
    trigger: str | None
    sleep_quality: str | None
    mood_hint: str | None
    raw_char_len: int

    def to_dict(self) -> Dict[str, Any]:  # pragma: no cover - trivial
        return asdict(self)

def _find_location(text: str) -> str | None:
    for k,v in _LOCATION_WORDS.items():
        if k in text:
            return v
    return None

def _find_severity(text: str) -> str | None:
    for k,v in _SEVERITY_MAP.items():
        if k in text:
            return v
    return None

def _find_sleep(text: str) -> str | None:
    for k,v in _SLEEP_MAP.items():
        if k in text:
            return v
    return None

def _find_mood(text: str) -> str | None:
    words = set(re.findall(r"[a-záéíóúñ]+", text))
    if words & _MOOD_POS:
        return "positive"
    if words & _MOOD_NEG:
        return "negative"
    return None

def _find_trigger(text: str) -> str | None:
    for pat in _TRIGGER_PATTERNS:
        m = pat.search(text)
        if m:
            frag = m.group(1).strip()
            return frag[:60]
    return None

def summarize_transcript(text: str) -> TranscriptSummary:
    t = text.lower()
    loc = _find_location(t)
    sev = _find_severity(t)
    trig = _find_trigger(t)
    slp = _find_sleep(t)
    mood = _find_mood(t)
    return TranscriptSummary(
        pain_location=loc,
        perceived_severity=sev,
        trigger=trig,
        sleep_quality=slp,
        mood_hint=mood,
        raw_char_len=len(text),
    )

__all__ = ["TranscriptSummary", "summarize_transcript"]
