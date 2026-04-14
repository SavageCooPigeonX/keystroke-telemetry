"""numeric_surface_dual_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 12 lines | ~121 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _build_dual_lookup(root: Path) -> dict[str, dict]:
    """Load dual_view.json and return name→node dict."""
    dv = root / "pigeon_brain" / "dual_view.json"
    if not dv.exists():
        return {}
    raw = json.loads(dv.read_text("utf-8"))
    nodes = raw.get("nodes", []) if isinstance(raw, dict) else []
    return {n["name"]: n for n in nodes if "name" in n}
