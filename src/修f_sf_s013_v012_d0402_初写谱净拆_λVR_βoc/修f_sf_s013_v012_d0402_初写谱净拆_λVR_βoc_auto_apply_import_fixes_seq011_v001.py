"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_auto_apply_import_fixes_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def auto_apply_import_fixes(root: Path, dry_run: bool = False) -> list[dict]:
    """Scan hardcoded pigeon imports and rewrite to use _resolve.py pattern.

    Rewrites `from src.module_seq003_v003_... import Foo, Bar` to:
        from src._resolve import src_import
        Foo, Bar = src_import("module_seq003", "Foo", "Bar")

    This is safe because src_import() resolves at runtime via glob,
    surviving any pigeon rename. No more naive str.replace corruption.
    """
    root = Path(root)
    results = []

    for py in sorted(root.rglob('*.py')):
        rel_parts = py.relative_to(root).parts
        if any(p in {'.venv', '__pycache__', '.git', 'node_modules'} for p in rel_parts):
            continue
        # Skip the resolver itself
        if py.name == '_resolve.py':
            continue

        try:
            text = py.read_text(encoding='utf-8')
        except Exception:
            continue

        if '_seq' not in text or '_v' not in text:
            continue

        lines = text.splitlines(keepends=True)
        new_lines = []
        changed = False
        needs_resolve_import = False

        for line in lines:
            # Check from-import pattern
            m = _HC_FROM_IMPORT.match(line)
            if m:
                indent = m.group(1)
                mod_full = m.group(3)
                symbols_raw = m.group(4)
                symbols = [s.strip().rstrip(')') for s in symbols_raw.split(',') if s.strip()]
                # Skip parenthesized multi-line imports (just flag them)
                if '(' in symbols_raw and ')' not in symbols_raw:
                    new_lines.append(line)
                    continue
                symbols = [s for s in symbols if s and s != '(']
                base = _seq_base(mod_full)
                if len(symbols) == 1:
                    new_line = f'{indent}{symbols[0]} = src_import("{base}", "{symbols[0]}")\n'
                else:
                    lhs = ', '.join(symbols)
                    args = ', '.join(f'"{s}"' for s in symbols)
                    new_line = f'{indent}{lhs} = src_import("{base}", {args})\n'
                new_lines.append(new_line)
                needs_resolve_import = True
                changed = True
                results.append({'file': str(py.relative_to(root)),
                                'old_import': line.strip(),
                                'new_expr': new_line.strip(),
                                'applied': not dry_run})
                continue

            # Check bare-import pattern
            m2 = _HC_BARE_IMPORT.match(line)
            if m2:
                indent = m2.group(1)
                mod_full = m2.group(3)
                base = _seq_base(mod_full)
                alias = base.split('_seq')[0]
                new_line = f'{indent}{alias} = src_import("{base}")\n'
                new_lines.append(new_line)
                needs_resolve_import = True
                changed = True
                results.append({'file': str(py.relative_to(root)),
                                'old_import': line.strip(),
                                'new_expr': new_line.strip(),
                                'applied': not dry_run})
                continue

            new_lines.append(line)

        if not changed or dry_run:
            continue

        # Inject `from src._resolve import src_import` if not present
        new_text = ''.join(new_lines)
        if needs_resolve_import and 'from src._resolve import src_import' not in new_text:
            # Remove any old _load_src helper if present
            new_text = re.sub(
                r'\ndef _load_src\(pattern:.*?return tuple\(.*?\)\n',
                '\n', new_text, flags=re.DOTALL)
            # Insert resolve import after pigeon header or first import
            insert_lines = new_text.splitlines(keepends=True)
            insert_pos = 0
            for i, ln in enumerate(insert_lines[:30]):
                if ln.strip().startswith(('import ', 'from ')):
                    insert_pos = i
            insert_lines.insert(insert_pos + 1,
                                'from src._resolve import src_import\n')
            new_text = ''.join(insert_lines)

        py.write_text(new_text, encoding='utf-8')

    return results
