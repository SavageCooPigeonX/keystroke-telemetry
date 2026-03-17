"""Generate per-push narrative: each changed file speaks as its own agent."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v004 | 182 lines | ~1,654 tokens
# DESC:   generate_per_push_narrative_each
# INTENT: pulse_telemetry_prompt
# LAST:   2026-03-17 @ 9e2a305
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def generate_push_narrative(
    root: Path,
    intent: str,
    commit_hash: str,
    changed_py: list[str],
    registry: dict,
    rework_stats: dict | None = None,
    query_mem: dict | None = None,
    heat_map: dict | None = None,
    cross_context: dict | None = None,
) -> Path | None:
    """Build a development narrative from file-agent voices.

    Each changed file 'speaks' about why it was touched. Combined into
    a single markdown doc written to docs/push_narratives/.

    Returns the output path, or None if skipped/failed.
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key or not changed_py:
        return None

    file_briefs = _build_file_briefs(root, changed_py, registry)
    if not file_briefs:
        return None

    prompt = _build_narrative_prompt(intent, file_briefs, rework_stats, query_mem, heat_map, cross_context)
    prose = _call_deepseek(prompt, api_key)
    if not prose:
        return None

    out_dir = root / 'docs' / 'push_narratives'
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    out_path = out_dir / f'{today}_{commit_hash}.md'

    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    header = (
        f'# Push Narrative — {commit_hash}\n\n'
        f'**Intent**: {intent}  \n'
        f'**Date**: {now_str}  \n'
        f'**Files touched**: {len(changed_py)}  \n\n'
        f'---\n\n'
    )
    out_path.write_text(header + prose + '\n', encoding='utf-8')
    return out_path


def _build_file_briefs(root: Path, changed_py: list[str], registry: dict) -> list[dict]:
    """Extract identity + context for each changed file from registry."""
    briefs = []
    for rel in changed_py:
        entry = registry.get(rel)
        if not entry:
            continue
        briefs.append({
            'name': entry.get('name', Path(rel).stem),
            'path': rel,
            'seq': entry.get('seq', '?'),
            'ver': entry.get('ver', 0),
            'desc': entry.get('desc', ''),
            'intent': entry.get('intent', ''),
            'tokens': entry.get('tokens', 0),
            'history_len': len(entry.get('history', [])),
        })
    return briefs


def _build_narrative_prompt(
    intent: str,
    file_briefs: list[dict],
    rework_stats: dict | None,
    query_mem: dict | None,
    heat_map: dict | None,
    cross_context: dict | None = None,
) -> str:
    """Single batched prompt — all files voice themselves."""
    files_block = '\n'.join(
        f'- **{b["name"]}** (seq{b["seq"]:03d} v{b["ver"]:03d}, {b["tokens"]}tok): '
        f'desc="{b["desc"]}", last_intent="{b["intent"]}", {b["history_len"]} versions'
        for b in file_briefs
    )

    signals = []
    if rework_stats:
        signals.append(f'Rework: miss_rate={rework_stats.get("miss_rate", 0)}, '
                       f'worst={rework_stats.get("worst_queries", [])}')
    if query_mem:
        gaps = query_mem.get('persistent_gaps', [])
        abandons = query_mem.get('recent_abandons', [])
        if gaps:
            signals.append(f'Recurring queries: {[g.get("query", "") for g in gaps[:3]]}')
        if abandons:
            signals.append(f'Recent abandons: {abandons[:3]}')
    if heat_map:
        complex_files = heat_map.get('complex_files', [])
        if complex_files:
            signals.append(f'High-hesitation files: {[c["module"] for c in complex_files[:3]]}')

    signals_block = '\n'.join(signals) if signals else 'No deep signals available yet.'

    # Cross-file dependency context
    cross_block = ''
    if cross_context:
        cross_lines = []
        for rel, ctx in cross_context.items():
            name = Path(rel).stem.split('_seq')[0]
            deps = ', '.join(Path(d).stem.split('_seq')[0] for d in ctx.get('imports_from', []))
            users = ', '.join(Path(u).stem.split('_seq')[0] for u in ctx.get('imported_by', []))
            parts = []
            if deps:
                parts.append(f'depends on [{deps}]')
            if users:
                parts.append(f'used by [{users}]')
            if parts:
                cross_lines.append(f'- {name}: {"; ".join(parts)}')
        if cross_lines:
            cross_block = f'\n\nCROSS-FILE DEPENDENCIES:\n' + '\n'.join(cross_lines)

    return (
        f'You are writing a development narrative for a code push.\n\n'
        f'COMMIT INTENT: {intent}\n\n'
        f'FILES CHANGED:\n{files_block}\n\n'
        f'OPERATOR DEEP SIGNALS:\n{signals_block}{cross_block}\n\n'
        f'INSTRUCTIONS:\n'
        f'Write a short development narrative (150-250 words). '
        f'Each changed file "speaks" in first person — one paragraph each — '
        f'explaining why it was touched and what it suspects about its own bugs '
        f'or technical debt based on its version history and the commit intent. '
        f'If cross-file dependencies are shown, each file should mention HOW '
        f'it relates to its neighbors — what it gives, what it receives, and '
        f'potential breakage if either side changes. '
        f'End with a 2-sentence summary of what this push accomplishes. '
        f'Use direct, technical prose. No markdown headers — just paragraphs.'
    )


def _call_deepseek(prompt: str, api_key: str) -> str | None:
    """Single DeepSeek call for the narrative."""
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.5,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None
