"""Record accepted Codex edits into training telemetry."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.codex_edit_outcome_binder_seq001_v001 import bind_codex_edit_outcome


def changed_files(root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="files to bind; defaults to git diff")
    parser.add_argument("--reason", default="accepted Codex edit outcome")
    parser.add_argument("--no-training", action="store_true")
    args = parser.parse_args()
    files = args.files or changed_files(ROOT)
    payload = bind_codex_edit_outcome(
        ROOT,
        files,
        reason=args.reason,
        capture_training=not args.no_training,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["edit_pairs_written"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
