"""codex_compat_capture_pair_seq069_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 069 | VER: v002 | 27 lines | ~332 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_refresh_state_seq057_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import refresh_state
from .codex_compat_repo_root_seq008_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _repo_root
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
