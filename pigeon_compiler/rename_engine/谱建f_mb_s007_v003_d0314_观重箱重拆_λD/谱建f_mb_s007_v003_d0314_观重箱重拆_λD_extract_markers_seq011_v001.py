"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_markers_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 15 lines | ~151 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_code_markers(text: str) -> list[dict]:
    """Extract TODO/FIXME/HACK/NOTE markers from comments."""
    markers = []
    for i, line in enumerate(text.splitlines(), 1):
        m = _MARKER_RE.search(line)
        if m:
            tag = m.group(1).upper()
            rest = line[m.end():].strip().lstrip(':').strip()
            if len(rest) > 60:
                rest = rest[:57] + '...'
            markers.append({'tag': tag, 'line': i, 'text': rest})
    return markers
