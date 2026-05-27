"""Run the context compressor for changed Python files and log the result."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.context_compressor_seq001_v001 import compress_changed


def changed_files(root: Path) -> list[str] | None:
    """Return best-effort changed files for a hook run."""
    probes = [
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "@{u}...HEAD"],
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "--cached"],
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD~1..HEAD"],
    ]
    for cmd in probes:
        try:
            out = subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True, encoding="utf-8").stdout
        except Exception:
            continue
        files = [line.strip() for line in out.splitlines() if line.strip()]
        py_files = [file for file in files if file.endswith(".py")]
        if py_files:
            return py_files
    return None


def run(root: Path, all_files: bool = False) -> dict:
    files = None if all_files else changed_files(root)
    result = compress_changed(root, files)
    payload = {
        "schema": "context_compression_push/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": "all" if all_files else "changed",
        "changed_files": files,
        "result": result,
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "context_compression_push_latest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (logs / "context_compression_push.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="compress every eligible Python file")
    args = parser.parse_args()
    payload = run(ROOT, all_files=args.all)
    print(json.dumps(payload["result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
