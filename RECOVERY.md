Recovery and Rollback Guide

Git restore points
- From tag:
  - `git fetch --tags`
  - `git checkout -b restore/from-tag checkpoint-2025-09-16`
- From checkpoint branch:
  - `git fetch origin checkpoint/project-b-aic-2025-09-16`
  - `git checkout -b restore/from-branch origin/checkpoint/project-b-aic-2025-09-16`
- Hard reset to tag (DANGEROUS: discards local changes):
  - `git reset --hard checkpoint-2025-09-16`

Local ZIP snapshot
- Location: `checkpoints/snapshot-YYYYMMDD-HHMMSS.zip`
- Unzip into a clean directory to restore working files quickly.

Quality gates
- `& .\.venv\Scripts\Activate.ps1`
- `..\.venv\Scripts\python.exe -m ruff check backend`
- `..\.venv\Scripts\python.exe -m pytest -q`
