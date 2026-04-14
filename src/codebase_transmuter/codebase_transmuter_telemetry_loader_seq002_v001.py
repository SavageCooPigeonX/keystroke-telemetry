"""codebase_transmuter_telemetry_loader_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 96 lines | ~1,031 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter, defaultdict
from pathlib import Path
import json
import re

def _load_telemetry(root):
    """Returns {module_name: {H, R, E, C, B, T, mood, demons}} for every known module."""
    telem = defaultdict(lambda: {'H': 0.0, 'R': 0.0, 'E': 0.0, 'C': 0.0, 'B': 0,
                                  'T': 0, 'mood': 'neutral', 'demons': []})

    # 1. heat map → E (operator hesitation per module)
    hm_path = root / 'file_heat_map.json'
    if hm_path.exists():
        hm = json.loads(hm_path.read_text('utf-8', errors='ignore'))
        for mod, data in hm.items():
            samples = data if isinstance(data, list) else data.get('samples', [])
            if samples:
                avg_hes = sum(s.get('hes', 0) for s in samples) / len(samples)
                telem[mod]['E'] = round(avg_hes, 3)

    # 2. entropy map → H (copilot uncertainty per module)
    em_path = root / 'logs' / 'entropy_map.json'
    if em_path.exists():
        em = json.loads(em_path.read_text('utf-8', errors='ignore'))
        for m in em.get('top_entropy_modules', []):
            telem[m['module']]['H'] = round(m.get('avg_entropy', 0), 3)

    # 3. rework log → R (aggregate rework rate per mentioned module)
    rw_path = root / 'rework_log.json'
    if rw_path.exists():
        rw = json.loads(rw_path.read_text('utf-8', errors='ignore'))
        if isinstance(rw, list):
            mod_rework = defaultdict(list)
            for entry in rw:
                hint = entry.get('query_hint', '')
                score = entry.get('rework_score', 0)
                # extract module refs from query hint
                words = re.findall(r'[a-zA-Z_]\w+', hint)
                for w in words:
                    if len(w) > 3:
                        mod_rework[w].append(score)
            for mod, scores in mod_rework.items():
                telem[mod]['R'] = round(sum(scores) / len(scores), 3)

    # 4. file profiles → C (coupling score)
    fp_path = root / 'file_profiles.json'
    if fp_path.exists():
        fp = json.loads(fp_path.read_text('utf-8', errors='ignore'))
        for mod, data in fp.items():
            partners = data.get('partners', [])
            if partners:
                avg_couple = sum(p.get('score', 0) for p in partners) / len(partners)
                telem[mod]['C'] = round(avg_couple, 3)

    # 5. bug profiles → B (bug count + demon names)
    bp_path = root / 'logs' / 'bug_profiles.json'
    if bp_path.exists():
        bp = json.loads(bp_path.read_text('utf-8', errors='ignore'))
        for mod, data in bp.get('all_modules', {}).items():
            bug_keys = data.get('bug_keys', [])
            entities = data.get('bug_entities', {})
            telem[mod]['B'] = len(bug_keys)
            telem[mod]['demons'] = [f"{k}:{entities.get(k, k)}" for k in bug_keys]

    # 6. copilot touch count → T (accumulated entropy from copilot edits)
    ep_path = root / 'logs' / 'edit_pairs.jsonl'
    if ep_path.exists():
        for line in ep_path.read_text('utf-8', errors='ignore').splitlines():
            try:
                entry = json.loads(line)
                f = entry.get('file', '')
                stem = Path(f).stem
                base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', stem)
                telem[base]['T'] += 1
            except Exception:
                continue

    # derive mood from signals — T enters as normalized copilot entropy
    for mod, t in telem.items():
        t_norm = min(t['T'] / 10.0, 1.0)  # 10+ touches = max entropy
        danger = (t['H'] * 0.25 + t['R'] * 0.15 + t['E'] * 0.2 +
                  t['C'] * 0.1 + min(t['B'] * 0.1, 0.1) + t_norm * 0.2)
        if danger > 0.5:
            t['mood'] = 'unhinged'
        elif danger > 0.35:
            t['mood'] = 'paranoid'
        elif danger > 0.2:
            t['mood'] = 'anxious'
        elif danger > 0.1:
            t['mood'] = 'cautious'
        else:
            t['mood'] = 'chill'
        t['danger'] = round(danger, 3)

    return dict(telem)
