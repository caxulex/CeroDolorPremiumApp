"""Generate a CycloneDX SBOM if tooling is available.

Attempts to use cyclonedx-bom. If not installed, prints instructions.

Usage:
  python scripts/generate_sbom.py --format json --output sbom.json
  python scripts/generate_sbom.py --format xml --output sbom.xml
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def generate(fmt: str, output: Path) -> int:
    tool = shutil.which("cyclonedx-py") or shutil.which("cyclonedx-bom")
    if not tool:
        print("Herramienta cyclonedx no instalada. Instala: pip install cyclonedx-bom", file=sys.stderr)
        return 1
    # Choose command style based on binary name
    if tool.endswith("cyclonedx-py"):
        cmd = [tool, "--format", fmt, "--output", str(output)]
    else:  # cyclonedx-bom
        cmd = [tool, "-o", str(output), "-F", fmt]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:  # noqa: BLE001
        print(f"Fallo ejecutando {' '.join(cmd)}: {e}", file=sys.stderr)
        return e.returncode or 1
    print(f"SBOM generado: {output}")
    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Generate CycloneDX SBOM")
    ap.add_argument("--format", choices=["json", "xml"], default="json")
    ap.add_argument("--output", type=Path, default=Path("sbom.json"))
    return ap.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = parse_args()
    rc = generate(args.format, args.output)
    raise SystemExit(rc)
