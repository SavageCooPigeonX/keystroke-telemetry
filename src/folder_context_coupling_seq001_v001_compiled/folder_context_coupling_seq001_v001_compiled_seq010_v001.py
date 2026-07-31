"""folder_context_coupling_seq001_v001_compiled_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


LATEST = "logs/folder_context_coupling_latest.json"

HISTORY = "logs/folder_context_coupling.jsonl"

MARKDOWN = "logs/folder_context_coupling.md"

FILE_SCAN_CAP = 600

OVERCAP_LINE_LIMIT = 800

PACKAGE_RANK_SCAN_CAP = 40

AST_IDENTITY_FILE_CAP = 6


_IDENTITY_STOPWORDS = {
    "ago",
    "and",
    "any",
    "are",
    "bool",
    "class",
    "def",
    "dict",
    "file",
    "files",
    "folder",
    "from",
    "get",
    "import",
    "json",
    "list",
    "local",
    "none",
    "path",
    "pigeon",
    "project",
    "repo",
    "return",
    "self",
    "seq001",
    "str",
    "true",
    "v001",
    "with",
}
