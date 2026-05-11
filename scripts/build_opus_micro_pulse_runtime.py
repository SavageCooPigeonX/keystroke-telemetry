"""Build the Opus micro-pulse runtime packet from prompt history or a prompt."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--max-pulses", type=int, default=3)
    parser.add_argument("--file-limit", type=int, default=8)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    owner = Path(__file__).resolve().parents[1]
    if str(owner) not in sys.path:
        sys.path.insert(0, str(owner))

    from src.opus_micro_pulse_runtime_seq001_v001 import build_opus_micro_pulse_runtime

    result = build_opus_micro_pulse_runtime(
        root,
        args.prompt or None,
        write=True,
        max_pulses=args.max_pulses,
        file_limit=args.file_limit,
    )
    cannon = result["cannon_job"]
    print(
        "opus_micro_pulse: "
        f"class={cannon['prompt_class']} "
        f"executor={cannon['executor_session']} "
        f"pulses={result['pulse_count']} "
        f"predicted={len(cannon['predicted_files'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
