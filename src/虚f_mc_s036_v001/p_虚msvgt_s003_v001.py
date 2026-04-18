"""虚f_mc_s036_v001_generate_tasks_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 61 lines | ~650 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

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
