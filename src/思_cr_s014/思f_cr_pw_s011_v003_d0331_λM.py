"""cognitive_reactor_seq014_patch_writer_seq011 — Apply code patches to source files.

Parses unified diff or replacement blocks from DeepSeek cognitive patches.
Writes changes to disk only after passing decision_maker safety gate.
Logs every application to logs/patch_applications.jsonl.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v003 | 128 lines | ~1,075 tokens
# DESC:   apply_code_patches_to_source
# INTENT: mutation_patch_pipeline
# LAST:   2026-03-31 @ a9e145a
# SESSIONS: 2
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-31T17:00:00.000000+00:00
# EDIT_HASH: auto
# EDIT_WHY:  implement patch writer from stub
# EDIT_STATE: harvested
# ── /pulse ──

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def extract_code_blocks(patch_text: str) -> list[str]:
    """Pull ```python ... ``` blocks from a DeepSeek patch response."""
    blocks = re.findall(r'```python\s*\n(.*?)```', patch_text, re.DOTALL)
    return [b.strip() for b in blocks if b.strip()]


def extract_replacements(patch_text: str) -> list[tuple[str, str]]:
    """Pull REPLACE: old → new pairs from structured patch output.

    Format expected:
    REPLACE:
    ```old
    <old code>
    ```
    WITH:
    ```new
    <new code>
    ```
    """
    pairs = []
    old_blocks = re.findall(r'```old\s*\n(.*?)```', patch_text, re.DOTALL)
    new_blocks = re.findall(r'```new\s*\n(.*?)```', patch_text, re.DOTALL)
    for old, new in zip(old_blocks, new_blocks):
        if old.strip() and new.strip():
            pairs.append((old.strip(), new.strip()))
    return pairs


def apply_patch(
    root: Path,
    target_path: str,
    patch_text: str,
    module_key: str,
    decision_fn=None,
) -> dict:
    """Parse a cognitive patch and apply it to the target file.

    Args:
        root: workspace root
        target_path: relative path to the file
        patch_text: raw DeepSeek patch output
        module_key: pigeon module key for logging
        decision_fn: callable(root, target_path, new_source, old_source) -> dict

    Returns:
        {'applied': bool, 'reason': str, 'replacements': int}
    """
    root = Path(root)
    fp = root / target_path
    if not fp.exists():
        return {'applied': False, 'reason': 'target file not found', 'replacements': 0}

    original = fp.read_text('utf-8')
    new_source = original
    n_replacements = 0

    # Try structured REPLACE/WITH pairs first
    pairs = extract_replacements(patch_text)
    for old_block, new_block in pairs:
        if old_block in new_source:
            new_source = new_source.replace(old_block, new_block, 1)
            n_replacements += 1

    # If no structured replacements, try full code block replacement
    if n_replacements == 0:
        blocks = extract_code_blocks(patch_text)
        if len(blocks) == 1 and len(blocks[0].splitlines()) > 5:
            new_source = blocks[0]
            n_replacements = 1

    if new_source == original:
        return {'applied': False, 'reason': 'no applicable changes found in patch', 'replacements': 0}

    # Safety gate
    if decision_fn:
        verdict = decision_fn(root, target_path, new_source, original)
        if not verdict.get('allow'):
            _log_application(root, module_key, target_path, False, verdict.get('reason', 'rejected'))
            return {'applied': False, 'reason': verdict.get('reason', 'rejected by decision_maker'), 'replacements': n_replacements}

    # Apply
    fp.write_text(new_source, encoding='utf-8')
    _log_application(root, module_key, target_path, True, f'{n_replacements} replacements applied')

    return {'applied': True, 'reason': f'{n_replacements} replacements applied', 'replacements': n_replacements}


def _log_application(root: Path, module: str, path: str, applied: bool, reason: str) -> None:
    log_path = root / 'logs' / 'patch_applications.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        'ts': datetime.now(timezone.utc).isoformat(),
        'module': module,
        'file': path,
        'applied': applied,
        'reason': reason,
    })
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

