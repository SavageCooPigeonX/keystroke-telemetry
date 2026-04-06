"""copilot_prompt_manager_seq020_operator_profile_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import re

def _parse_operator_profile(root: Path) -> dict | None:
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return None
    try:
        text = prof_path.read_text(encoding='utf-8')
    except Exception:
        return None

    def _re(pattern: str, default: str) -> str:
        match = re.search(pattern, text)
        return match.group(1) if match else default

    return {
        'messages': int(_re(r'(\d+) messages ingested', '0') or '0'),
        'dominant': _re(r'\*\*Dominant state:\s*(\w+)\*\*', 'neutral'),
        'submit_rate': int(_re(r'\*\*Submit rate:.*?\((\d+)%\)\*\*', '0') or '0'),
        'avg_wpm': float(_re(r'\|\s*WPM\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'avg_del': float(_re(r'\|\s*Deletion\s*%\s*\|[^|]+\|[^|]+\|\s*([\d.]+)%', '0') or '0'),
        'avg_hes': float(_re(r'\|\s*Hesitation\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'active_hours': _re(r'\*\*Active hours:\*\*\s*(.+)', '').strip(),
    }


def _load_coaching_prose(root: Path, max_age_s: float = 7200.0) -> str | None:
    """Load coaching prose from operator_coaching.md if file is < max_age_s old."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        import time as _time
        age_s = _time.time() - coaching_path.stat().st_mtime
        if age_s > max_age_s:
            return None  # stale — don't inject outdated coaching
        text = coaching_path.read_text(encoding='utf-8')
        match = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception:
        return None
    return None
