"""Purge a patient session JSON file safely.

Usage:
  python scripts/purge_session.py --patient-id <id>

Options:
  --dry-run   Show the target file without deleting.

Exit codes:
  0 success / nothing to do
  1 error (missing id or file issues)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root on path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.src.utils.persistence import store  # type: ignore
except ModuleNotFoundError as e:  # pragma: no cover
    print(f"[FATAL] Import failure: {e}. Ejecutar desde la raíz del repo.", file=sys.stderr)
    raise


def resolve_path(patient_id: str) -> Path:
    # Use internal path builder via store API (private) replicated logic
    root = store.root  # type: ignore[attr-defined]
    safe = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")) or "session"
    return root / f"{safe}.json"


def purge(patient_id: str, dry_run: bool) -> int:
    path = resolve_path(patient_id)
    if not path.exists():
        print(f"No existe archivo para paciente '{patient_id}' ({path}).")
        return 0
    if dry_run:
        print(f"[DRY-RUN] Se eliminaría: {path}")
        return 0
    try:
        path.unlink()
    except Exception as e:  # noqa: BLE001
        print(f"Error eliminando {path}: {e}", file=sys.stderr)
        return 1
    # Remove also cached session in memory if loaded
    try:
        if patient_id in store._cache:  # type: ignore[attr-defined]
            del store._cache[patient_id]  # type: ignore[attr-defined]
    except Exception:
        pass
    print(f"Sesión '{patient_id}' eliminada.")
    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Purge patient session file")
    ap.add_argument("--patient-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = parse_args()
    rc = purge(args.patient_id, args.dry_run)
    raise SystemExit(rc)
