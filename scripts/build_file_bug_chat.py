"""Build operator/Opus chat comments for surfaced file bugs."""
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
    from src.file_bug_chat_seq001_v001 import build_file_bug_chat
    from src.root_sim_key_file_seq001_v001 import build_root_sim_key_file
    from src.unified_manifest_state_seq001_v001 import refresh_master_manifest

    chat = build_file_bug_chat(root, write=True)
    build_root_sim_key_file(root, write=True)
    refresh_master_manifest(root, [], dry_run=False)
    print(f"file_bug_chat: comments={chat['comment_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
