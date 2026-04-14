"""Operator state block builder + inject_operator_state + inject_entropy_layers."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 199 lines | ~1,831 tokens
# DESC:   operator_state_block_builder_inject
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from __future__ import annotations
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

_COPILOT_PATH = '.github/copilot-instructions.md'

_STATE_HINTS: dict[str, str] = {
    'frustrated': 'concise answers, 2-3 options max, bullets, lead with solution',
    'hesitant': 'warm tone, anticipate intent, ask one follow-up question',
    'flow': 'match energy - full technical depth, no hand-holding',
    'focused': 'thorough and structured, match effort level',
    'restructuring': 'precise, use headers/numbered lists to mirror their effort',
    'abandoned': 'welcoming, direct - they re-approached after backing off',
    'neutral': 'standard response style',
}

# ── duplicated micro-utilities ────────────────────────────────────────────────

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def _upsert_block(text: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    pattern = re.compile(rf'(?ms)^\s*{re.escape(start)}\s*$\n.*?^\s*{re.escape(end)}\s*$')
    if pattern.search(text):
        return pattern.sub(block, text)
    if anchor and anchor in text:
        m = re.compile(rf'(?m)^\s*{re.escape(anchor)}\s*$').search(text)
        if m:
            return text[:m.end()] + '\n\n' + block + text[m.end():]
    return text.rstrip() + '\n\n' + block + '\n'

# ── profile / coaching loaders ────────────────────────────────────────────────

def _parse_operator_profile(root: Path) -> dict | None:
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return None
    try:
        text = prof_path.read_text(encoding='utf-8')
    except Exception:
        return None

    def _re(pattern: str, default: str) -> str:
        m = re.search(pattern, text)
        return m.group(1) if m else default

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
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        if time.time() - coaching_path.stat().st_mtime > max_age_s:
            return None
        text = coaching_path.read_text(encoding='utf-8')
        m = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        return None
    return None

# ── builder ───────────────────────────────────────────────────────────────────

def _build_operator_state_block(root: Path) -> str | None:
    profile = _parse_operator_profile(root)
    if not profile or profile['messages'] == 0:
        return None

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    dominant = profile['dominant']
    coaching_prose = _load_coaching_prose(root)
    header = (
        f'**Dominant: `{dominant}`** '
        f'| Submit: {profile["submit_rate"]}% '
        f'| WPM: {profile["avg_wpm"]:.1f} '
        f'| Del: {profile["avg_del"]:.1f}% '
        f'| Hes: {profile["avg_hes"]:.3f}'
    )
    if coaching_prose:
        return '\n'.join([
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} - {profile["messages"]} message(s) - LLM-synthesized*',
            '',
            header,
            '',
            coaching_prose,
            '',
            '<!-- /pigeon:operator-state -->',
        ])

    hint = _STATE_HINTS.get(dominant, _STATE_HINTS['neutral'])
    lines = [
        '<!-- pigeon:operator-state -->',
        '## Live Operator State',
        '',
        f'*Auto-updated {today} - {profile["messages"]} message(s) in profile*',
        '',
        header,
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
            f'- Submit rate {profile["submit_rate"]}% -> messages often abandoned; '
            'check if previous answer landed before going deep'
        )
    if profile['avg_hes'] > 0.4:
        lines.append('- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples')
    if profile['active_hours']:
        lines.append(f'- Active hours: {profile["active_hours"]}')
    lines.append('<!-- /pigeon:operator-state -->')
    return '\n'.join(lines)

# ── injectors ─────────────────────────────────────────────────────────────────

def inject_operator_state(root: Path) -> bool:
    cp_path = root / _COPILOT_PATH
    if not cp_path.exists():
        return False
    block = _build_operator_state_block(root)
    if not block:
        return False
    text = cp_path.read_text(encoding='utf-8')
    new_text = _upsert_block(
        text,
        '<!-- pigeon:operator-state -->',
        '<!-- /pigeon:operator-state -->',
        block,
        anchor='<!-- /pigeon:task-queue -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_entropy_layers(root: Path) -> bool:
    cp_path = root / _COPILOT_PATH
    if not cp_path.exists():
        return False
    try:
        from src.entropy_shedding import build_entropy_block, build_red_layer_block, build_entropy_directive
    except Exception:
        return False

    text = cp_path.read_text(encoding='utf-8')
    new_text = _upsert_block(
        text,
        '<!-- pigeon:entropy-map -->',
        '<!-- /pigeon:entropy-map -->',
        build_entropy_block(root),
        anchor='<!-- pigeon:bug-voices -->',
    )
    new_text = _upsert_block(
        new_text,
        '<!-- pigeon:entropy-red-layer -->',
        '<!-- /pigeon:entropy-red-layer -->',
        build_red_layer_block(root),
        anchor='<!-- pigeon:bug-voices -->',
    )
    directive = build_entropy_directive(root)
    if directive:
        new_text = _upsert_block(
            new_text,
            '<!-- pigeon:entropy-directive -->',
            '<!-- /pigeon:entropy-directive -->',
            '<!-- pigeon:entropy-directive -->\n' + directive + '\n<!-- /pigeon:entropy-directive -->',
            anchor='<!-- pigeon:entropy-map -->',
        )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
        return True
    return False
