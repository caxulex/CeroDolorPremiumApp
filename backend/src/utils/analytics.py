"""Lightweight analytics enrichment utilities.

Provides:
 - bootstrap_ci_mean: non-parametric CI for mean
 - correlation_pearson: simple Pearson r (manual, minimal deps)
 - bootstrap_ci_correlation: CI for correlation (paired resampling)
 - build_session_enrichment: produce enriched analytics snapshot for a patient

Design constraints:
 - No heavy numeric libs (pure Python) to keep offline footprint low
 - Small sample guard: returns None for CI if <4 samples
 - Deterministic seeding optional (seed parameter)
"""
from __future__ import annotations

from math import sqrt
from random import Random
from typing import Dict, List, Optional, Sequence, Tuple


def bootstrap_ci_mean(samples: Sequence[float], *, iters: int = 400, alpha: float = 0.05, seed: int | None = None) -> Tuple[float, float] | None:
    n = len(samples)
    if n < 4:
        return None
    rnd = Random(seed)
    means: List[float] = []
    for _ in range(iters):
        b = [samples[rnd.randrange(0, n)] for _ in range(n)]
        means.append(sum(b) / n)
    means.sort()
    lo_idx = int((alpha / 2) * iters)
    hi_idx = int((1 - alpha / 2) * iters) - 1
    lo_idx = max(0, min(lo_idx, iters - 1))
    hi_idx = max(0, min(hi_idx, iters - 1))
    return (means[lo_idx], means[hi_idx])


def correlation_pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = sqrt(sum((xi - mean_x) ** 2 for xi in x))
    den_y = sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if not den_x or not den_y:
        return None
    return num / (den_x * den_y)


def bootstrap_ci_correlation(x: Sequence[float], y: Sequence[float], *, iters: int = 400, alpha: float = 0.05, seed: int | None = None) -> Tuple[float, float] | None:
    if len(x) != len(y) or len(x) < 4:
        return None
    rnd = Random(seed)
    n = len(x)
    vals: List[float] = []
    for _ in range(iters):
        idxs = [rnd.randrange(0, n) for _ in range(n)]
        bx = [x[i] for i in idxs]
        by = [y[i] for i in idxs]
        r = correlation_pearson(bx, by)
        if r is not None:
            vals.append(r)
    if not vals:
        return None
    vals.sort()
    lo_idx = int((alpha / 2) * len(vals))
    hi_idx = int((1 - alpha / 2) * len(vals)) - 1
    lo_idx = max(0, min(lo_idx, len(vals) - 1))
    hi_idx = max(0, min(hi_idx, len(vals) - 1))
    return (vals[lo_idx], vals[hi_idx])


def _extract_series(sess) -> Dict[str, List[float]]:  # type: ignore[no-untyped-def]
    pain_levels: List[float] = []
    mood_index: List[float] = []
    sleep_index: List[float] = []
    mood_map = {"feliz": 0.2, "positivo": 0.1, "neutral": 0.0, "ansioso": 0.4, "triste": 0.5, "deprimido": 0.6}
    sleep_map = {"bien": 0.0, "regular": 0.2, "mal": 0.5, "pobre": 0.5}
    for ev in getattr(sess, "events", []):
        t = ev.get("type")
        if t == "pain_registration":
            data = (ev.get("data") or {}).get("pain") if isinstance(ev.get("data"), dict) else None
            if isinstance(data, dict):
                lvl = data.get("level") or data.get("pain_level") or data.get("value")
                if isinstance(lvl, (int, float)):
                    pain_levels.append(float(lvl))
        elif t == "mood_sleep":
            ms = (ev.get("data") or {}).get("mood_sleep") if isinstance(ev.get("data"), dict) else None
            if isinstance(ms, dict):
                mood = (ms.get("mood") or "").lower()
                sleep = (ms.get("sleep") or "").lower()
                mood_index.append(mood_map.get(mood, 0.3))  # default mid
                sleep_index.append(sleep_map.get(sleep, 0.25))
    return {"pain": pain_levels, "mood_index": mood_index, "sleep_index": sleep_index}


def build_session_enrichment(sess, *, seed: int | None = None) -> Dict[str, object]:  # type: ignore[no-untyped-def]
    series = _extract_series(sess)
    pain = series["pain"]
    enrich: Dict[str, object] = {"counts": {k: len(v) for k, v in series.items()}}
    if pain:
        ci_pain = bootstrap_ci_mean(pain, seed=seed)
        if ci_pain:
            enrich["pain_mean_ci"] = ci_pain
    # correlations
    mood = series["mood_index"]
    sleep = series["sleep_index"]
    if pain and mood and len(pain) == len(mood):
        r_pm = correlation_pearson(pain, mood)
        if r_pm is not None:
            enrich["corr_pain_mood"] = r_pm
            ci_pm = bootstrap_ci_correlation(pain, mood, seed=seed)
            if ci_pm:
                enrich["corr_pain_mood_ci"] = ci_pm
    if pain and sleep and len(pain) == len(sleep):
        r_ps = correlation_pearson(pain, sleep)
        if r_ps is not None:
            enrich["corr_pain_sleep"] = r_ps
            ci_ps = bootstrap_ci_correlation(pain, sleep, seed=seed)
            if ci_ps:
                enrich["corr_pain_sleep_ci"] = ci_ps
    return enrich


__all__ = [
    "bootstrap_ci_mean",
    "bootstrap_ci_correlation",
    "correlation_pearson",
    "build_session_enrichment",
]
