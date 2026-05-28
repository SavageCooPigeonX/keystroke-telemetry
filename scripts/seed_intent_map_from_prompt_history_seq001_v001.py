"""Replay complex prompt history through the intent-map router."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.tc_intent_keys_seq001_v001 import seed_intent_graphs_from_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed intent graph/profile memory from prompt history")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--history", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("prompts", nargs="*")
    args = parser.parse_args()

    summary = seed_intent_graphs_from_history(
        Path(args.root),
        history_path=Path(args.history) if args.history else None,
        prompts=args.prompts or None,
        limit=args.limit,
        write=not args.no_write,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
