"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_jsonl_tail(filepath: Path, max_lines: int = 50) -> list[dict]:
    """Read last N lines of a JSONL file."""
    if not filepath.exists():
        return []
    try:
        data = filepath.read_bytes()
        lines = data.decode('utf-8', errors='replace').strip().split('\n')
        results = []
        for line in lines[-max_lines:]:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return results
    except OSError:
        return []


def _normalize_text(text: str) -> str:
    return ' '.join(str(text or '').lower().split())


def _summarize_text(text: str, max_chars: int = 220) -> str:
    cleaned = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not cleaned:
        return ''
    if len(cleaned) <= max_chars:
        return cleaned
    for sep in ('. ', '! ', '? '):
        idx = cleaned.find(sep)
        if 0 < idx < max_chars:
            return cleaned[:idx + 1].strip()
    return cleaned[:max_chars - 3].rstrip() + '...'


def _top_counts(items: list[str], limit: int = 5) -> list[dict]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item or '').strip()
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{'value': value, 'count': count} for value, count in ranked[:limit]]
