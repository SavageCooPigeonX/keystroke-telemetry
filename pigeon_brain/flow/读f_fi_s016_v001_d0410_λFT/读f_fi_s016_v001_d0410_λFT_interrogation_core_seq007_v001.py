"""读f_fi_s016_v001_d0410_λFT_interrogation_core_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 47 lines | ~420 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json, os, re, hashlib, urllib.request, urllib.error

def interrogate_file(
    root: Path, file_path: str, node_name: str, bugs: list, force: bool = False
) -> dict | None:
    """LLM reads file, caches result by source hash. Skips if unchanged (unless force)."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(f"  SKIP {node_name} — no GEMINI_API_KEY")
        return None

    src_path = root / file_path
    if not src_path.exists():
        return None

    source = src_path.read_text("utf-8", errors="replace")
    src_hash = hashlib.md5(source.encode()).hexdigest()[:12]

    nm = _load_nm(root)
    existing = nm.get(node_name, {}).get("file_understanding", {})
    if not force and existing.get("source_hash") == src_hash:
        return existing  # cache hit — file unchanged

    prompt = _build_prompt(node_name, source, bugs, _credit_trend(nm, node_name))
    raw = _call_gemini(prompt, api_key)

    understanding = _parse_json(raw)
    if not understanding:
        understanding = {
            "intent": "parse_failed",
            "autonomous_directive": raw[:300],
            "what_to_fix": [],
            "break_risk": [],
        }

    understanding.update({
        "source_hash": src_hash,
        "interrogated_at": datetime.now(timezone.utc).isoformat(),
        "model": _MODEL,
    })

    nm.setdefault(node_name, {})["file_understanding"] = understanding
    _save_nm(root, nm)
    return understanding
