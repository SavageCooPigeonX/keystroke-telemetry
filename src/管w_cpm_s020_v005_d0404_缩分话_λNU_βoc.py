"""Copilot prompt manager — thin orchestrator. Builders in src/管_cpm_s020/ sub-files.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# sub-module re-exports (src/__init__.py imports these by name)
from src.管_cpm_s020.管w_cpm_bvx_s013_v001 import inject_bug_voices
from src.管_cpm_s020.管w_cpm_ops_s014_v001 import inject_operator_state, inject_entropy_layers
from src.管_cpm_s020.管w_cpm_rmp_s016_v001 import refresh_managed_prompt

COPILOT_PATH = '.github/copilot-instructions.md'
SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'
AUDIT_PATH = 'logs/copilot_prompt_audit.json'
PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'
PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'

BLOCK_MARKERS = {
    'task_context': ('<!-- pigeon:task-context -->', '<!-- /pigeon:task-context -->'),
    'task_queue': ('<!-- pigeon:task-queue -->', '<!-- /pigeon:task-queue -->'),
    'operator_state': ('<!-- pigeon:operator-state -->', '<!-- /pigeon:operator-state -->'),
    'prompt_telemetry': (PROMPT_BLOCK_START, PROMPT_BLOCK_END),
    'entropy_map': ('<!-- pigeon:entropy-map -->', '<!-- /pigeon:entropy-map -->'),
    'entropy_red_layer': ('<!-- pigeon:entropy-red-layer -->', '<!-- /pigeon:entropy-red-layer -->'),
    'auto_index': ('<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->'),
    'bug_voices': ('<!-- pigeon:bug-voices -->', '<!-- /pigeon:bug-voices -->'),
    'probe_resolutions': ('<!-- pigeon:probe-resolutions -->', '<!-- /pigeon:probe-resolutions -->'),
}

# ── core utilities ─────────────────────────────────────────────────────────────

def _block_pattern(start: str, end: str) -> re.Pattern[str]:
    return re.compile(rf'(?ms)^\s*{re.escape(start)}\s*$\n.*?^\s*{re.escape(end)}\s*$')


def _extract_block(text: str, start: str, end: str) -> str | None:
    match = _block_pattern(start, end).search(text)
    return match.group(0) if match else None


def _count_blocks(text: str, start: str, end: str) -> int:
    return len(_block_pattern(start, end).findall(text))


def _replace_or_insert_after_line(text: str, anchor: str, block: str) -> str:
    anchor_pattern = re.compile(rf'(?m)^\s*{re.escape(anchor)}\s*$')
    match = anchor_pattern.search(text)
    if not match:
        return text.rstrip() + '\n\n' + block + '\n'
    insert_at = match.end()
    return text[:insert_at] + '\n\n' + block + text[insert_at:]


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _render_prompt_block(snapshot: dict) -> str:
    return (
        f'{PROMPT_BLOCK_START}\n'
        '## Live Prompt Telemetry\n\n'
        f'*Auto-updated per prompt · source: `{SNAPSHOT_PATH}`*\n\n'
        'Use this block as the highest-freshness prompt-level telemetry. '
        'When it conflicts with older commit-time context, prefer this block.\n\n'
        '```json\n'
        f'{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n'
        '```\n\n'
        f'{PROMPT_BLOCK_END}'
    )


def _upsert_block(text: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    pattern = _block_pattern(start, end)
    if pattern.search(text):
        return pattern.sub(block, text)
    if anchor and anchor in text:
        return _replace_or_insert_after_line(text, anchor, block)
    return text.rstrip() + '\n\n' + block + '\n'


def inject_prompt_telemetry(root: Path, snapshot: dict | None = None) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    if snapshot is None:
        snapshot = _load_json(root / SNAPSHOT_PATH)
    if not snapshot:
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _render_prompt_block(snapshot)
    new_text = _upsert_block(
        text, PROMPT_BLOCK_START, PROMPT_BLOCK_END, block,
        anchor='<!-- /pigeon:operator-state -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_auto_index(root: Path, registry: dict | None = None, processed: int = 0) -> bool:
    from src.管_cpm_s020.管w_cpm_idx_s012_v001 import _build_auto_index_block
    cp_path = root / COPILOT_PATH
    if not cp_path.exists() or not registry:
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_auto_index_block(root, registry, processed)
    new_text = _upsert_block(text, '<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->', block)
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def audit_copilot_prompt(root: Path) -> dict:
    cp_path = root / COPILOT_PATH
    snapshot = _load_json(root / SNAPSHOT_PATH) or {}
    mutations = _load_json(root / 'logs' / 'copilot_prompt_mutations.json') or {}
    queue = _load_json(root / 'task_queue.json') or {}

    if not cp_path.exists():
        result = {
            'generated': datetime.now(timezone.utc).isoformat(),
            'missing_file': True,
            'missing_blocks': list(BLOCK_MARKERS.keys()),
            'unfilled_fields': ['copilot_instructions_missing'],
        }
        out_path = root / AUDIT_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return result

    text = cp_path.read_text(encoding='utf-8')
    block_status = {}
    missing_blocks = []
    duplicate_blocks = []
    unfilled_fields = []
    extracted_blocks = {}

    for name, (start, end) in BLOCK_MARKERS.items():
        body = _extract_block(text, start, end)
        present = body is not None
        count = _count_blocks(text, start, end)
        block_status[name] = {'present': present, 'count': count}
        extracted_blocks[name] = body or ''
        if not present:
            missing_blocks.append(name)
        elif count > 1:
            duplicate_blocks.append(name)

    if 'Fresh start' in extracted_blocks.get('task_context', ''):
        unfilled_fields.append('task_context_placeholder')
    if 'Fresh start' in extracted_blocks.get('operator_state', ''):
        unfilled_fields.append('operator_state_placeholder')
    if 'Fresh start' in extracted_blocks.get('task_queue', '') and queue.get('tasks'):
        unfilled_fields.append('task_queue_not_reflecting_tasks')
    if block_status.get('prompt_telemetry', {}).get('present'):
        latest_preview = (((snapshot.get('latest_prompt') or {}).get('preview')) or '').strip()
        if latest_preview and latest_preview not in text:
            unfilled_fields.append('prompt_telemetry_stale')
    else:
        unfilled_fields.append('prompt_telemetry_missing')

    total_mutations = mutations.get('total_mutations', 0) if isinstance(mutations, dict) else 0
    if total_mutations == 0:
        unfilled_fields.append('mutation_tracking_empty')

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'missing_file': False,
        'blocks': block_status,
        'missing_blocks': missing_blocks,
        'duplicate_blocks': duplicate_blocks,
        'unfilled_fields': unfilled_fields,
        'mutation_snapshots': total_mutations,
        'latest_prompt_preview': ((snapshot.get('latest_prompt') or {}).get('preview')),
    }
    out_path = root / AUDIT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    result = refresh_managed_prompt(root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
