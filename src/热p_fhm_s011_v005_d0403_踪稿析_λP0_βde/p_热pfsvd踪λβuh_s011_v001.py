"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_update_heat_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 58 lines | ~580 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

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
