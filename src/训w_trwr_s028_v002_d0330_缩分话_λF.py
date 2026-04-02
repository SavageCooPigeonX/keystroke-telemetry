"""training_writer_seq028_v001.py — End-of-prompt training pair writer.

At the end of every copilot prompt→response cycle, captures the muxed state:
- operator prompt (raw)
- copilot response (summary)
- cognitive state at prompt time (wpm, deletion, hesitation, state)
- which shards were routed (names + relevance scores)
- active contradictions
- rework verdict (when available, backfilled)

Writes to logs/shards/training_pairs.md as human-readable markdown.
The anchor: pair programming. Copilot is the pair. This is the shared notebook.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 028 | VER: v002 | 251 lines | ~2,113 tokens
# DESC:   end_of_prompt_training_pair
# INTENT: gemini_flash_enricher
# LAST:   2026-03-30 @ 5018891
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-30T06:35:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add per-shard training categorization
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import json
import re
from pathlib import Path
from src._resolve import src_import
from datetime import datetime, timezone

TRAINING_FILE = 'logs/shards/training_pairs.md'
MAX_PROMPT_CHARS = 300
MAX_RESPONSE_CHARS = 500
MAX_PAIRS = 500
MAX_SHARD_TRAINING_ENTRIES = 100  # per shard


def _jload(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception:
        return None


def _now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')


def _get_cognitive_state(root: Path) -> dict:
    snap = _jload(root / 'logs' / 'prompt_telemetry_latest.json')
    if not snap:
        return {}
    signals = snap.get('signals', {})
    summary = snap.get('running_summary', {})
    return {
        'state': summary.get('dominant_state', 'unknown'),
        'wpm': round(signals.get('wpm', 0), 1),
        'del_ratio': round(signals.get('deletion_ratio', 0), 3),
        'hes': signals.get('hesitation_count', 0),
    }


def _get_routed_shards(root: Path, query: str) -> list[dict]:
    try:
        route_context = src_import("context_router_seq027", "route_context")
        return route_context(root, query)
    except Exception:
        return []


def _get_contradictions(root: Path) -> int:
    try:
        get_unresolved_contradictions = src_import("shard_manager_seq026", "get_unresolved_contradictions")
        return len(get_unresolved_contradictions(root))
    except Exception:
        return 0


def write_training_pair(root: Path, prompt: str, response: str,
                        verdict: str = 'pending',
                        rework_score: float | None = None) -> bool:
    """Write one training pair with full muxed state to training_pairs.md.

    Called at the end of each copilot prompt→response cycle.
    """
    root = Path(root)
    ts = _now()

    # gather muxed state
    cog = _get_cognitive_state(root)
    routed = _get_routed_shards(root, prompt)
    n_contradictions = _get_contradictions(root)

    # format shard hits
    shard_hits = ', '.join(
        f"{r['name']}({r['relevance']})" for r in routed
    ) or 'none'

    # format cognitive line
    cog_line = (
        f"state={cog.get('state', '?')} "
        f"wpm={cog.get('wpm', 0)} "
        f"del={cog.get('del_ratio', 0)} "
        f"hes={cog.get('hes', 0)}"
    ) if cog else 'unavailable'

    # truncate for readability
    prompt_display = prompt[:MAX_PROMPT_CHARS]
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt_display += '...'
    response_display = response[:MAX_RESPONSE_CHARS]
    if len(response) > MAX_RESPONSE_CHARS:
        response_display += '...'

    # rework line
    rework_line = f"verdict={verdict}"
    if rework_score is not None:
        rework_line += f" score={rework_score:.2f}"

    block = (
        f'\n### `{ts}` pair\n\n'
        f'**PROMPT:** {prompt_display}\n\n'
        f'**RESPONSE:** {response_display}\n\n'
        f'**COGNITIVE:** {cog_line}\n\n'
        f'**SHARDS:** {shard_hits}\n\n'
        f'**CONTRADICTIONS:** {n_contradictions}\n\n'
        f'**REWORK:** {rework_line}\n\n'
        f'---\n'
    )

    p = root / TRAINING_FILE
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        header = (
            '# Training Pairs\n\n'
            '> Anchor: pair programming. Copilot is the pair. '
            'This is the shared notebook.\n'
            '> Each entry captures: prompt + response + muxed cognitive state.\n\n'
            '---\n'
        )
        p.write_text(header + block, 'utf-8')
    else:
        # check pair count, trim oldest if over limit
        existing = p.read_text('utf-8', errors='ignore')
        pair_count = existing.count('### `')
        if pair_count >= MAX_PAIRS:
            # trim first pair block
            first_pair = existing.find('\n### `')
            if first_pair >= 0:
                second_pair = existing.find('\n### `', first_pair + 1)
                if second_pair >= 0:
                    existing = existing[:first_pair] + existing[second_pair:]
                    p.write_text(existing, 'utf-8')

        with open(p, 'a', encoding='utf-8') as f:
            f.write(block)

    # ── per-shard categorized training entries ──
    _write_per_shard_entries(root, ts, prompt_display, response_display,
                            cog_line, verdict, rework_score, routed)

    return True


def _write_per_shard_entries(root: Path, ts: str, prompt: str, response: str,
                             cog_line: str, verdict: str,
                             rework_score: float | None, routed: list[dict]) -> None:
    """Append a compact training entry to each routed shard's file.

    Each shard accumulates training data relevant to its topic — so the shard
    becomes a self-learning context bank, not just static facts.
    """
    for shard in routed:
        name = shard.get('name', '')
        relevance = shard.get('relevance', 0)
        if not name or relevance < 0.05:
            continue

        shard_path = root / 'logs' / 'shards' / f'{name}.md'
        if not shard_path.exists():
            continue

        rework_str = f"verdict={verdict}"
        if rework_score is not None:
            rework_str += f" score={rework_score:.2f}"

        entry = (
            f'\n- **[training {ts}]** relevance={relevance} | {cog_line} | '
            f'{rework_str}\n'
            f'  - prompt: {prompt[:150]}\n'
            f'  - response: {response[:150]}\n'
        )

        # trim if over limit
        existing = shard_path.read_text('utf-8', errors='ignore')
        training_count = existing.count('[training ')
        if training_count >= MAX_SHARD_TRAINING_ENTRIES:
            # remove oldest training entry
            idx = existing.find('\n- **[training ')
            if idx >= 0:
                next_idx = existing.find('\n- ', idx + 1)
                if next_idx >= 0:
                    existing = existing[:idx] + existing[next_idx:]
                    shard_path.write_text(existing, 'utf-8')

        with open(shard_path, 'a', encoding='utf-8') as f:
            f.write(entry)


def backfill_rework(root: Path, prompt_hint: str, verdict: str, score: float) -> bool:
    """Backfill rework verdict into the most recent matching training pair."""
    root = Path(root)
    p = root / TRAINING_FILE
    if not p.exists():
        return False

    text = p.read_text('utf-8', errors='ignore')
    hint = prompt_hint[:80]

    # find last pair with this prompt hint that still says pending
    pattern = re.compile(
        r'(\*\*PROMPT:\*\*\s*' + re.escape(hint[:40]) + r'.*?\n\n'
        r'.*?'
        r'\*\*REWORK:\*\*\s*)verdict=pending',
        re.DOTALL
    )
    match = None
    for m in pattern.finditer(text):
        match = m  # take the last match

    if not match:
        return False

    replacement = f'{match.group(1)}verdict={verdict} score={score:.2f}'
    text = text[:match.start()] + replacement + text[match.end():]
    p.write_text(text, 'utf-8')
    return True


if __name__ == '__main__':
    root = Path('.')
    ok = write_training_pair(
        root,
        prompt='test writes with an actual call using this prompt',
        response='built training pair writer, muxed state captured per prompt',
    )
    print(f'Write OK: {ok}')
