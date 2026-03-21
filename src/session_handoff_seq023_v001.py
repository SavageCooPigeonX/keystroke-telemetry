"""Session handoff summary generator.

Triggered on idle (os_hook `status: idle`) or CLI: `py -m src.session_handoff_seq023_v001`
Writes docs/session_handoffs/YYYY-MM-DD_HHMM.md with:
  - Current cognitive state + WPM
  - Hot modules from file_heat_map
  - Active task queue
  - Last 5 journal entries (prompt previews)
  - Open pulse states (any stamped-but-unharvested pulse blocks)
  - Recent rework verdicts

Zero LLM calls. Safe to run repeatedly — deduplicates by minute bucket.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v001 | ~130 lines
# DESC:   session_handoff_summary_generator
# INTENT: session_handoff
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
from __future__ import annotations
import glob as _glob
import json
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text('utf-8')) if path.exists() else default
    except Exception:
        return default


def _last_journal_entries(root: Path, n: int = 5) -> list[dict]:
    p = root / 'logs' / 'prompt_journal.jsonl'
    if not p.exists():
        return []
    lines = [l for l in p.read_text('utf-8', errors='replace').splitlines() if l.strip()]
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def _open_pulses(root: Path) -> list[str]:
    """Find .py files under src/ with a stamped (non-None) EDIT_TS in their pulse block."""
    open_files = []
    for fp in sorted((root / 'src').glob('*.py')):
        try:
            text = fp.read_text('utf-8', errors='replace')
            if '# EDIT_TS:   None' not in text and '# ── telemetry:pulse ──' in text:
                import re
                m = re.search(r'# EDIT_TS:\s+(\S+)', text)
                if m and m.group(1) != 'None':
                    open_files.append(fp.name)
        except Exception:
            pass
    return open_files


def generate(root: Path) -> Path:
    """Generate a session handoff markdown file. Returns the output path."""
    now = datetime.now(timezone.utc)
    bucket = now.strftime('%Y-%m-%d_%H%M')

    out_dir = root / 'docs' / 'session_handoffs'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{bucket}.md'

    if out_path.exists():
        return out_path  # already generated this minute — skip

    lines = [
        f'# Session Handoff — {now.strftime("%Y-%m-%d %H:%M UTC")}',
        '',
        '> Auto-generated on idle. Resume from here next session.',
        '',
    ]

    # Cognitive state
    snap = _read_json(root / 'logs' / 'prompt_telemetry_latest.json', {})
    if snap:
        lp = snap.get('latest_prompt', {})
        sig = snap.get('signals', {})
        state = lp.get('state', 'unknown')
        wpm = sig.get('wpm', 0)
        del_r = sig.get('deletion_ratio', 0)
        lines += [
            '## Cognitive State at Handoff',
            '',
            f'**State:** `{state}` | **WPM:** {wpm:.1f} | **Del ratio:** {del_r:.2f}',
            '',
        ]

    # Hot modules
    heat = _read_json(root / 'file_heat_map.json', {})
    modules = heat.get('modules', heat) if isinstance(heat, dict) else {}
    if isinstance(modules, dict):
        hot = sorted(modules.items(), key=lambda kv: kv[1].get('hes', 0) if isinstance(kv[1], dict) else 0, reverse=True)[:5]
    else:
        hot = []
    if hot:
        lines += ['## Hot Modules', '']
        for name, data in hot:
            hes = data.get('hes', 0) if isinstance(data, dict) else 0
            lines.append(f'- `{name}` (hes={hes:.3f})')
        lines.append('')

    # Task queue
    tq = _read_json(root / 'task_queue.json', {})
    tasks = tq.get('tasks', []) if isinstance(tq, dict) else []
    in_prog = [t for t in tasks if t.get('status') == 'in_progress']
    pending = [t for t in tasks if t.get('status') == 'pending']
    if in_prog or pending:
        lines += ['## Task Queue', '']
        for t in in_prog:
            lines.append(f'- 🔄 **[IN PROGRESS]** {t.get("title", "?")}')
        for t in pending[:5]:
            lines.append(f'- ⏳ {t.get("title", "?")}')
        lines.append('')

    # Last journal entries
    entries = _last_journal_entries(root, n=5)
    if entries:
        lines += ['## Last 5 Prompts', '']
        for e in entries:
            ts = e.get('ts', '')[:19]
            preview = e.get('msg', '')[:80].replace('\n', ' ')
            state_e = e.get('cognitive_state', '?')
            lines.append(f'- `{ts}` [{state_e}] {preview}')
        lines.append('')

    # Open pulses
    open_p = _open_pulses(root)
    if open_p:
        lines += ['## Open Pulse Blocks (not yet harvested)', '']
        for fp in open_p:
            lines.append(f'- `src/{fp}`')
        lines.append('')

    # Rework summary
    rework = _read_json(root / 'rework_log.json', [])
    if rework:
        recent = rework[-10:]
        misses = sum(1 for r in recent if r.get('verdict') == 'miss')
        lines += [
            '## Recent Rework',
            '',
            f'Last 10 responses: **{misses}/10 misses**',
            '',
        ]

    # Coaching bullets
    coaching_path = root / 'operator_coaching.md'
    if coaching_path.exists():
        try:
            import re, time as _time
            age_h = (_time.time() - coaching_path.stat().st_mtime) / 3600
            if age_h < 24:
                text = coaching_path.read_text('utf-8')
                bullets = re.findall(r'^\s*[-*]\s+\*\*(.+?)\*\*', text, re.MULTILINE)[:5]
                if bullets:
                    lines += ['## Active Coaching Directives', '']
                    for b in bullets:
                        lines.append(f'- **{b}**')
                    lines.append('')
        except Exception:
            pass

    lines += ['---', f'*Generated {now.isoformat()}*']
    out_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return out_path


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    p = generate(root)
    print(f'Handoff written: {p}')
