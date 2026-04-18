"""context_compressor_seq001_v001_text_cleaners_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 31 lines | ~234 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _strip_comments(source):
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('#'):
            if stripped.startswith('#!') or 'coding' in stripped:
                lines.append(line)
            continue
        if '  #' in line:
            idx = line.index('  #')
            before = line[:idx]
            if before.count("'") % 2 == 0 and before.count('"') % 2 == 0:
                line = before.rstrip()
        lines.append(line)
    return '\n'.join(lines)


def _collapse_blanks(source):
    out = []
    prev_blank = False
    for line in source.splitlines():
        if not line.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(line)
    return '\n'.join(out)
