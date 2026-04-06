"""Generate per-push narrative: each changed file speaks as its own agent."""


import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def generate_push_narrative(
    root: Path, intent: str, commit_hash: str, changed_py: list[str],
    registry: dict, rework_stats: dict | None = None,
    query_mem: dict | None = None, heat_map: dict | None = None,
    cross_context: dict | None = None,
) -> Path | None:
    """Build a narrative from file-agent voices → docs/push_narratives/."""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key or not changed_py:
        return None

    # Cap file briefs to avoid massive prompts that timeout
    file_briefs = _build_file_briefs(root, changed_py[:20], registry)
    if not file_briefs:
        return None

    # Load operator composition data for this session
    comp_snapshot = _load_composition_snapshot(root)

    prompt = _build_narrative_prompt(
        intent, file_briefs, rework_stats, query_mem,
        heat_map, cross_context, comp_snapshot)
    prose = _call_deepseek(prompt, api_key)
    if not prose:
        return None

    out_dir = root / 'docs' / 'push_narratives'
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out_path = out_dir / f'{today}_{commit_hash}.md'

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    fl = '\n'.join(f'- `{b["path"]}`' for b in file_briefs)
    dw = comp_snapshot.get('deleted_words', []) if comp_snapshot else []
    dw_l = f'**Deleted words**: {", ".join(dw[:10])}  \n' if dw else ''
    hdr = (f'# Push Narrative — {commit_hash}\n\n**Intent**: {intent}  \n'
           f'**Date**: {now}  \n**Files**: {len(changed_py)}  \n{dw_l}\n{fl}\n\n---\n\n')
    out_path.write_text(hdr + prose + '\n', encoding='utf-8')
    return out_path


def _load_composition_snapshot(root: Path) -> dict | None:
    log = root / 'logs' / 'prompt_compositions.jsonl'
    if not log.exists(): return None
    try:
        lines = log.read_text(encoding='utf-8').strip().splitlines()
        return json.loads(lines[-1]) if lines else None
    except Exception: return None

def _build_file_briefs(root: Path, changed_py: list[str], registry: dict) -> list[dict]:
    briefs = []
    for rel in changed_py:
        entry = registry.get(rel)
        if entry:
            briefs.append({
                'name': entry.get('name', Path(rel).stem),
                'path': rel,
                'seq': entry.get('seq', '?'),
                'ver': entry.get('ver', 0),
                'desc': entry.get('desc', ''),
                'intent': entry.get('intent', ''),
                'tokens': entry.get('tokens', 0),
                'history_len': len(entry.get('history', [])),
            })
        else:
            p = root / rel
            try: tokens = max(1, len(p.read_text(encoding='utf-8')) // 4) if p.exists() else 0
            except Exception: tokens = 0
            briefs.append({'name': Path(rel).stem, 'path': rel, 'seq': '-',
                           'ver': 0, 'desc': rel, 'intent': '',
                           'tokens': tokens, 'history_len': 0})
    return briefs


def _build_narrative_prompt(
    intent: str,
    file_briefs: list[dict],
    rework_stats: dict | None,
    query_mem: dict | None,
    heat_map: dict | None,
    cross_context: dict | None = None,
    composition: dict | None = None,
) -> str:
    def _brief_line(b):
        seq = b['seq']
        ver = b['ver']
        tag = f'seq{seq:03d} v{ver:03d}' if isinstance(seq, int) else b['path']
        return (f'- **{b["name"]}** ({tag}, {b["tokens"]}tok): '
                f'desc="{b["desc"]}", last_intent="{b["intent"]}", '
                f'{b["history_len"]} versions')

    files_block = '\n'.join(_brief_line(b) for b in file_briefs)

    signals = []
    if rework_stats:
        signals.append(f'Rework: miss_rate={rework_stats.get("miss_rate", 0)}, '
                       f'worst={rework_stats.get("worst_queries", [])}')
    if query_mem:
        gaps = query_mem.get('persistent_gaps', [])
        abandons = query_mem.get('recent_abandons', [])
        if gaps:
            signals.append(f'Recurring queries: {[g.get("query", "") for g in gaps[:3]]}')
        if abandons:
            signals.append(f'Recent abandons: {abandons[:3]}')
    if heat_map:
        complex_files = heat_map.get('complex_files', [])
        if complex_files:
            signals.append(f'High-hesitation files: {[c["module"] for c in complex_files[:3]]}')

    signals_block = '\n'.join(signals) if signals else 'No deep signals available yet.'

    # Cross-file dependency context
    cross_block = ''
    if cross_context:
        cross_lines = []
        for rel, ctx in cross_context.items():
            name = Path(rel).stem.split('_seq')[0]
            deps = ', '.join(Path(d).stem.split('_seq')[0] for d in ctx.get('imports_from', []))
            users = ', '.join(Path(u).stem.split('_seq')[0] for u in ctx.get('imported_by', []))
            parts = ([f'depends on [{deps}]'] if deps else []) + ([f'used by [{users}]'] if users else [])
            if parts: cross_lines.append(f'- {name}: {"; ".join(parts)}')
        if cross_lines: cross_block = '\n\nCROSS-FILE DEPS:\n' + '\n'.join(cross_lines)

    # Composition: what the operator deleted/rewrote while building this commit
    comp_block = ''
    if composition:
        dw = composition.get('deleted_words', [])
        dr = composition.get('deletion_ratio', 0)
        rw = composition.get('rewrites', 0)
        state = composition.get('chat_state', {}).get('state', '?')
        comp_parts = [f'cognitive_state={state}, deletion_ratio={dr}, rewrites={rw}']
        if dw:
            comp_parts.append(f'deleted_words={dw[:8]}')
        comp_block = '\n\nOPERATOR COMPOSITION (what they typed then deleted while writing this commit):\n' + ', '.join(comp_parts)

    return (
        f'You are writing a debugging-grade development narrative for a code push.\n\n'
        f'COMMIT INTENT: {intent}\n\n'
        f'FILES CHANGED:\n{files_block}\n\n'
        f'OPERATOR DEEP SIGNALS:\n{signals_block}{cross_block}{comp_block}\n\n'
        f'INSTRUCTIONS:\n'
        f'Write a development narrative (200-350 words) optimized for future debugging. '
        f'Each changed file "speaks" in first person — one paragraph each — '
        f'explaining: (1) why it was touched, (2) what assumption it makes that '
        f'could break, (3) one specific regression to watch for. '
        f'If cross-file dependencies exist, each file names what it gives/receives '
        f'and the exact failure mode if that contract changes. '
        f'If operator composition data shows deleted words or high deletion ratio, '
        f'note what the operator was struggling with — their hesitation IS signal. '
        f'End with: a 1-line "REGRESSION WATCHLIST" of the 3 most fragile points '
        f'in this push, and a 1-sentence summary of what this push accomplishes. '
        f'Use direct, technical prose. No markdown headers — just paragraphs.'
    )


def _call_deepseek(prompt: str, api_key: str) -> str | None:
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 800,
        'temperature': 0.45,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'  [push_narrative] DeepSeek call failed: {type(e).__name__}: {e}')
        return None
