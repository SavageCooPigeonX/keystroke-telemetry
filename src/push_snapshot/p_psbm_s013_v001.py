"""push_snapshot_seq001_v001_biggest_moves_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 26 lines | ~323 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _biggest_moves(drift: dict) -> list[str]:
    """Identify the biggest drift metrics for narrative generation."""
    moves = []
    if abs(drift.get('compliance_delta', 0)) > 2:
        d = drift['compliance_delta']
        moves.append(f"compliance {'up' if d > 0 else 'down'} {abs(d):.1f}%")
    if abs(drift.get('bugs_delta', 0)) > 5:
        d = drift['bugs_delta']
        moves.append(f"bugs {'up' if d > 0 else 'down'} {abs(d)}")
    if abs(drift.get('avg_tokens_delta', 0)) > 20:
        d = drift['avg_tokens_delta']
        moves.append(f"avg file size {'grew' if d > 0 else 'shrank'} {abs(d):.0f} tokens")
    if abs(drift.get('health_delta', 0)) > 3:
        d = drift['health_delta']
        moves.append(f"health {'up' if d > 0 else 'down'} {abs(d):.1f} pts")
    if drift.get('deaths_delta', 0) > 0:
        moves.append(f"{drift['deaths_delta']} new execution deaths")
    if drift.get('intents_delta', 0) > 0:
        moves.append(f"{drift['intents_delta']} new operator intents extracted")
    if drift.get('probes_delta', 0) > 0:
        moves.append(f"{drift['probes_delta']} new probe conversations")
    if not moves:
        moves.append('no significant drift')
    return moves
