"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_load_hesitation_map_seq025_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 025 | VER: v001 | 22 lines | ~202 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_hesitation_map(root: Path) -> dict:
    """Load message_id → hesitation_score from all summary files."""
    hes = {}
    for d in LOG_DIRS:
        log_dir = root / d
        if not log_dir.is_dir():
            continue
        for sf in log_dir.glob('summary_*.json'):
            try:
                data = json.loads(sf.read_text(encoding='utf-8', errors='ignore'))
                for msg in data.get('messages', []):
                    mid = msg.get('message_id', '')
                    if mid:
                        hes[mid] = msg.get('hesitation_score', 0.0)
            except Exception:
                continue
    return hes
