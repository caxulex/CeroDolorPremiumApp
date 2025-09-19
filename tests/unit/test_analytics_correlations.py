from backend.src.utils.analytics import compute_correlations, weekly_aggregate


def _mk_event(e_type, **data):
    ev = {"type": e_type, "id": 0, "ts": "2025-09-16T12:00:00Z", "data": {}}
    if e_type == "pain_registration":
        ev["data"] = {"pain": {"level": data.get("level", 5)}}
    elif e_type == "mood_sleep":
        ev["data"] = {"mood_sleep": {"mood": data.get("mood", "neutral"), "sleep": data.get("sleep", "normal")}}
    return ev


def test_correlations_basic_alignment():
    events = [
        _mk_event("mood_sleep", mood="triste", sleep="mal"),
        _mk_event("pain_registration", level=8),
        _mk_event("mood_sleep", mood="neutral", sleep="normal"),
        _mk_event("pain_registration", level=5),
        _mk_event("mood_sleep", mood="feliz", sleep="excelente"),
        _mk_event("pain_registration", level=2),
    ]
    corr = compute_correlations(events)
    assert corr["count"] == 3
    # Should produce numeric correlations (may be positive or negative depending on mapping)
    assert corr["pain_vs_mood"] is not None
    assert corr["pain_vs_sleep"] is not None


def test_correlations_insufficient():
    # fewer than 3 pain points -> None correlations
    events = [
        _mk_event("pain_registration", level=5),
        _mk_event("pain_registration", level=6),
    ]
    corr = compute_correlations(events)
    assert corr["count"] == 2
    assert corr["pain_vs_mood"] is None
    assert corr["pain_vs_sleep"] is None


def test_weekly_aggregate_multiple_weeks():
    events = [
        {"type": "pain_registration", "ts": "2025-09-15T10:00:00Z", "data": {"pain": {"level": 5}}},  # week 38
        {"type": "pain_registration", "ts": "2025-09-16T10:00:00Z", "data": {"pain": {"level": 7}}},  # week 38
        {"type": "pain_registration", "ts": "2025-09-23T10:00:00Z", "data": {"pain": {"level": 3}}},  # week 39
    ]
    wk = weekly_aggregate(events)
    keys = sorted(wk.keys())
    assert len(keys) == 2
    # Check averages
    w1 = [v for k, v in wk.items() if k.endswith("W38") or k.endswith("-W38")]
    w2 = [v for k, v in wk.items() if k.endswith("W39") or k.endswith("-W39")]
    assert w1 and w1[0]["avg"] == 6.0
    assert w2 and w2[0]["avg"] == 3.0
