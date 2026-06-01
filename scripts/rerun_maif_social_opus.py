"""Rerun MAIF social Opus 4.8 tone repair from exported Supabase rows."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--input", default="", help="JSON/JSONL export of MAIF social rows")
    parser.add_argument("--table", default="", help="Supabase table name; defaults to MAIF_SOCIAL_POSTS_TABLE or maif_social_posts")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--apply", action="store_true", help="PATCH Supabase rows using SUPABASE_URL and service key env")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    owner = Path(__file__).resolve().parents[1]
    if str(owner) not in sys.path:
        sys.path.insert(0, str(owner))

    from src.maif_social_opus_rerun_seq001_v001 import build_maif_social_opus_rerun

    result = build_maif_social_opus_rerun(
        root,
        input_path=args.input or None,
        apply=args.apply,
        table=args.table or None,
        limit=args.limit or None,
        write=True,
    )
    print(json.dumps({
        "status": result["status"],
        "source": result["source"],
        "candidate_count": result["candidate_count"],
        "supabase_apply": result["supabase_apply"],
        "latest": result["paths"]["latest"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
