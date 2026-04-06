"""copilot_prompt_manager_seq020_audit_decomposed_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

from datetime import datetime, timezone
from pathlib import Path
import json
import re

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
    unfilled_fields = []
    extracted_blocks = {}

    for name, (start, end) in BLOCK_MARKERS.items():
        body = _extract_block(text, start, end)
        present = body is not None
        block_status[name] = {'present': present}
        extracted_blocks[name] = body or ''
        if not present:
            missing_blocks.append(name)

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
        'unfilled_fields': unfilled_fields,
        'mutation_snapshots': total_mutations,
        'latest_prompt_preview': ((snapshot.get('latest_prompt') or {}).get('preview')),
    }
    out_path = root / AUDIT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return result
