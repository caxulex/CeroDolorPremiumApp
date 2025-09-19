from backend.src.utils.analytics import (
    bootstrap_correlation_ci,
    build_analytics_snapshot,
    cross_feature_anomalies,
    weekly_trends,
)


def test_weekly_trends_delta():
    weekly = {
        "2025-W38": {"count": 2, "avg": 5.0, "min": 5, "max": 5},
        "2025-W39": {"count": 1, "avg": 7.0, "min": 7, "max": 7},
    }
    wt = weekly_trends(weekly)
    assert wt["2025-W38"]["delta_vs_prev"] is None
    assert wt["2025-W39"]["delta_vs_prev"] == 2.0


def test_bootstrap_ci_deterministic():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]
    ci1 = bootstrap_correlation_ci(xs, ys, n_boot=100, seed=42)
    ci2 = bootstrap_correlation_ci(xs, ys, n_boot=100, seed=42)
    assert ci1 is not None and ci2 is not None
    assert ci1 == ci2
    assert ci1["r"] <= 1.0 and ci1["r"] >= 0.9  # strong positive


def _mk_ev(t, ts, **data):
    return {"type": t, "ts": ts, "data": data}


def test_cross_feature_anomalies():
    events = [
        _mk_ev("mood_sleep", "2025-09-16T10:00:00Z", mood_sleep={"mood": "ansioso", "sleep": "mal"}),
        _mk_ev("pain_registration", "2025-09-16T10:05:00Z", pain={"level": 3}),
        _mk_ev("pain_registration", "2025-09-16T10:10:00Z", pain={"level": 8}),  # high pain + poor context
        _mk_ev("pain_registration", "2025-09-16T10:15:00Z", pain={"level": 9}),  # jump 1 (not >=4) but still high pain + poor
        _mk_ev("mood_sleep", "2025-09-16T10:20:00Z", mood_sleep={"mood": "triste", "sleep": "terrible"}),
        _mk_ev("pain_registration", "2025-09-16T10:25:00Z", pain={"level": 9}),
        _mk_ev("pain_registration", "2025-09-16T10:30:00Z", pain={"level": 4}),  # drop (no anomaly)
        _mk_ev("pain_registration", "2025-09-16T10:40:00Z", pain={"level": 9}),  # jump 5 -> sudden_jump_with_context
    ]
    anomalies = cross_feature_anomalies(events)
    tags = {tuple(a["tags"]) for a in anomalies}
    # Expect at least one composite high pain and at least one sudden jump
    found_high = any("high_pain_with_poor_recovery" in a["tags"] for a in anomalies)
    found_jump = any("sudden_jump_with_context" in a["tags"] for a in anomalies)
    assert found_high and found_jump


def test_build_snapshot_keys():
    events = [
        _mk_ev("mood_sleep", "2025-09-16T10:00:00Z", mood_sleep={"mood": "ansioso", "sleep": "mal"}),
        _mk_ev("pain_registration", "2025-09-16T10:05:00Z", pain={"level": 5}),
        _mk_ev("pain_registration", "2025-09-16T10:06:00Z", pain={"level": 9}),
    ]
    snap = build_analytics_snapshot(events)
    for key in ("pain", "weekly", "correlations", "anomalies"):
        assert key in snap
    assert isinstance(snap["weekly"], dict)
