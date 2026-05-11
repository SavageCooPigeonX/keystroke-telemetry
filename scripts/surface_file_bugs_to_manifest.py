"""Run stale checks and surface file bugs into manifest state."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-stale-audit", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    owner = Path(__file__).resolve().parents[1]
    if str(owner) not in sys.path:
        sys.path.insert(0, str(owner))
    if not args.no_stale_audit:
        from src.pipeline_staleness_audit_seq001_v001 import run_pipeline_staleness_audit

        run_pipeline_staleness_audit(root, write=True)
    from src.file_bug_surface_seq001_v001 import build_file_bug_surface
    from src.file_bug_chat_seq001_v001 import build_file_bug_chat
    from src.root_sim_key_file_seq001_v001 import build_root_sim_key_file
    from src.unified_manifest_state_seq001_v001 import refresh_master_manifest

    surface = build_file_bug_surface(root, write=True)
    build_file_bug_chat(root, write=True)
    build_root_sim_key_file(root, write=True)
    refresh_master_manifest(root, [], dry_run=False)
    print(f"file_bug_surface: bugs={surface['bug_count']} action={surface['most_logical_autonomous_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
