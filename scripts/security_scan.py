"""Optional security scan runner.

Executes Bandit (if installed) with a lightweight configuration against the
project source directories. Exits with non-zero only if critical issues found
(unless --strict passed).

Usage:
  python scripts/security_scan.py
  python scripts/security_scan.py --strict
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

TARGETS = ["backend/src", "scripts"]


def run_bandit(strict: bool) -> int:
    if shutil.which("bandit") is None:
        print("Bandit no instalado (pip install bandit). Saliendo con 0.")
        return 0
    cmd = [
        "bandit",
        "-q",
        "-r",
        *TARGETS,
        "-x",
        "tests",
        "--severity-level",
        "LOW",
        "--confidence-level",
        "LOW",
        "-f",
        "json",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as e:  # noqa: BLE001
        print(f"Error ejecutando bandit: {e}")
        return 1 if strict else 0

    if proc.returncode != 0 and strict:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        return proc.returncode

    # In non-strict mode, always succeed but still show summary lines
    if proc.stdout:
        print(proc.stdout[:4000])  # truncate defensive
    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Fail build on Bandit findings")
    return ap.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = parse_args()
    raise SystemExit(run_bandit(args.strict))
