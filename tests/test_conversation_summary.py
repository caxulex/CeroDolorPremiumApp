from backend.src.services.conversation_service import summarize_transcript


def test_summarize_transcript_deterministic():
    text = "Tengo dolor moderado en la espalda baja, peor al levantarme. Dormí mal y me siento ansioso."
    s1 = summarize_transcript(text).to_dict()
    s2 = summarize_transcript(text).to_dict()
    assert s1 == s2
    # Key expectations
    assert "location_keywords" in s1
    assert "sleep_quality" in s1
    assert s1.get("mood_hint") in {"ansioso", "ansiedad", None}
