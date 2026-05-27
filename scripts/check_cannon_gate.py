"""Check the repo-wide cannon gate before executor work."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--no-hash", action="store_true", help="do not require latest cannon to match this prompt")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    owner = Path(__file__).resolve().parents[1]
    if str(owner) not in sys.path:
        sys.path.insert(0, str(owner))

    from src.cannon_execution_gate_seq001_v001 import build_cannon_execution_gate

    result = build_cannon_execution_gate(
        root,
        args.prompt,
        write=True,
        require_prompt_hash=not args.no_hash,
    )
    if result["cleared"]:
        print(
            "cannon_gate: cleared "
            f"class={result['prompt_class']} "
            f"executor={result['executor_session']} "
            f"predicted={result['predicted_file_count']}"
        )
        return 0
    print("cannon_gate: blocked " + ", ".join(result["blockers"]))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
