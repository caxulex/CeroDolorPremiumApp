from backend.src.utils.normalization import sanitize_enum


def test_sanitize_enum_direct_match():
    assert sanitize_enum("Regular", ["bueno", "regular", "irregular", "malo"], default="regular") == "regular"


def test_sanitize_enum_alias():
    assert sanitize_enum(
        "desconocido",
        ["bueno", "regular", "irregular", "malo"],
        mapping={"desconocido": "regular"},
        default="regular",
    ) == "regular"


def test_sanitize_enum_fallback():
    assert sanitize_enum(
        "whatever",
        ["bueno", "regular", "irregular", "malo"],
        default="regular",
    ) == "regular"


def test_sanitize_enum_case_sensitive():
    assert sanitize_enum(
        "Regular",
        ["regular"],
        default="regular",
        case_insensitive=False,
    ) == "regular"  # because candidate == allowed (exact case required)


def test_sanitize_enum_invalid_default_raises():
    import pytest
    with pytest.raises(ValueError):
        sanitize_enum("x", ["a"], default="b")
