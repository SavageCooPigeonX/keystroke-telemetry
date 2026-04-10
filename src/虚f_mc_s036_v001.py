"""虚f_mc — Missing context scanner (void detector for code).

Asks files what they don't know. Each high-hesitation file gets its full
profile loaded — source, bugs, entropy, coupling, fix history, death records —
and an LLM call asks the file to declare its own knowledge gaps.

Aggregates missing context blocks across files to detect ARCHITECTURAL VOIDS
(multiple files needing the same missing context = design gap, not a bug).
Auto-generates wiring tasks from missing context blocks.

Glyph: 虚 (xū) = void / emptiness — the gap is always the product.
"""
from __future__ import annotations

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-09T03:50:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  split into 3 pigeon-compliant files
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ensure workspace root is on path for both CLI and import usage
_WS = Path(__file__).resolve().parent.parent
if str(_WS) not in sys.path:
    sys.path.insert(0, str(_WS))

from src.虚f_mc_s036_v001_profile import (
    top_hesitation_files, build_file_profile,
)
from src.虚f_mc_s036_v001_llm import (
    get_api_key, build_void_prompt, call_gemini, parse_blocks,
)

HESITATION_THRESHOLD = 0.5
MAX_FILES_PER_SCAN = 15
OUTPUT_FILE = 'logs/missing_context.json'


# ── aggregation ──────────────────────────────


def _detect_voids(all_blocks: dict[str, list[dict]]) -> list[dict]:
    source_requests: dict[str, list[dict]] = defaultdict(list)
    for file_name, blocks in all_blocks.items():
        for b in blocks:
            who = b.get('who_has_it', '').strip()
            if who:
                source_requests[who].append({
                    'requester': file_name,
                    'what': b['what'],
                    'confidence': b['confidence'],
                    'type': b['type'],
                })

    voids = []
    for source_module, requests in source_requests.items():
        if len(requests) >= 2:
            avg_conf = sum(r['confidence'] for r in requests) / len(requests)
            voids.append({
                'source_module': source_module,
                'void_score': len(requests),
                'avg_confidence': round(avg_conf, 3),
                'requesters': requests,
                'diagnosis': (
                    f'{source_module} is a SILO — {len(requests)} files need data '
                    f'from it but none have access. Architectural integration gap.'
                ),
            })
    return sorted(voids, key=lambda v: v['void_score'], reverse=True)


def _generate_tasks(root: Path, all_blocks: dict[str, list[dict]],
                    voids: list[dict]) -> list[dict]:
    add_task = None
    try:
        from src._resolve import src_import
        add_task = src_import('task_queue_seq018', 'add_task')
    except Exception:
        try:
            import importlib
            for f in (root / 'src').glob('*tq*s018*.py'):
                spec = importlib.util.spec_from_file_location('tq', f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                add_task = getattr(mod, 'add_task', None)
                break
        except Exception:
            pass

    tasks = []
    for void in voids:
        title = f'Wire {void["source_module"]} data to {void["void_score"]} consumers'
        focus = [void['source_module']] + [r['requester'] for r in void['requesters'][:3]]
        tid = None
        if add_task:
            try:
                tid = add_task(root, title=title, intent='integration',
                               stage='pending', focus_files=focus)
            except Exception:
                pass
        tasks.append({
            'task_id': tid, 'title': title, 'source': 'void_detection',
            'void_score': void['void_score'], 'focus_files': focus,
            'priority': 'HIGH' if void['void_score'] >= 3 else 'MEDIUM',
        })

    for file_name, blocks in all_blocks.items():
        for b in blocks:
            if b['confidence'] < 0.7 or b.get('type') == 'self_knowledge_gap':
                continue
            who = b.get('who_has_it', '').split(',')[0].split('(')[0].strip()[:40]
            if any(who == v['source_module'] for v in voids):
                continue
            title = f'{file_name}: {b["what"][:50]}'
            tid = None
            if add_task:
                try:
                    tid = add_task(root, title=title, intent='integration',
                                   stage='pending',
                                   focus_files=[file_name, who] if who else [file_name])
                except Exception:
                    pass
            tasks.append({
                'task_id': tid, 'title': title, 'source': 'missing_context',
                'confidence': b['confidence'], 'type': b['type'],
                'focus_files': [file_name, who] if who else [file_name],
                'priority': 'HIGH' if b['confidence'] >= 0.85 else 'MEDIUM',
            })
    return tasks


# ── orchestrator ─────────────────────────────


def scan_missing_context(root: Path, *, dry_run: bool = False) -> dict:
    root = Path(root)
    api_key = get_api_key(root)
    if not api_key and not dry_run:
        return {'error': 'no GEMINI_API_KEY found', 'files_scanned': 0}

    targets = top_hesitation_files(root, HESITATION_THRESHOLD, MAX_FILES_PER_SCAN)
    if not targets:
        return {'files_scanned': 0, 'blocks': {}, 'voids': [], 'tasks': []}

    all_blocks: dict[str, list[dict]] = {}
    errors = []

    for t in targets:
        module = t['module']
        profile = build_file_profile(root, module, t['avg_hes'])
        if dry_run:
            all_blocks[module] = [{'what': '(dry run)', 'why': '', 'who_has_it': '',
                                   'confidence': 0, 'type': 'dry_run'}]
            continue
        prompt = build_void_prompt(module, profile)
        try:
            raw = call_gemini(api_key, prompt)
            all_blocks[module] = parse_blocks(raw)
        except Exception as e:
            errors.append({'module': module, 'error': str(e)})
            all_blocks[module] = []

    voids = _detect_voids(all_blocks)
    tasks = _generate_tasks(root, all_blocks, voids) if not dry_run else []

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'files_scanned': len(targets),
        'total_blocks': sum(len(b) for b in all_blocks.values()),
        'total_voids': len(voids),
        'total_tasks': len(tasks),
        'per_file': {
            name: {
                'hesitation': next((t['avg_hes'] for t in targets if t['module'] == name), 0),
                'missing_context': blocks,
            }
            for name, blocks in all_blocks.items()
        },
        'voids': voids,
        'tasks': tasks,
        'errors': errors,
    }

    out_path = root / OUTPUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    result = scan_missing_context(_WS, dry_run=dry)
    scanned = result.get('files_scanned', 0)
    blocks = result.get('total_blocks', 0)
    voids_n = result.get('total_voids', 0)
    tasks_n = result.get('total_tasks', 0)
    print(f'虚 void scan: {scanned} files → {blocks} missing context blocks → {voids_n} voids → {tasks_n} tasks')
    if result.get('voids'):
        for v in result['voids']:
            print(f'  VOID: {v["source_module"]} (score={v["void_score"]}) — {v["diagnosis"][:80]}')
    if result.get('errors'):
        for e in result['errors']:
            print(f'  ERR: {e["module"]}: {e["error"][:60]}')
