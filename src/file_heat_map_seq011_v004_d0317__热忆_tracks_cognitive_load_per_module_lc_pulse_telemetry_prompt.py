"""Per-file hesitation map — tracks cognitive load per module over time.

Cross-references operator typing patterns with recently-committed pigeon files
to build a complexity debt map: which modules consistently spike hesitation,
deletion rate, or produce rework. This tells the AI exactly where the operator
struggles before they even ask.

Reads pigeon_registry.json + rework_log.json. Zero LLM calls.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v004 | 144 lines | ~1,347 tokens
# DESC:   tracks_cognitive_load_per_module
# INTENT: pulse_telemetry_prompt
# LAST:   2026-03-17 @ 9e2a305
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HEAT_STORE      = 'file_heat_map.json'
RECENT_MSGS     = 3    # messages after a commit = "working on that file"
HIGH_HES_THRESH = 0.45
HIGH_VER_THRESH = 5    # ≥5 versions = recurring pain point


def update_heat_map(root: Path, state: str, hesitation: float,
                    rework_verdict: str, wpm: float) -> None:
    """Associate current message metrics with recently-touched pigeon files."""
    registry_path = root / 'pigeon_registry.json'
    if not registry_path.exists():
        return
    try:
        registry = json.loads(registry_path.read_text('utf-8'))
    except Exception:
        return

    heat_path = root / HEAT_STORE
    try:
        heat = json.loads(heat_path.read_text('utf-8')) if heat_path.exists() else {}
    except Exception:
        heat = {}

    # Find recently-modified files (sorted by date in filename)
    recent_files = _get_recent_files(registry, top_n=RECENT_MSGS)

    for module_name in recent_files:
        entry = heat.setdefault(module_name, {
            'samples': [], 'avg_hes': 0.0, 'avg_wpm': 0.0,
            'miss_count': 0, 'total': 0,
        })
        entry['samples'].append({
            'ts':       datetime.now(timezone.utc).isoformat(),
            'hes':      hesitation,
            'wpm':      wpm,
            'state':    state,
            'rework':   rework_verdict,
        })
        # Keep last 20 samples per file
        entry['samples'] = entry['samples'][-20:]
        samples = entry['samples']
        entry['avg_hes']    = round(sum(s['hes'] for s in samples) / len(samples), 3)
        entry['avg_wpm']    = round(sum(s['wpm'] for s in samples) / len(samples), 1)
        entry['miss_count'] = sum(1 for s in samples if s['rework'] == 'miss')
        entry['total']      = len(samples)

    heat_path.write_text(json.dumps(heat, indent=2), encoding='utf-8')


def _get_recent_files(registry: dict, top_n: int = 3) -> list[str]:
    """Return module names of the most recently versioned files.

    pigeon_registry.json has structure: {"files": [...entries...]}
    but callers may also pass the already-unpacked {path: entry} dict
    from load_registry(). Handle both formats.
    """
    # Raw JSON format: {"generated": ..., "total": ..., "files": [...]}
    if 'files' in registry and isinstance(registry['files'], list):
        entries = registry['files']
    else:
        # Already unpacked {path: entry_dict} from load_registry()
        entries = [v for v in registry.values() if isinstance(v, dict)]
    entries = sorted(entries, key=lambda e: (e.get('ver', 1), e.get('date', '')), reverse=True)
    return [e['name'] for e in entries[:top_n] if e.get('name')]


def load_heat_map(root: Path) -> dict:
    """Load file heat map → summary for coaching prompt."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        heat = json.loads(heat_path.read_text('utf-8'))
    except Exception:
        return {}

    # High-hesitation files (cognitive complexity debt)
    complex_files = [
        {'module': name, 'avg_hes': d['avg_hes'], 'avg_wpm': d['avg_wpm'],
         'miss_count': d['miss_count'], 'samples': d['total']}
        for name, d in heat.items()
        if d['avg_hes'] >= HIGH_HES_THRESH and d['total'] >= 2
    ]
    complex_files.sort(key=lambda x: x['avg_hes'], reverse=True)

    # High miss-rate files
    miss_files = [
        {'module': name, 'miss_rate': round(d['miss_count'] / max(d['total'], 1), 2)}
        for name, d in heat.items()
        if d['total'] >= 2 and d['miss_count'] / max(d['total'], 1) >= 0.4
    ]
    miss_files.sort(key=lambda x: x['miss_rate'], reverse=True)

    return {
        'modules_tracked':  len(heat),
        'complex_files':    complex_files[:5],   # top 5 by hesitation
        'high_miss_files':  miss_files[:3],       # top 3 AI-failure zones
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
    entries = [
        {'module': e['name'], 'ver': e.get('ver', 1),
         'desc': e.get('desc', ''), 'tokens': e.get('tokens', 0)}
        for e in reg.values()
        if e.get('ver', 1) >= HIGH_VER_THRESH
    ]
    entries.sort(key=lambda x: x['ver'], reverse=True)
    return entries[:8]
