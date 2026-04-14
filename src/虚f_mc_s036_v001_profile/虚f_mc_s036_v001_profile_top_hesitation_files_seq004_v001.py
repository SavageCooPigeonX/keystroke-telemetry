"""虚f_mc_s036_v001_profile_top_hesitation_files_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 19 lines | ~204 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def top_hesitation_files(root: Path, threshold: float, max_n: int) -> list[dict]:
    heat = _jload(root / 'file_heat_map.json') or {}
    items = []
    for name, v in heat.items():
        if not isinstance(v, dict):
            continue
        if not is_real_module_name(name):
            continue
        samples = v.get('samples', [])
        if len(samples) < 2:
            continue
        avg_hes = sum(s.get('hes', 0) for s in samples) / max(len(samples), 1)
        if avg_hes >= threshold:
            items.append({'module': name, 'avg_hes': round(avg_hes, 3), 'samples': len(samples)})
    return sorted(items, key=lambda x: x['avg_hes'], reverse=True)[:max_n]
