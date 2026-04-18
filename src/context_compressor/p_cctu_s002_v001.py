"""context_compressor_seq001_v001_token_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 4 lines | ~43 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _approx_tokens(text):
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))
