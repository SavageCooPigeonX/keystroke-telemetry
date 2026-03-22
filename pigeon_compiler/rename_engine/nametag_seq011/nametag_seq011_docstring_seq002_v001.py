"""nametag_seq011_docstring_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _docstring_first_line(text: str) -> str:
    """Get first meaningful line from module docstring."""
    try:
        tree = ast.parse(text)
        ds = ast.get_docstring(tree)
        if not ds:
            return ''
    except SyntaxError:
        return ''

    for line in ds.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith(('Args:', 'Returns:', '---', 'Usage:')):
            continue
        # Skip lines that are just file paths (e.g. "listen/live/foo.py")
        if line.endswith('.py') and ('/' in line or '\\' in line):
            continue
        # Skip lines that are bare filenames (e.g. "foo_seq001_v001.py")
        if re.match(r'^[\w.]+\.py$', line):
            continue
        # Strip filename prefix like "module.py — description"
        if ' \u2014 ' in line:
            line = line.split(' \u2014 ', 1)[1]
        elif ' - ' in line:
            parts = line.split(' - ', 1)
            if len(parts[0].split()) <= 4:
                line = parts[1]
        return line.rstrip('.')
    return ''
