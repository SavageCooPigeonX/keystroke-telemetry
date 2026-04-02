"""警p_sa_s030_v003_d0402_缩分话_λV_inject_alert_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re

def inject_staleness_alert(root: Path) -> bool:
    """Check blocks and inject/remove alert. Returns True if alert was injected."""
    root = Path(root)
    cp = root / COPILOT_PATH
    if not cp.exists():
        return False

    stale = check_staleness(root)
    text = cp.read_text('utf-8')
    text = _strip_alert_block(text)

    if not stale:
        # Everything fresh — remove alert if it existed
        if ALERT_START in cp.read_text('utf-8'):
            cp.write_text(text, 'utf-8')
        return False

    # Build angry alert block
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        ALERT_START,
        '## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE',
        '',
        f'*Checked {now_str} — {len(stale)} block(s) stale or missing*',
        '',
        '**ATTENTION: The following blocks did NOT update when they should have.**',
        '**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**',
        '',
    ]

    for s in stale:
        lines.append(f'- **`{s["block"]}`**: {s["reason"]}')
        lines.append(f'  - Writer: `{s["writer"]}`')
        if s.get('last_ts'):
            lines.append(f'  - Last updated: {s["last_ts"]}')
        lines.append('')

    lines.append('**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.')
    lines.append('')
    lines.append(ALERT_END)

    block = '\n'.join(lines)

    # Insert at the very top of the file content (after the # header line)
    # so Copilot sees it FIRST
    header_end = text.find('\n---\n')
    if header_end >= 0:
        # Insert right after the first --- separator
        insert_at = header_end + len('\n---\n')
        text = text[:insert_at] + '\n' + block + '\n\n' + text[insert_at:]
    else:
        # Prepend
        text = block + '\n\n' + text

    cp.write_text(text, 'utf-8')
    return True
