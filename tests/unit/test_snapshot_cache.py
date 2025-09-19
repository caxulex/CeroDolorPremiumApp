from backend.src.utils.snapshot_cache import clear_snapshot_cache, compute_or_get_snapshot


def _make_events(n=3):
    evs = []
    for i in range(1, n+1):
        evs.append({
            "id": i,
            "type": "pain_registration",
            "data": {"pain": {"pain_level": i+1}},
            "ts": f"2025-09-17T00:00:0{i}Z",
        })
    return evs


def test_cache_miss_then_hit():
    clear_snapshot_cache()
    events = _make_events(4)
    snap1 = compute_or_get_snapshot(events, "p1")
    assert snap1.get("_cache_hit") is False
    snap2 = compute_or_get_snapshot(list(events), "p1")
    assert snap2.get("_cache_hit") is True
    # Modify events -> should miss again
    events.append({
        "id": 999,
        "type": "pain_registration",
        "data": {"pain": {"pain_level": 9}},
        "ts": "2025-09-17T00:00:59Z",
    })
    snap3 = compute_or_get_snapshot(events, "p1")
    assert snap3.get("_cache_hit") is False
