"""Per-file heat map — tracks Copilot edit frequency + entropy per module.

Mines edit_pairs.jsonl for which files Copilot actually touches, weighted by
recency. Cross-references entropy_map.json for uncertainty scores. The combined
signal tells the thought completer which files are actually hot — not which
files the operator hesitates on.

Reads edit_pairs.jsonl + entropy_map.json. Zero LLM calls.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

HEAT_STORE      = 'file_heat_map.json'
COPILOT_BRAIN_STORE = 'logs/copilot_brain_map.json'
DECAY_HALF_LIFE = 86400 * 3  # 3 days — touches decay to half relevance
HIGH_VER_THRESH = 5
QUICK_RETOUCH_S = 20 * 60
HIGH_LATENCY_MS = 5 * 60_000

STATE_ENTROPY = {
    'focused': 0.05,
    'neutral': 0.08,
    'restructuring': 0.18,
    'abandoned': 0.24,
    'hesitant': 0.28,
    'frustrated': 0.32,
    'confused': 0.30,
    'unknown': 0.12,
}


def update_heat_map(root: Path, **_kw) -> None:
    """Rebuild heat map from Copilot edit history + entropy scores.

    Reads edit_pairs.jsonl for touch counts with time-decay,
    reads entropy_map.json for per-module uncertainty.
    Combined: heat = decayed_touches * (1 + entropy).
    """
    events = _load_edit_events(root)
    touches = _count_copilot_touches(root, events)
    entropy = _load_entropy_scores(root)
    brain = _build_copilot_brain_map(root, events, touches)
    edit_entropy = {
        mod: data.get('edit_entropy', 0.0)
        for mod, data in brain.get('modules', {}).items()
    }

    heat = {}
    all_modules = set(touches) | set(entropy) | set(edit_entropy)
    for mod in all_modules:
        touch_score = touches.get(mod, 0.0)
        ent = entropy.get(mod, 0.0)
        copilot_ent = edit_entropy.get(mod, 0.0)
        region = brain.get('modules', {}).get(mod, {}).get('region', 'cortex')
        heat_score = touch_score * (1 + ent + copilot_ent)
        if touch_score == 0 and ent > 0.3:
            heat_score = max(heat_score, 0.1 * ent)
        if touch_score == 0 and copilot_ent > 0.3:
            heat_score = max(heat_score, 0.08 * copilot_ent)
        heat[mod] = {
            'touch_score': round(touch_score, 3),
            'entropy': round(ent, 3),
            'copilot_edit_entropy': round(copilot_ent, 3),
            'brain_region': region,
            'heat': round(heat_score, 3),
        }

    # Add high-entropy modules even if Copilot hasn't touched them recently
    for mod, ent in entropy.items():
        if mod not in heat and ent > 0.3:
            heat[mod] = {
                'touch_score': 0.0,
                'entropy': round(ent, 3),
                'copilot_edit_entropy': 0.0,
                'brain_region': 'cortex',
                'heat': round(0.1 * ent, 3),  # small base for untouched
            }

    heat_path = root / HEAT_STORE
    heat_path.write_text(json.dumps(heat, indent=2), encoding='utf-8')

    brain_path = root / COPILOT_BRAIN_STORE
    brain_path.parent.mkdir(parents=True, exist_ok=True)
    brain_path.write_text(json.dumps(brain, indent=2), encoding='utf-8')


def _module_key(raw_file: str) -> str:
    stem = Path(raw_file).stem
    mod = re.split(r'_s(?:eq)?\d{3}', stem)[0]
    return mod or stem


def _region_from_path(raw_file: str) -> str:
    folder = str(Path(raw_file).parent).replace('\\', '/')
    if folder.startswith('src/cognitive_reactor'):
        return 'motor'
    if folder.startswith('src/copilot_prompt_manager'):
        return 'language'
    if folder.startswith('src/cognitive'):
        return 'consciousness'
    if folder.startswith('src'):
        return 'cortex'
    if folder.startswith('pigeon_brain'):
        return 'stem'
    if folder.startswith('pigeon_compiler/rename_engine'):
        return 'naming'
    if folder.startswith('pigeon_compiler/cut_executor'):
        return 'spatial'
    if folder.startswith('pigeon_compiler/state_extractor') or folder.startswith('pigeon_compiler/bones'):
        return 'analysis'
    if folder.startswith('pigeon_compiler/runners'):
        return 'coordination'
    if folder.startswith('streaming_layer'):
        return 'transport'
    return 'cortex'


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


def _count_copilot_touches(root: Path, events: list[dict] | None = None) -> dict[str, float]:
    """Count Copilot file touches from edit_pairs.jsonl with time decay."""
    if events is None:
        events = _load_edit_events(root)
    if not events:
        return {}

    now = datetime.now(timezone.utc)
    scores: dict[str, float] = {}

    try:
        for entry in events:
            mod = entry['module']
            # Time decay
            ts = entry.get('edit_ts', '')
            try:
                edit_time = datetime.fromisoformat(ts)
                age_s = (now - edit_time).total_seconds()
            except Exception:
                age_s = DECAY_HALF_LIFE * 2  # old if unparseable

            weight = math.exp(-0.693 * age_s / DECAY_HALF_LIFE)
            scores[mod] = scores.get(mod, 0.0) + weight
    except Exception:
        pass

    return scores


def _build_copilot_brain_map(root: Path, events: list[dict], touches: dict[str, float]) -> dict:
    """Build a brain-style entropy map from Copilot edits only.

    Signals are exclusively derived from harvested Copilot edits:
    - prompt→edit latency
    - quick retouches to the same module
    - cognitive state at edit time
    - edit-reason diversity
    """
    by_module: dict[str, list[dict]] = {}
    for event in events:
        by_module.setdefault(event['module'], []).append(event)

    modules = {}
    regions: dict[str, dict] = {}
    now = datetime.now(timezone.utc).isoformat()

    for mod, rows in by_module.items():
        rows.sort(key=lambda row: row.get('edit_ts', ''))
        latencies = [row['latency_ms'] for row in rows if row.get('latency_ms', 0) >= 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        latency_score = min(avg_latency / HIGH_LATENCY_MS, 1.0)

        quick_retouches = 0
        for prev, curr in zip(rows, rows[1:]):
            try:
                prev_ts = datetime.fromisoformat(prev['edit_ts'])
                curr_ts = datetime.fromisoformat(curr['edit_ts'])
                if (curr_ts - prev_ts).total_seconds() <= QUICK_RETOUCH_S:
                    quick_retouches += 1
            except Exception:
                continue
        retouch_score = min(quick_retouches / max(len(rows) - 1, 1), 1.0) if len(rows) > 1 else 0.0

        state_counts: dict[str, int] = {}
        for row in rows:
            state = row.get('state', 'unknown') or 'unknown'
            state_counts[state] = state_counts.get(state, 0) + 1
        state_scores = [STATE_ENTROPY.get(row.get('state', 'unknown'), STATE_ENTROPY['unknown']) for row in rows]
        state_score = sum(state_scores) / len(state_scores) if state_scores else 0.0

        reasons = {row.get('edit_why', 'auto') for row in rows if row.get('edit_why') and row.get('edit_why') != 'auto'}
        reason_score = min(len(reasons) / max(len(rows), 1), 1.0)

        edit_entropy = min(
            1.0,
            latency_score * 0.4 + retouch_score * 0.25 + state_score * 0.2 + reason_score * 0.15,
        )
        confidence = max(0.0, 1.0 - edit_entropy)
        region = rows[-1].get('region', 'cortex')
        touch_score = touches.get(mod, 0.0)
        brain_heat = touch_score * (1 + edit_entropy)

        modules[mod] = {
            'region': region,
            'event_count': len(rows),
            'touch_score': round(touch_score, 3),
            'avg_latency_ms': round(avg_latency),
            'quick_retouches': quick_retouches,
            'reason_count': len(reasons),
            'edit_entropy': round(edit_entropy, 3),
            'confidence': round(confidence, 3),
            'brain_heat': round(brain_heat, 3),
            'dominant_state': max(state_counts, key=state_counts.get) if state_counts else 'unknown',
            'latest_file': rows[-1].get('file', ''),
        }

        region_bucket = regions.setdefault(region, {
            'module_count': 0,
            'total_entropy': 0.0,
            'total_heat': 0.0,
            'modules': [],
        })
        region_bucket['module_count'] += 1
        region_bucket['total_entropy'] += edit_entropy
        region_bucket['total_heat'] += brain_heat
        region_bucket['modules'].append(mod)

    for region, bucket in regions.items():
        bucket['avg_entropy'] = round(bucket['total_entropy'] / max(bucket['module_count'], 1), 3)
        bucket['brain_heat'] = round(bucket['total_heat'], 3)
        bucket['modules'] = sorted(bucket['modules'])[:12]
        del bucket['total_entropy']
        del bucket['total_heat']

    top_modules = [
        {'module': mod, **data}
        for mod, data in sorted(modules.items(), key=lambda item: (-item[1]['brain_heat'], -item[1]['edit_entropy'], item[0]))[:15]
    ]
    hot_regions = [
        {'region': region, **data}
        for region, data in sorted(regions.items(), key=lambda item: (-item[1]['brain_heat'], -item[1]['avg_entropy'], item[0]))
    ]

    global_avg = sum(data['edit_entropy'] for data in modules.values()) / max(len(modules), 1) if modules else 0.0
    return {
        'generated': now,
        'source': 'copilot_edits_only',
        'total_events': len(events),
        'modules_tracked': len(modules),
        'global_avg_edit_entropy': round(global_avg, 3),
        'top_modules': top_modules,
        'regions': hot_regions,
        'modules': modules,
    }


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
