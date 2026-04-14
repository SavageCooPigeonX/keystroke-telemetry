"""engagement_hooks_hook_generators_seq007_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 18 lines | ~162 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _dossier_awareness(ctx):
    d = ctx["dossier"]
    if not d or d.get("confidence", 0) < 0.5:
        return None
    focus = d.get("focus_modules", [])
    bugs = d.get("focus_bugs", [])
    if focus:
        mods = "`, `".join(focus[:3])
        bug_str = ", ".join(bugs) if bugs else "none flagged"
        return (
            f"Router matched this prompt to `{mods}` "
            f"(bugs: {bug_str}). Context slimmed to {len(focus)} modules. "
            "Wrong match? Say so. Right match? Go deeper.",
            3, "lure",
        )
    return None
