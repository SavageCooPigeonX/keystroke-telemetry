"""双f_dsb_s008_v002_d0323_缩分话_λP_renderer_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 11 lines | ~121 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def render_dual_json(root: Path, output: str = "pigeon_brain/dual_view.json") -> Path:
    """Write the dual-substrate view as JSON for the React UI to consume."""
    view = build_dual_view(root)
    out = root / output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(view, indent=2), encoding="utf-8")
    return out
