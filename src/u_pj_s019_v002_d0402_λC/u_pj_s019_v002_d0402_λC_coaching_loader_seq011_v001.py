"""u_pj_s019_v002_d0402_λC_coaching_loader_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _load_fresh_coaching_bullets(root: Path, max_age_s: float = 7200.0) -> list[str]:
    """Read coaching bullet lines from operator_coaching.md if < max_age_s old."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return []
    try:
        import time as _time
        if _time.time() - coaching_path.stat().st_mtime > max_age_s:
            return []
        text = coaching_path.read_text(encoding='utf-8')
        # Pull bullet lines (- **...**) from coaching block or plain markdown
        bullets = re.findall(r'^\s*[-*]\s+\*\*(.+?)\*\*', text, re.MULTILINE)
        if not bullets:
            bullets = re.findall(r'^\s*[-*]\s+(.+)', text, re.MULTILINE)
        return [b.strip() for b in bullets[:6]]
    except Exception:
        return []


def _dominant_state(state_dist: dict) -> str | None:
    if not state_dist:
        return None
    return next(iter(state_dist))
