"""End-to-end backend flow: text -> analysis -> suggestion -> optional TTS.

Runs entirely locally with placeholders unless env vars are set.
Outputs JSON summary and optional audio file path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.services.aip_service import register_mood_sleep, register_pain, tts_speak
from src.services.aiper_service import generate_intervention
from src.services.asd_service import analyze_data


def run_e2e(patient_id: str, pain_level: int, pain_desc: str, mood: str, sleep: str) -> dict[str, Any]:
    pain = register_pain(patient_id, pain_level, pain_desc)
    ms = register_mood_sleep(patient_id, mood, sleep)
    insights = analyze_data(patient_id, {"pain": pain, "mood_sleep": ms})
    suggestion = generate_intervention(patient_id)

    audio_file = None
    if os.getenv("ELEVENLABS_API_KEY"):
        audio = tts_speak(f"Sugerencia: {suggestion}")
        if audio:
            out = Path(__file__).resolve().parent / "e2e_suggestion.wav"
            out.write_bytes(audio)
            audio_file = str(out)

    return {
        "patient_id": patient_id,
        "pain": pain,
        "mood_sleep": ms,
        "insights": insights,
        "suggestion": suggestion,
        "audio_file": audio_file,
    }


def main() -> None:
    # Simple defaults suitable for demo
    data = run_e2e("demo_patient", 6, "punzante", "ansioso", "mal")
    print(json.dumps(data, ensure_ascii=False, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
