"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_brain_map_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 110 lines | ~1,164 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import re

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
