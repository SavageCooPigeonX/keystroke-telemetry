"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_loaders_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 99 lines | ~794 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_edit_events(root: Path) -> list[dict]:
    """Load Copilot edit events from edit_pairs.jsonl only.

    This is the edit-only ground truth: prompt-linked file mutations harvested
    from telemetry pulses. No response-text heuristics.
    """
    ep = root / 'logs' / 'edit_pairs.jsonl'
    if not ep.exists():
        return []

    events = []
    for line in ep.read_text('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        raw_file = entry.get('file', '')
        if not raw_file:
            continue
        events.append({
            'file': raw_file,
            'module': _module_key(raw_file),
            'region': _region_from_path(raw_file),
            'edit_ts': entry.get('edit_ts') or entry.get('ts', ''),
            'latency_ms': max(0, int(entry.get('latency_ms', 0) or 0)),
            'edit_why': (entry.get('edit_why') or 'auto').strip(),
            'state': (entry.get('state') or 'unknown').strip(),
        })
    return events


def _load_entropy_scores(root: Path) -> dict[str, float]:
    """Load per-module entropy from entropy_map.json."""
    ep = root / 'logs' / 'entropy_map.json'
    if not ep.exists():
        return {}
    try:
        data = json.loads(ep.read_text('utf-8', errors='ignore'))
        result = {}
        for m in data.get('top_entropy_modules', []):
            mod = m.get('module', '')
            if mod:
                result[mod] = m.get('avg_entropy', 0.0)
        return result
    except Exception:
        return {}


def load_heat_map(root: Path) -> dict:
    """Load file heat map → sorted list for coaching prompt."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        heat = json.loads(heat_path.read_text('utf-8'))
    except Exception:
        return {}

    hot_files = [
        {'module': name, 'heat': d['heat'],
         'touches': d['touch_score'], 'entropy': d['entropy']}
        for name, d in heat.items()
    ]
    hot_files.sort(key=lambda x: x['heat'], reverse=True)

    return {
        'modules_tracked': len(heat),
        'hot_files': hot_files[:8],
    }


def load_registry_churn(root: Path) -> list[dict]:
    """Return top-churn modules from pigeon_registry for heat enrichment."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception:
        return []
    files = reg.get('files', [])
    if not isinstance(files, list):
        files = [v for v in reg.values() if isinstance(v, dict)]
    entries = [
        {'module': e.get('name', ''), 'ver': e.get('ver', 1),
         'desc': e.get('desc', ''), 'tokens': e.get('tokens', 0)}
        for e in files
        if e.get('ver', 1) >= HIGH_VER_THRESH
    ]
    entries.sort(key=lambda x: x['ver'], reverse=True)
    return entries[:8]
