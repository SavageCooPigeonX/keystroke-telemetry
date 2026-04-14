"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_parse_pigeon_header_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _parse_pigeon_header(text: str) -> dict:
    """Extract pigeon metadata from the # ── pigeon ── header block."""
    info = {}
    for line in text.splitlines()[:20]:
        line = line.strip().lstrip('#').strip()
        if line.startswith('SEQ:'):
            m = re.search(r'VER:\s*(v\d+)', line)
            if m:
                info['ver'] = m.group(1)
            m2 = re.search(r'~([\d,]+)\s*tokens', line)
            if m2:
                info['tokens'] = int(m2.group(1).replace(',', ''))
        elif line.startswith('LAST:'):
            info['last'] = line.split('LAST:', 1)[1].strip()
        elif line.startswith('SESSIONS:'):
            m = re.search(r'SESSIONS:\s*(\d+)', line)
            if m:
                info['sessions'] = int(m.group(1))
        elif line.startswith('INTENT:'):
            info['intent'] = line.split('INTENT:', 1)[1].strip()
    # Also check @pigeon comment for role
    for line in text.splitlines()[:5]:
        if line.startswith('# @pigeon:'):
            m = re.search(r'role=(\w+)', line)
            if m:
                info['role'] = m.group(1)
    return info
