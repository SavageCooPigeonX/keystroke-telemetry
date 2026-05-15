"""codex_compat_load_intent_numeric_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v002 | 32 lines | ~344 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_repo_root_seq008_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _repo_root
from pathlib import Path
from typing import Any
import importlib.util
import json
import re

def _load_intent_numeric(root: Path) -> Any | None:
    src_dir = _repo_root() / "src"
    matches = sorted(src_dir.glob("intent_numeric_seq001*.py"), key=lambda item: item.name)
    for module_path in matches:
        spec = importlib.util.spec_from_file_location("codex_intent_numeric", module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = Path(root)
        module.VOCAB_PATH = Path(root) / "logs" / "intent_vocab.json"
        module.MATRIX_PATH = Path(root) / "logs" / "intent_matrix.json"
        module.TOUCH_LOG_PATH = Path(root) / "logs" / "intent_touches.jsonl"
        module._vocab = {}
        module._vocab_inverse = {}
        module._next_id = 1
        module._vocab_loaded = False
        module._matrix = {}
        module._touch_counts = {}
        module._matrix_loaded = False
        module._surface_healed = False
        module._lexicon_cache = None
        return module
    return None
