"""Normalization utilities for enum-like fields.

Provides a generic sanitizer that coerces incoming values
into a permitted enumeration set with optional mapping and
fallback default.
"""
from __future__ import annotations
from typing import Iterable, Mapping, Any

__all__ = ["sanitize_enum"]


def sanitize_enum(
    raw: Any,
    allowed: Iterable[str],
    *,
    mapping: Mapping[str, str] | None = None,
    default: str,
    case_insensitive: bool = True,
) -> str:
    """Return a sanitized enum value.

    Parameters
    ----------
    raw : Any
        Incoming value (could be None or non-string).
    allowed : Iterable[str]
        The canonical permitted values.
    mapping : Mapping[str, str] | None, optional
        Extra alias -> canonical mappings (applied after case folding if enabled).
    default : str
        Value to use if nothing matches; must itself be in `allowed`.
    case_insensitive : bool, default True
        If true, performs case-fold normalization for comparison.

    Returns
    -------
    str
        A valid member of `allowed`.
    """
    allowed_set = list(allowed)
    if default not in allowed_set:
        raise ValueError(f"default '{default}' not in allowed set: {allowed_set}")

    if isinstance(raw, str):
        candidate = raw.strip()
        candidate_lower = candidate.lower() if case_insensitive else None

        if case_insensitive:
            allowed_lookup = {v.lower(): v for v in allowed_set}
            if candidate_lower in allowed_lookup:  # type: ignore[arg-type]
                return allowed_lookup[candidate_lower]  # type: ignore[index]
        else:
            if candidate in allowed_set:
                return candidate

        # Apply mapping if provided
        if mapping:
            # Build lowered mapping if case-insensitive
            if case_insensitive and candidate_lower is not None:
                lowered_map = {k.lower(): v for k, v in mapping.items()}
                if candidate_lower in lowered_map:
                    mapped = lowered_map[candidate_lower]
                    if mapped in allowed_set:
                        return mapped
            else:
                if candidate in mapping:  # type: ignore[operator]
                    mapped = mapping[candidate]  # type: ignore[index]
                    if mapped in allowed_set:
                        return mapped

    # Nothing matched
    return default
