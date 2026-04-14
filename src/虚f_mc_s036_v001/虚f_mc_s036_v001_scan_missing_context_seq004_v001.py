"""虚f_mc_s036_v001_scan_missing_context_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 64 lines | ~587 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from src.虚f_mc_s036_v001_llm import (
    get_api_key, build_void_prompt, call_gemini, parse_blocks,
)
from src.虚f_mc_s036_v001_profile import (
    top_hesitation_files, build_file_profile,
)
import json

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
