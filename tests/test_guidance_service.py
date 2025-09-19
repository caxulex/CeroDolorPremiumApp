from backend.src.services.guidance_service import next_guided_question


def test_guided_question_anomaly_priority():
    stats = {"anomaly": True, "severity_trend": "up", "delta_last": 3, "last": 8}
    summary = {"mood_hint": "ansioso", "location_keywords": ["espalda"], "triggers": ["correr"]}
    q = next_guided_question(patient_id="p1", asked_categories=[], stats=stats, summary=summary, adherence=80)
    assert q["category"] == "anomaly"
    assert q["priority"] == 1


def test_guided_question_avoids_repetition():
    stats = {"anomaly": False, "severity_trend": "up"}
    q1 = next_guided_question(patient_id="p1", asked_categories=[], stats=stats, summary=None, adherence=80)
    q2 = next_guided_question(patient_id="p1", asked_categories=[str(q1["category"])], stats=stats, summary=None, adherence=80)
    assert q1["category"] != q2["category"]
