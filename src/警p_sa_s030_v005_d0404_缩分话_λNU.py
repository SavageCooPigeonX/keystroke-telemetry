"""Copilot self-diagnostic: detect stale managed blocks in copilot-instructions.md."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

COPILOT_PATH = '.github/copilot-instructions.md'
ALERT_START = '<!-- pigeon:staleness-alert -->'
ALERT_END   = '<!-- /pigeon:staleness-alert -->'

# Blocks that MUST refresh every prompt cycle
PER_PROMPT_BLOCKS = {
    'current-query': {
        'block_start': '<!-- pigeon:current-query -->',
        'block_end':   '<!-- /pigeon:current-query -->',
        'pattern': r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC',
        'fmt': '%Y-%m-%d %H:%M',
        'max_age_min': 10,
        'writer': 'prompt_enricher (Gemini Flash)',
    },
    'prompt-telemetry': {
        'block_start': '<!-- pigeon:prompt-telemetry -->',
        'block_end':   '<!-- /pigeon:prompt-telemetry -->',
        'pattern': r'"updated_at":\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        'fmt': '%Y-%m-%dT%H:%M:%S',
        'max_age_min': 10,
        'writer': 'prompt_journal._refresh_copilot_instructions',
    },
    'task-context': {
        'block_start': '<!-- pigeon:task-context -->',
        'block_end':   '<!-- /pigeon:task-context -->',
        'pattern': r'Auto-injected (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC',
        'fmt': '%Y-%m-%d %H:%M',
        'max_age_min': 120,  # refreshed by classify_bridge, looser threshold
        'writer': 'dynamic_prompt.inject_task_context (via classify_bridge)',
    },
}


def _parse_ts(raw: str, fmt: str) -> datetime | None:
    try:
        return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _strip_alert_block(text: str) -> str:
    pat = re.compile(
        rf'^\s*{re.escape(ALERT_START)}\s*$\n.*?^\s*{re.escape(ALERT_END)}\s*$\n?',
        re.MULTILINE | re.DOTALL,
    )
    return pat.sub('', text)


def _extract_managed_block(text: str, block_start: str, block_end: str) -> str | None:
    """Return the actual managed block, not an inline example mention."""
    pat = re.compile(
        rf'(?ms)^\s*{re.escape(block_start)}\s*$\n.*?^\s*{re.escape(block_end)}\s*$'
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(0)


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

    # Check learning loop health
    stale.extend(_check_learning_loop(root, now))

    return stale


def _check_learning_loop(root: Path, now: datetime) -> list[dict]:
    """Check if the learning loop has fallen behind the journal."""
    import json
    state_path = root / 'pigeon_brain' / 'learning_loop_state.json'
    journal_path = root / 'logs' / 'prompt_journal.jsonl'
    if not state_path.exists() or not journal_path.exists():
        return []
    try:
        state = json.loads(state_path.read_text('utf-8'))
        journal_lines = sum(1 for _ in journal_path.open('r', encoding='utf-8'))
        processed = state.get('last_processed_line', 0)
        unprocessed = max(0, journal_lines - processed)
        last_ts_raw = state.get('last_processed_ts') or state.get('updated_at')
        if last_ts_raw:
            last_ts = datetime.fromisoformat(last_ts_raw)
            age = now - last_ts
            age_hours = age.total_seconds() / 3600
        else:
            age_hours = None
        # Alert if >20 entries behind or >24h stale
        if unprocessed > 20 or (age_hours and age_hours > 24):
            reason = f'BEHIND — {unprocessed} unprocessed entries'
            if age_hours:
                reason += f', last ran {age_hours:.0f}h ago'
            return [{
                'block': 'learning-loop',
                'reason': reason,
                'writer': 'git_plugin → catch_up (post-commit)',
                'age_min': round(age_hours * 60, 1) if age_hours else None,
                'last_ts': last_ts_raw,
            }]
    except Exception:
        pass
    return []

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


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    stale = check_staleness(root)
    inject_staleness_alert(root)
    if stale:
        print(f'STALE ({len(stale)}): ' + ', '.join(s['block'] for s in stale))
    else:
        print('All blocks fresh')
