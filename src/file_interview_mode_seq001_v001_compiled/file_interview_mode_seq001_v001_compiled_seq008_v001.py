"""file_interview_mode_seq001_v001_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import json
import re

def _load_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    from .file_interview_mode_seq001_v001_compiled_seq001_v001 import interview_files

    parser = argparse.ArgumentParser(description="Ask codebase files local interview questions.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--question", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    result = interview_files(
        Path(args.root),
        question=args.question,
        files=args.file,
        limit=args.limit,
        write=not args.no_write,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


DEFAULT_QUESTIONS = [
    "What did you learn from the latest push?",
    "What do you think the fix is?",
    "Is your current path still paired to your identity after rename or split?",
]
