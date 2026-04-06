"""file_consciousness_seq019_dependencies_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import ast
import json
import re

def _derive_dependencies(node, local_fns: set) -> list[str]:
    """i_want: What this function needs — imports, file reads, local calls."""
    wants = []
    for child in ast.walk(node):
        # File reads: open(), Path().read_text(), glob(), etc.
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('open', 'read_text', 'read_bytes'):
                # Try to extract the path argument
                if child.args:
                    arg = _const_value(child.args[0])
                    wants.append(f'file:{arg}' if arg else f'file:unknown')
            elif fname in ('glob', 'rglob'):
                arg = _const_value(child.args[0]) if child.args else None
                wants.append(f'glob:{arg}' if arg else 'glob:pattern')
            elif fname in local_fns:
                wants.append(f'func:{fname}')
        # json.loads / json.load
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('json.loads', 'json.load', 'json.loads'):
                wants.append('json_input')
    return list(dict.fromkeys(wants))[:8]  # deduplicate, cap at 8


def _derive_exports(node) -> list[str]:
    """i_give: What this function returns or writes."""
    gives = []
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            gives.append(f'returns:{_type_hint(child.value)}')
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('write_text', 'write_bytes', 'write'):
                gives.append('writes:file')
            elif fname in ('json.dumps', 'json.dump'):
                gives.append('writes:json')
            elif fname == 'print':
                gives.append('prints:stdout')
    return list(dict.fromkeys(gives))[:6]
