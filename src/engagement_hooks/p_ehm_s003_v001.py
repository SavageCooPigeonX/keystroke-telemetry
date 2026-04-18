"""engagement_hooks_seq001_v001_mood_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 29 lines | ~245 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _mood(ctx, history):
    if not history:
        return "new"
    recent_states = [h.get("state", "neutral") for h in history[-10:]]
    abandon_count = recent_states.count("abandoned")
    frust_count = recent_states.count("frustrated")
    focus_count = recent_states.count("focused")
    recent_del = [h.get("del_ratio", 0) for h in history[-5:]]
    avg_del = sum(recent_del) / max(len(recent_del), 1)

    if abandon_count >= 4:
        return "spiraling"
    if frust_count >= 3 and avg_del > 0.3:
        return "spiraling"
    if frust_count >= 3:
        return "combative"
    if focus_count >= 5 and avg_del < 0.1:
        return "locked_in"
    if focus_count >= 3:
        return "flow"
    if len(history) > 40 and ctx["hour"] >= 22:
        return "marathon"
    if len(history) > 50:
        return "entrenched"
    if len(history) < 3:
        return "new"
    return "cruising"
