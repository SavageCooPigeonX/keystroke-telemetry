"""push_snapshot_seq001_v001_inject_drift_decomposed_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 76 lines | ~732 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

def inject_drift_block(root: Path, snapshot: dict, drift_result: dict):
    """Inject the latest drift analysis into copilot-instructions.md."""
    ci_path = root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return

    d = drift_result.get('drift', {})
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    lines = [BLOCK_START]
    lines.append('## Push Drift Analysis')
    lines.append('')
    lines.append(f'*Snapshot at `{snapshot.get("commit", "?")}` · {ts}*')
    lines.append('')

    # Health headline
    health = d.get('health_score', 0)
    direction = d.get('health_direction', 'stable')
    prev = d.get('prev_health_score')
    if prev is not None:
        lines.append(f'**Health: {health}/100** ({direction}, was {prev})')
    else:
        lines.append(f'**Health: {health}/100** (first snapshot)')
    lines.append('')

    # Key deltas
    if d.get('biggest_moves'):
        lines.append('**Biggest moves:**')
        for move in d['biggest_moves']:
            lines.append(f'- {move}')
        lines.append('')

    # Numbers
    m = snapshot.get('modules', {})
    b = snapshot.get('bugs', {})
    f = snapshot.get('file_stats', {})
    lines.append(f'**Modules:** {m.get("total", 0)} ({m.get("compliance_pct", 0)}% compliant)')
    lines.append(f'**Bugs:** {b.get("total", 0)} (hi={b.get("hardcoded_import", 0)} oc={b.get("over_hard_cap", 0)})')
    lines.append(f'**Avg tokens/file:** {f.get("avg_tokens", 0)} ({d.get("bloat_direction", "unknown")})')
    lines.append(f'**Deaths:** {snapshot.get("deaths", {}).get("total", 0)}')
    lines.append(f'**Sync:** {snapshot.get("cycle", {}).get("sync_score", 0)}')
    lines.append(f'**Probes:** {snapshot.get("probes", {}).get("modules_probed", 0)} modules, {snapshot.get("probes", {}).get("total_intents_extracted", 0)} intents')
    lines.append('')

    # Hours since last push
    hrs = d.get('hours_since_last_push')
    if hrs:
        lines.append(f'*{hrs}h since last push*')
        lines.append('')

    lines.append(BLOCK_END)
    block = '\n'.join(lines)

    content = ci_path.read_text('utf-8')
    start_idx = content.find(BLOCK_START)
    end_idx = content.find(BLOCK_END)

    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + block + content[end_idx + len(BLOCK_END):]
    else:
        # Insert before predictions block
        marker = '<!-- pigeon:predictions -->'
        idx = content.find(marker)
        if idx == -1:
            marker = '<!-- pigeon:operator-state -->'
            idx = content.find(marker)
        if idx >= 0:
            content = content[:idx] + block + '\n' + content[idx:]
        else:
            content += '\n\n' + block

    ci_path.write_text(content, 'utf-8')
