"""push_snapshot_seq001_v001_heat_map_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 28 lines | ~296 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_heat_map(root: Path) -> dict:
    p = root / 'file_heat_map.json'
    if not p.exists():
        return {'count': 0, 'avg_hes': 0, 'hottest': []}
    try:
        data = json.loads(p.read_text('utf-8'))
        modules = []
        for name, info in data.items():
            avg_hes = info.get('avg_hes', 0)
            if isinstance(info, dict) and 'samples' in info:
                samples = info['samples']
                if samples:
                    hes_vals = [s.get('hes', 0) for s in samples if isinstance(s, dict)]
                    avg_hes = sum(hes_vals) / len(hes_vals) if hes_vals else 0
            modules.append({'name': name, 'hes': round(avg_hes, 3)})
        modules.sort(key=lambda x: x['hes'], reverse=True)
        all_hes = [m['hes'] for m in modules if m['hes'] > 0]
        return {
            'count': len(modules),
            'avg_hes': round(sum(all_hes) / len(all_hes), 3) if all_hes else 0,
            'hottest': modules[:10],
        }
    except Exception:
        return {'count': 0, 'avg_hes': 0, 'hottest': []}
