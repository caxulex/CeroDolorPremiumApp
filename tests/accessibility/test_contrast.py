import re

# Simple WCAG contrast checker for a subset of theme colors.
# Formula per WCAG 2.1: (L1+0.05)/(L2+0.05) >= threshold

def _rel_luminance(rgb):
    def _adj(c):
        c = c / 255.0
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055) ** 2.4
    r, g, b = rgb
    return 0.2126*_adj(r) + 0.7152*_adj(g) + 0.0722*_adj(b)

_hex_re = re.compile(r"^#([0-9a-fA-F]{6})$")

def _hex_to_rgb(h):
    m = _hex_re.match(h)
    assert m, f"Invalid hex {h}"
    v = m.group(1)
    return tuple(int(v[i:i+2], 16) for i in (0,2,4))

# Chosen pairs: text on background, accent on white, anomaly badge text on anomaly background.
PAIRS = [
    ("#2D3748", "#FFFFFF", "text on white"),
    ("#FFFFFF", "#DD6B20", "white on accent"),
    ("#fee2e2", "#b91c1c", "anomaly reverse"),
]

MIN_AA_NORMAL = 4.5

def contrast_ratio(fg, bg):
    lf = _rel_luminance(_hex_to_rgb(fg))
    lb = _rel_luminance(_hex_to_rgb(bg))
    lighter, darker = (lf, lb) if lf > lb else (lb, lf)
    return (lighter + 0.05) / (darker + 0.05)

def test_color_contrast_pairs():
    failures = []
    for fg, bg, label in PAIRS:
        ratio = contrast_ratio(fg, bg)
        if ratio < MIN_AA_NORMAL:
            failures.append((label, ratio))
    assert not failures, f"Contrast failures: {failures}"
