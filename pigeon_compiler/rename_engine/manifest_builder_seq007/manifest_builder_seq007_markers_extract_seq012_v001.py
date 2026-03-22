"""manifest_builder_seq007_markers_extract_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
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
