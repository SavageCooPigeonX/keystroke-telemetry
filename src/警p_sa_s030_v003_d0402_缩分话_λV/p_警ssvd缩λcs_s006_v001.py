"""警p_sa_s030_v003_d0402_缩分话_λV_check_staleness_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re

def check_staleness(root: Path) -> list[dict]:
    """Check all per-prompt blocks for staleness. Returns list of stale block dicts."""
    root = Path(root)
    cp = root / COPILOT_PATH
    if not cp.exists():
        return []

    text = cp.read_text('utf-8')
    now = datetime.now(timezone.utc)
    stale = []

    for block_name, cfg in PER_PROMPT_BLOCKS.items():
        block_text = _extract_managed_block(text, cfg['block_start'], cfg['block_end'])
        if block_text is None:
            stale.append({
                'block': block_name,
                'reason': 'MISSING — block not found in file',
                'writer': cfg['writer'],
                'age_min': None,
            })
            continue
        m = re.search(cfg['pattern'], block_text)
        if not m:
            stale.append({
                'block': block_name,
                'reason': f'MISSING — timestamp not found inside block',
                'writer': cfg['writer'],
                'age_min': None,
            })
            continue

        ts = _parse_ts(m.group(1), cfg['fmt'])
        if ts is None:
            stale.append({
                'block': block_name,
                'reason': f'UNPARSEABLE timestamp: {m.group(1)}',
                'writer': cfg['writer'],
                'age_min': None,
            })
            continue

        age = now - ts
        age_min = age.total_seconds() / 60
        if age_min > cfg['max_age_min']:
            stale.append({
                'block': block_name,
                'reason': f'STALE — {age_min:.0f}min old (max {cfg["max_age_min"]}min)',
                'writer': cfg['writer'],
                'age_min': round(age_min, 1),
                'last_ts': m.group(1),
            })

    return stale
