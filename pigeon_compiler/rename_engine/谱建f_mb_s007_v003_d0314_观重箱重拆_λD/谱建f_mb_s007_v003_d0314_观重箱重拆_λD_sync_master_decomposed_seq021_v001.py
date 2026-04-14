"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_sync_master_decomposed_seq021_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 021 | VER: v001 | 66 lines | ~615 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import ast
import re

def sync_master_structure(root: Path, results: list[dict] = None):
    """Rebuild the PROJECT STRUCTURE section in MASTER_MANIFEST.md.

    Scans the actual filesystem and generates a current folder tree
    with file counts and compliance stats per folder.
    """
    master = root / 'MASTER_MANIFEST.md'
    if not master.exists():
        return
    content = master.read_text(encoding='utf-8')

    # Build the new structure block
    tree = _build_structure_tree(root)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    new_section = (
        '## FOLDER TREE\n'
        f'*Auto-synced by manifest_builder | {now}*\n\n'
        '```\n'
        f'{tree}'
        '```'
    )

    # Replace the existing FOLDER TREE section
    start_marker = '## FOLDER TREE'
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return

    # Find end: next ## heading or end of file
    rest = content[start_idx + len(start_marker):]
    end_match = re.search(r'\n## [A-Z]', rest)
    if end_match:
        end_idx = start_idx + len(start_marker) + end_match.start() + 1
    else:
        end_idx = len(content)

    content = content[:start_idx] + new_section + '\n\n' + content[end_idx:]

    # Inject or replace OPERATOR KEYSTROKE TRAIL section
    trail_section = _build_keystroke_trail(root, now)
    if trail_section:
        trail_marker = '## OPERATOR KEYSTROKE TRAIL'
        trail_idx = content.find(trail_marker)
        if trail_idx != -1:
            rest_t = content[trail_idx + len(trail_marker):]
            end_t = re.search(r'\n## [A-Z]', rest_t)
            if end_t:
                trail_end = trail_idx + len(trail_marker) + end_t.start() + 1
            else:
                trail_end = len(content)
            content = content[:trail_idx] + trail_section + '\n\n' + content[trail_end:]
        else:
            # Append before CHANGELOG if it exists, else at end
            changelog_idx = content.find('## CHANGELOG')
            if changelog_idx != -1:
                content = content[:changelog_idx] + trail_section + '\n\n' + content[changelog_idx:]
            else:
                content = content.rstrip() + '\n\n' + trail_section + '\n'

    master.write_text(content, encoding='utf-8')
