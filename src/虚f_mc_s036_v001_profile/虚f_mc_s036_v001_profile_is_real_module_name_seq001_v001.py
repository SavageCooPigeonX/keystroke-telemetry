"""虚f_mc_s036_v001_profile_is_real_module_name_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 6 lines | ~54 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def is_real_module_name(name: str) -> bool:
    if len(name.split('_')) > 4:
        return False
    return True
