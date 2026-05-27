"""Build ROOT_SIM_KEYS.md from the latest sim surfaces."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    owner = Path(__file__).resolve().parents[1]
    if str(owner) not in sys.path:
        sys.path.insert(0, str(owner))
    from src.root_sim_key_file_seq001_v001 import build_root_sim_key_file

    result = build_root_sim_key_file(root, write=True)
    print(f"root_sim_key_file: called={result['called_count']} path={result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
