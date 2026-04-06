"""cognitive_reactor_seq014_reactor_core_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re

def _fire_reactor(
    root: Path,
    module_key: str,
    streak: dict,
    timestamp: str,
) -> dict:
    """Autonomous code analysis + patch generation for a struggling module."""
    import importlib.util

    avg_hes = round(streak['total_hes'] / max(streak['count'], 1), 3)
    dominant_state = max(set(streak['states']), key=streak['states'].count)

    # Load registry to find the actual file
    reg_path = root / 'pigeon_registry.json'
    registry = {}
    target_file = None
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text('utf-8'))
            files = reg.get('files', [])
            for entry in files:
                p = entry.get('path', '')
                name = entry.get('name', '')
                if name == module_key or module_key in p:
                    target_file = entry
                    break
            registry = reg
        except Exception:
            pass

    # Run self-fix focused on this module
    problems = []
    cross_context = {}
    try:
        matches = sorted(root.glob('src/修f_sf_s013*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('sf', matches[-1])
            sf = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sf)
            report = sf.run_self_fix(root, registry,
                                     changed_py=[target_file['path']] if target_file else None)
            problems = [p for p in report.get('problems', [])
                        if module_key in p.get('file', '')]
            cross_context = report.get('cross_context', {})
    except Exception:
        pass

    # Read the actual source of the struggling file
    source_snippet = ''
    if target_file:
        fp = root / target_file['path']
        if fp.exists():
            try:
                lines = fp.read_text('utf-8').splitlines()
                source_snippet = '\n'.join(lines[:80])  # first 80 lines
            except Exception:
                pass

    # Generate cognitive patch via DeepSeek
    patch = _generate_patch(
        module_key, avg_hes, dominant_state, streak['count'],
        problems, cross_context, source_snippet, target_file
    )

    # Write patch to docs/cognitive_patches/
    out_dir = root / 'docs' / 'cognitive_patches'
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')
    out_path = out_dir / f'{today}_{module_key}.md'

    header = (
        f'# Cognitive Patch — {module_key}\n\n'
        f'**Triggered**: {timestamp}  \n'
        f'**Reason**: {streak["count"]} consecutive high-load flushes '
        f'(avg hesitation {avg_hes}, dominant state: {dominant_state})  \n'
        f'**Problems found**: {len(problems)}  \n\n'
        f'---\n\n'
    )
    body = patch or '_DeepSeek unavailable — raw problems listed below._\n'
    if not patch and problems:
        body += '\n'.join(
            f'- [{p["severity"]}] {p["type"]}: {p.get("file","")} — {p.get("fix","")}'
            for p in problems
        )

    out_path.write_text(header + body + '\n', encoding='utf-8')

    # Auto-apply docstring patch when confidence is high enough
    staged = None
    if (target_file and streak['count'] >= FRUSTRATION_STREAK * 2
            and avg_hes >= HESITATION_THRESHOLD + 0.1):
        staged = _apply_docstring_patch(root, target_file, module_key, avg_hes, dominant_state)

    # Inject a hint into copilot-instructions if streak was severe
    if streak['count'] >= FRUSTRATION_STREAK * 2:
        _inject_cognitive_hint(root, module_key, avg_hes, dominant_state, patch)

    return {
        'fired': True,
        'module': module_key,
        'avg_hes': avg_hes,
        'dominant_state': dominant_state,
        'problems': len(problems),
        'patch_path': str(out_path.relative_to(root)),
        'staged_docstring_patch': staged,
    }
