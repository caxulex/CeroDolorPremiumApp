import pytest

from backend.src.utils.analytics import compute_pain_stats, integrate_session_events


def test_empty():
    stats = compute_pain_stats([])
    assert stats["count"] == 0
    assert stats["last"] is None


def test_single_value():
    stats = compute_pain_stats([5])
    assert stats["count"] == 1
    assert stats["last"] == 5
    assert stats["delta_last"] is None
    assert stats["anomaly"] is False  # single value shouldn't be anomalous


def test_increasing_trend():
    stats = compute_pain_stats([3, 4, 5])
    assert stats["count"] == 3
    assert stats["last"] == 5
    assert stats["severity_trend"] == "up"
    assert stats["delta_last"] == 1


def test_large_jump_anomaly():
    stats = compute_pain_stats([2, 2, 2, 8])
    assert stats["last"] == 8
    assert stats["anomaly"] is True  # large absolute jump


def test_zscore_anomaly():
    # create distribution then outlier
    base = [5] * 10
    seq = base + [10]
    stats = compute_pain_stats(seq)
    assert stats["last"] == 10
    assert stats["anomaly"] is True
    assert stats["zscore_last"] is not None


def test_pct_change():
    stats = compute_pain_stats([4, 5])
    assert stats["pct_change_last"] == 25.0  # (1 / 4) * 100


def test_rolling_means_and_delta():
    seq = [3, 4, 5, 6]
    stats = compute_pain_stats(seq)
    assert stats["mean_last_3"] == pytest.approx((4 + 5 + 6) / 3)
    assert stats["mean_last_7"] == pytest.approx(sum(seq) / len(seq))
    assert stats["delta_last"] == 1
    assert stats["anomaly"] is False


def test_trend_flat():
    stats = compute_pain_stats([4, 4, 4])
    assert stats["severity_trend"] == "flat"


def test_trend_down():
    stats = compute_pain_stats([6, 5, 4])
    assert stats["severity_trend"] == "down"


def test_integrate_session_events():
    events = [
        {"type": "noise"},
        {"type": "pain_registration", "data": {"pain": {"level": 4}}},
        {"type": "pain_registration", "data": {"pain": {"level": 6}}},
    ]
    out = integrate_session_events(events)
    assert out["pain"]["count"] == 2
    assert out["pain"]["last"] == 6
