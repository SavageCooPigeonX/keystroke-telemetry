"""escalation_engine_fix_duplicate_docstring_decomposed_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 63 lines | ~633 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _fix_duplicate_docstring(root: Path, module: str, registry_entry: dict) -> dict:
    """Remove duplicate docstrings from a file."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found', 'details': []}

    try:
        source = fpath.read_text(encoding='utf-8')
        lines = source.split('\n')
        seen_docstrings = set()
        new_lines = []
        in_docstring = False
        docstring_buf = []
        skip_block = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                if stripped.count(quote) >= 2:
                    # single-line docstring
                    if stripped in seen_docstrings:
                        i += 1
                        continue
                    seen_docstrings.add(stripped)
                    new_lines.append(line)
                else:
                    # multi-line docstring start
                    docstring_buf = [line]
                    in_docstring = True
                    i += 1
                    while i < len(lines):
                        docstring_buf.append(lines[i])
                        if quote in lines[i]:
                            break
                        i += 1
                    block = '\n'.join(docstring_buf)
                    if block in seen_docstrings:
                        i += 1
                        continue
                    seen_docstrings.add(block)
                    new_lines.extend(docstring_buf)
            else:
                new_lines.append(line)
            i += 1

        new_source = '\n'.join(new_lines)
        if new_source != source:
            fpath.write_text(new_source, encoding='utf-8')
            removed = len(lines) - len(new_lines)
            return {
                'success': True,
                'description': f'removed {removed} duplicate docstring lines',
                'details': [{'file': str(fpath), 'lines_removed': removed}],
            }
        return {'success': False, 'description': 'no duplicates found', 'details': []}
    except Exception as e:
        return {'success': False, 'description': f'docstring dedup failed: {e}', 'details': []}
