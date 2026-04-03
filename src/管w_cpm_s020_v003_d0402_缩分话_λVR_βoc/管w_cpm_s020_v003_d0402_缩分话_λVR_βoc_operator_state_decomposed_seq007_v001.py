"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_operator_state_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
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


def _build_operator_state_block(root: Path) -> str | None:
    profile = _parse_operator_profile(root)
    if not profile or profile['messages'] == 0:
        return None

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    dominant = profile['dominant']
    coaching_prose = _load_coaching_prose(root)
    if coaching_prose:
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} - {profile["messages"]} message(s) - LLM-synthesized*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {profile["submit_rate"]}% '
             f'| WPM: {profile["avg_wpm"]:.1f} '
             f'| Del: {profile["avg_del"]:.1f}% '
             f'| Hes: {profile["avg_hes"]:.3f}'),
            '',
            coaching_prose,
            '',
            '<!-- /pigeon:operator-state -->',
        ]
        return '\n'.join(lines)

    hint = _STATE_HINTS.get(dominant, _STATE_HINTS['neutral'])
    lines = [
        '<!-- pigeon:operator-state -->',
        '## Live Operator State',
        '',
        f'*Auto-updated {today} - {profile["messages"]} message(s) in profile*',
        '',
        (f'**Dominant: `{dominant}`** '
         f'| Submit: {profile["submit_rate"]}% '
         f'| WPM: {profile["avg_wpm"]:.1f} '
         f'| Del: {profile["avg_del"]:.1f}% '
         f'| Hes: {profile["avg_hes"]:.3f}'),
        '',
        '**Behavioral tunes for this session:**',
        f'- **{dominant}** -> {hint}',
    ]
    if profile['avg_wpm'] < 45:
        lines.append('- WPM < 45 -> prefer bullets and code blocks over dense prose')
    if profile['avg_del'] > 30:
        lines.append('- Deletion ratio > 30% -> high rethinking; consider asking "what specifically do you need?"')
    if profile['submit_rate'] < 60:
        lines.append(
            f'- Submit rate {profile["submit_rate"]}% -> messages often abandoned; check if previous answer landed before going deep'
        )
    if profile['avg_hes'] > 0.4:
        lines.append('- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples')
    if profile['active_hours']:
        lines.append(f'- Active hours: {profile["active_hours"]}')
    lines.append('<!-- /pigeon:operator-state -->')
    return '\n'.join(lines)
