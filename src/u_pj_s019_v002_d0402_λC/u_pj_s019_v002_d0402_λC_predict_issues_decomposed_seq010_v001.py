"""u_pj_s019_v002_d0402_λC_predict_issues_decomposed_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _predict_next_issues(root: Path, current_intent: str, current_refs: list[str]) -> list[dict]:
    """Analyze prompt journal history to predict what the operator will debug next.

    Pattern mining:
    1. After frustrated/hesitant states, which modules come up in the NEXT 3 prompts?
    2. Recurring module→debug cycles (touched module X → debugged X within 5 prompts)
    3. Modules with high heat + recent mention = likely next struggle
    """
    entries = _read_jsonl(root / JOURNAL_PATH)
    if len(entries) < 10:
        return []

    from collections import Counter
    # Pattern 1: modules that follow frustrated states
    post_frustration_modules: Counter = Counter()
    for i, e in enumerate(entries):
        if e.get('cognitive_state') in ('frustrated', 'hesitant'):
            for j in range(i + 1, min(i + 4, len(entries))):
                for ref in entries[j].get('module_refs', []):
                    post_frustration_modules[ref] += 1

    # Pattern 2: debug cycles — implement/build → debug same module
    debug_cycles: Counter = Counter()
    for i, e in enumerate(entries):
        if e.get('intent') in ('building', 'restructuring'):
            refs = set(e.get('module_refs', []))
            for j in range(i + 1, min(i + 6, len(entries))):
                if entries[j].get('intent') == 'debugging':
                    for ref in entries[j].get('module_refs', []):
                        if ref in refs:
                            debug_cycles[ref] += 1

    # Pattern 3: recent module mentions trending toward frustration
    recent = entries[-15:]
    recent_refs: Counter = Counter()
    for e in recent:
        weight = 2 if e.get('cognitive_state') in ('frustrated', 'hesitant') else 1
        for ref in e.get('module_refs', []):
            recent_refs[ref] += weight

    # Merge signals — score each module
    all_modules = set(post_frustration_modules) | set(debug_cycles) | set(recent_refs)
    predictions = []
    heat = {m['module']: m['hes'] for m in _hot_modules(root, top_n=20)}
    for mod in all_modules:
        score = (
            post_frustration_modules.get(mod, 0) * 0.3 +
            debug_cycles.get(mod, 0) * 0.5 +
            recent_refs.get(mod, 0) * 0.2 +
            heat.get(mod, 0) * 2.0
        )
        if score >= 1.0:
            reasons = []
            if debug_cycles.get(mod, 0) >= 2:
                reasons.append(f'{debug_cycles[mod]}x build→debug cycle')
            if post_frustration_modules.get(mod, 0) >= 2:
                reasons.append(f'follows frustration {post_frustration_modules[mod]}x')
            if heat.get(mod, 0) >= 0.5:
                reasons.append(f'high heat ({heat[mod]:.2f})')
            if recent_refs.get(mod, 0) >= 3:
                reasons.append('trending in recent prompts')
            predictions.append({'module': mod, 'score': round(score, 2), 'reasons': reasons})

    predictions.sort(key=lambda p: p['score'], reverse=True)
    return predictions[:4]
