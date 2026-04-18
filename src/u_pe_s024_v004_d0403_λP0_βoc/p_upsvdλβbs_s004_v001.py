"""u_pe_s024_v004_d0403_λP0_βoc_bug_scoring_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import os
import re
from .p_upsvdλβu_s002_v001 import _jload, _jsonl
from .p_upsvdλβdl_s003_v001 import _hot_files

def _score_bug_dossiers(root: Path, query: str, open_files: list | None = None) -> list[dict]:
    """Multi-signal scorer: query text + editor files + hot modules + rework overlap."""
    reg = _jload(root / 'pigeon_registry.json')
    if not reg: return []
    files = reg if isinstance(reg, list) else reg.get('files', [])
    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w{3,}\b', query_lower))
    bug_signals = {'bug', 'fix', 'broke', 'broken', 'error', 'fail', 'crash',
                   'import', 'stale', 'wrong', 'missing', 'dead', 'overcap',
                   'split', 'cap', 'rename', 'fallout', 'demon', 'hurt'}
    is_bug_prompt = bool(query_words & bug_signals)
    # Signal 2: open editor files
    open_stems = set()
    for f in (open_files or []):
        open_stems.add(Path(f).stem.split('_seq')[0].split('_s0')[0].split('_s1')[0])
    # Signal 3: hot modules
    hot_names = set()
    hot_data = _hot_files(root, top_n=8)
    for h in hot_data:
        hot_names.add(h['file'].split('_seq')[0].split('_s0')[0].split('_s1')[0])
    scored = []
    for f in files:
        bugs = f.get('bug_keys') or []
        if not bugs: continue
        name = f.get('file', '') or f.get('desc', '')
        name_lower = name.lower()
        name_parts = set(name_lower.split('_'))
        name_stem = name_lower.split('_seq')[0].split('_s0')[0].split('_s1')[0]
        score = 0.0
        # Signal 1: query word overlap with module name
        name_overlap = sum(1 for p in name_parts if len(p) > 3 and p in query_lower)
        score += name_overlap * 0.3
        if is_bug_prompt: score += 0.15
        # Signal 2: file is open in editor
        if name_stem in open_stems: score += 0.35
        # Signal 3: file is cognitively hot
        if name_stem in hot_names: score += 0.2
        # Signal 4: bug recurrence (persistent demons score higher)
        counts = f.get('bug_counts', {})
        recur = sum(counts.values()) if counts else 0
        if recur >= 3: score += 0.15
        elif recur >= 2: score += 0.1
        # Signal 5: rework feedback from registry
        dossier_score = f.get('dossier_score', 0)
        score += dossier_score * 0.2
        if score > 0:
            scored.append({
                'file': name, 'bugs': bugs, 'score': round(score, 3),
                'entity': f.get('bug_entity', ''), 'recur': recur,
                'counts': counts, 'last_mark': f.get('last_bug_mark', ''),
                'last_change': f.get('last_change', ''),
            })
    scored.sort(key=lambda x: -x['score'])
    return scored
