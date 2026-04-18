"""git_plugin_operator_state_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 91 lines | ~908 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import os
import re

def _refresh_operator_state(root: Path) -> bool:
    """Rebuild <!-- pigeon:operator-state --> block in copilot-instructions.md.

    Priority:
      1. LLM-synthesized prose from operator_coaching.md (generated every 8 submitted msgs)
      2. Static template built from operator_profile.md metrics (always available)

    This lets the block evolve from raw stats → rich behavioral coaching over time
    as the operator accumulates enough history for the LLM to detect real patterns.
    """
    cp_path = root / '.github' / 'copilot-instructions.md'
    if not cp_path.exists():
        return False

    prof = _parse_operator_profile(root)
    if not prof or prof['messages'] == 0:
        return False

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    dominant = prof['dominant']

    # ── Try LLM-generated prose first ──────────────────────────────────────
    coaching_prose = _load_coaching_prose(root)
    if coaching_prose:
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} · {prof["messages"]} message(s) · LLM-synthesized*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {prof["submit_rate"]}% '
             f'| WPM: {prof["avg_wpm"]:.1f} '
             f'| Del: {prof["avg_del"]:.1f}% '
             f'| Hes: {prof["avg_hes"]:.3f}'),
            '',
            coaching_prose,
            '',
            '<!-- /pigeon:operator-state -->',
        ]
        block = '\n'.join(lines)
    else:
        # ── Static template fallback (first <8 messages) ────────────────────
        hint = _STATE_HINTS.get(dominant, _STATE_HINTS['neutral'])
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} · {prof["messages"]} message(s) in profile*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {prof["submit_rate"]}% '
             f'| WPM: {prof["avg_wpm"]:.1f} '
             f'| Del: {prof["avg_del"]:.1f}% '
             f'| Hes: {prof["avg_hes"]:.3f}'),
            '',
            '**Behavioral tunes for this session:**',
            f'- **{dominant}** → {hint}',
        ]
        if prof['avg_wpm'] < 45:
            lines.append('- WPM < 45 → prefer bullets and code blocks over dense prose')
        if prof['avg_del'] > 30:
            lines.append('- Deletion ratio > 30% → high rethinking; consider asking "what specifically do you need?"')
        if prof['submit_rate'] < 60:
            lines.append(
                f'- Submit rate {prof["submit_rate"]}% → messages often abandoned; '
                'check if previous answer landed before going deep'
            )
        if prof['avg_hes'] > 0.4:
            lines.append('- Hesitation > 0.4 → uncertain operator; proactively offer alternatives or examples')
        if prof['active_hours']:
            lines.append(f'- Active hours: {prof["active_hours"]}')
        lines.append('<!-- /pigeon:operator-state -->')
        block = '\n'.join(lines)

    try:
        text = cp_path.read_text(encoding='utf-8')
    except Exception:
        return False

    if not _OPERATOR_STATE_RE.search(text):
        return False  # Placeholder not present — don't auto-insert, location is hand-chosen

    cp_path.write_text(_OPERATOR_STATE_RE.sub(block, text), encoding='utf-8')
    return True
