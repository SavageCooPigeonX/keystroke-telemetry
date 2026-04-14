"""git_plugin_copilot_index_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 57 lines | ~567 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import re

def _refresh_copilot_instructions(root: Path, registry: dict, processed: int) -> bool:
    """Rebuild the <!-- pigeon:auto-index --> block in .github/copilot-instructions.md.

    Only updates the auto-index section — everything hand-written is preserved.
    Fires on every commit that touches pigeon .py files so the index stays live.
    """
    cp_path = root / '.github' / 'copilot-instructions.md'
    if not cp_path.exists():
        return False

    # Group registry entries by folder
    groups: dict[str, list] = {}
    for path, entry in registry.items():
        folder = str(Path(path).parent).replace('\\', '/')
        groups.setdefault(folder, []).append({
            'name':   entry.get('name', ''),
            'seq':    entry.get('seq', 0),
            'desc':   (entry.get('desc') or '').replace('_', ' ')[:52],
            'tokens': entry.get('tokens', 0),
        })

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    block_lines = [
        '<!-- pigeon:auto-index -->',
        f'*Auto-updated {today} — {len(registry)} modules tracked | {processed} touched this commit*',
        '',
    ]
    for folder in sorted(groups.keys()):
        items = sorted(groups[folder], key=lambda e: (e['seq'], e['name']))
        block_lines.append(f'**{folder}/** — {len(items)} module(s)')
        block_lines.append('')
        block_lines.append('| Search pattern | Desc | Tokens |')
        block_lines.append('|---|---|---:|')
        for item in items:
            pat = f'`{item["name"]}_seq{item["seq"]:03d}*`'
            block_lines.append(f'| {pat} | {item["desc"]} | ~{item["tokens"]:,} |')
        block_lines.append('')
    block_lines.append('<!-- /pigeon:auto-index -->')
    block = '\n'.join(block_lines)

    try:
        text = cp_path.read_text(encoding='utf-8')
    except Exception:
        return False

    if _AUTO_INDEX_RE.search(text):
        new_text = _AUTO_INDEX_RE.sub(block, text)
    else:
        new_text = text.rstrip() + '\n\n---\n\n### Full Module Index\n\n' + block + '\n'

    cp_path.write_text(new_text, encoding='utf-8')
    return True
