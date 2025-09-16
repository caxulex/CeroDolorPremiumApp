# ruff: noqa: I001
import json
import subprocess
import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parent  # backend/
AIP = BACKEND / "src" / "agents" / "aip.py"
ASD = BACKEND / "src" / "agents" / "asd.py"
AIPER = BACKEND / "src" / "agents" / "aiper.py"


def run_agent(path: Path, payload: dict) -> dict:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(path)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout.decode() or "{}")


def main() -> None:
    # Simulate: AIP → ASD → AIPer
    msg = {"type": "ping", "from": "router"}
    r1 = run_agent(AIP, msg)
    r2 = run_agent(ASD, r1)
    r3 = run_agent(AIPER, r2)
    print(json.dumps({"aip": r1, "asd": r2, "aiper": r3}, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
