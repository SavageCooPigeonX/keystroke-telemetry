"""缩p_fdt_s006_v002_d0323_描环检意_λP_classify_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 50 lines | ~424 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def classify_death(electron: dict) -> dict:
    """Classify an electron's death from its lifecycle data.

    Returns {cause, severity, node, score, detail}
    """
    status = electron.get("status", "")
    death_cause = electron.get("death_cause", "")
    path = electron.get("path", [])
    loop_count = electron.get("loop_count", 0)
    total_errors = electron.get("total_errors", 0)
    total_calls = electron.get("total_calls", 0)

    # Determine node where death occurred
    death_node = path[-1] if path else "unknown"

    if death_cause == "stale_import":
        severity = "critical"
        score = 0.9
        detail = f"Stale import killed electron at {death_node}"
    elif death_cause == "timeout":
        severity = "high"
        score = 0.7
        detail = f"Timeout after {total_calls} calls at {death_node}"
    elif loop_count > 0:
        severity = "high"
        score = 0.65
        detail = f"Loop detected: {loop_count} revisits, died at {death_node}"
    elif death_cause == "max_attempts":
        severity = "medium"
        score = 0.5
        detail = f"Max attempts reached at {death_node}"
    elif death_cause == "exception":
        severity = "high"
        score = 0.75
        detail = f"Exception at {death_node} after {total_calls} calls"
    else:
        severity = "low"
        score = 0.3
        detail = f"Unknown death at {death_node}"

    return {
        "cause": death_cause or "unknown",
        "severity": severity,
        "node": death_node,
        "score": score,
        "detail": detail,
        "path_length": len(path),
    }
