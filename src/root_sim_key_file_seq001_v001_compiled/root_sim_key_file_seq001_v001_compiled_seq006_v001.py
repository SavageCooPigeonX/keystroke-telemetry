"""root_sim_key_file_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _local_manifest(file_path: str) -> str:
    clean = file_path.strip("\"'").replace("\\", "/")
    if not clean or "/" not in clean:
        return "MANIFEST.md"
    folder = str(Path(clean).parent).replace("\\", "/")
    if folder in {"", "."}:
        return "MANIFEST.md"
    return f"{folder}/MANIFEST.md"

def _cell(value: Any, limit: int = 140) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]

def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

ROOT_KEY = "ROOT_SIM_KEYS.md"

DEFAULT_ATTENTION_LIMIT = 18
