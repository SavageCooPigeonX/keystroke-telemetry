"""codex_compat_seq040_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _append_jsonl
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq002_v001 import _repo_root
from .codex_compat_seq031_v001 import refresh_state
from pathlib import Path
from typing import Any
import importlib.util
import json
import re

def capture_pair(root: Path) -> dict[str, Any] | None:
    root = Path(root)
    repo = _repo_root()
    src_dir = repo / "src"
    candidates = sorted(src_dir.glob("*s027*.py"), key=lambda item: item.name)
    for candidate in candidates:
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "def capture_training_pair" not in text or "def _load_jsonl_tail" not in text:
            continue
        spec = importlib.util.spec_from_file_location("codex_training_pairs", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pair = module.capture_training_pair(root)
        refresh_state(root, "captured training pair")
        return pair
    raise ImportError(f"No complete training pair module found under {src_dir}")


def record_entropy_shed(root: Path, module: str, confidence: float, note: str = "") -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": _utc_now(),
        "module": module,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "note": note,
        "source": "codex_explicit",
    }
    _append_jsonl(root / "logs" / "entropy_sheds.jsonl", entry)
    refresh_state(root, f"recorded entropy shed for {module}")
    return entry
