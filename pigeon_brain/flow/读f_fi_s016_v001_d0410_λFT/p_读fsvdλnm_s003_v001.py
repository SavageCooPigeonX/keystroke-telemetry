"""读f_fi_s016_v001_d0410_λFT_node_memory_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 26 lines | ~262 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, os, re, hashlib, urllib.request, urllib.error

def _load_nm(root: Path) -> dict:
    p = root / _NM_FILE
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def _save_nm(root: Path, nm: dict) -> None:
    (root / _NM_FILE).write_text(json.dumps(nm, indent=2, ensure_ascii=False), "utf-8")


def _credit_trend(nm: dict, node_name: str) -> str:
    entries = nm.get(node_name, {}).get("entries", [])[-5:]
    if not entries:
        return "no history"
    scores = [e.get("credit_score", 0) for e in entries]
    avg = round(sum(scores) / len(scores), 3)
    arrow = "↑" if scores[-1] > scores[0] else ("↓" if scores[-1] < scores[0] else "→")
    return f"avg={avg} {arrow}"


def get_file_understanding(root: Path, node_name: str) -> dict | None:
    """Pre-computed LLM understanding. Returns None if not interrogated yet."""
    return _load_nm(root).get(node_name, {}).get("file_understanding")
