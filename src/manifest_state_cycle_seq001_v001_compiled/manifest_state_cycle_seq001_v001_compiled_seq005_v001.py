"""manifest_state_cycle_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _own_manifest(root: Path, rel: str) -> Path | None:
    path = Path(rel)
    parts = path.parts
    for index in range(len(parts), 0, -1):
        candidate = root / Path(*parts[:index]) / "MANIFEST.md"
        if candidate.exists():
            return candidate
    return root / "MANIFEST.md" if (root / "MANIFEST.md").exists() else None


def _belongs(file_path: str, folder: str) -> bool:
    clean = file_path.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


LATEST = "logs/manifest_state_write_latest.json"

HISTORY = "logs/manifest_state_write.jsonl"

MARKDOWN = "logs/manifest_state_write.md"
