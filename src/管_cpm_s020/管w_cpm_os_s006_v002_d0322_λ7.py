"""copilot_prompt_manager_seq020_operator_state_decomposed_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

from datetime import datetime, timezone
from pathlib import Path
import re

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
