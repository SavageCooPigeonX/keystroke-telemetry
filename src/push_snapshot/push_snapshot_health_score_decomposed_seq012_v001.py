"""push_snapshot_health_score_decomposed_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 60 lines | ~489 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _compute_health_score(snapshot: dict) -> float:
    """Compute an overall health score (0-100) from snapshot metrics.

    Weighted composite — higher = healthier codebase.
    Token thresholds use ~10 tokens/line ratio for pigeon standard alignment.
    """
    score = 50.0  # baseline

    # Compliance (+25 max)
    compliance = snapshot.get('modules', {}).get('compliance_pct', 0)
    score += (compliance / 100) * 25

    # Bug penalty (-20 max)
    total_bugs = snapshot.get('bugs', {}).get('total', 0)
    total_modules = max(snapshot.get('modules', {}).get('total', 1), 1)
    bug_ratio = min(total_bugs / total_modules, 1.0)
    score -= bug_ratio * 20

    # File size bonus (+10 max) — reward small files
    # Token thresholds: 500 ≈ 50 lines (target), 2000 ≈ 200 lines (cap)
    avg_tokens = snapshot.get('file_stats', {}).get('avg_tokens', 500)
    if avg_tokens <= 500:
        score += 10
    elif avg_tokens <= 2000:
        score += 5
    elif avg_tokens > 5000:
        score -= 5

    # Death penalty (-5 max)
    deaths = snapshot.get('deaths', {}).get('total', 0)
    score -= min(deaths * 0.5, 5)

    # Sync bonus (+10 max) — stepped scale for behavioral metric
    sync = snapshot.get('cycle', {}).get('sync_score', 0)
    if sync >= 0.5:
        score += 10
    elif sync >= 0.1:
        score += 8
    elif sync >= 0.03:
        score += 5
    elif sync > 0:
        score += 3

    # Probe engagement bonus (+5 max)
    probed = snapshot.get('probes', {}).get('modules_probed', 0)
    if probed > 10:
        score += 5
    elif probed > 0:
        score += 2

    # Heat penalty (-5 max) — high average hesitation = cognitive debt
    avg_hes = snapshot.get('heat', {}).get('avg_hesitation', 0)
    if avg_hes > 0.6:
        score -= 5
    elif avg_hes > 0.4:
        score -= 2

    return round(max(0, min(100, score)), 1)
