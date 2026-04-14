"""探p_ur_s024_v002_d0329_读唤任_λS_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 22 lines | ~274 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

DELETION_THRESHOLD = 0.15  # 15%+ deletion = uncertainty signal — fires reconstruction

INTENT_DELETE_MIN_RUN = 5  # 5+ consecutive backspaces = intent change (matches composition analyzer)

GEMINI_MODEL = 'gemini-2.5-flash'

GEMINI_TIMEOUT = 4  # seconds — must be fast, runs synchronously on Enter


SYSTEM_PROMPT = (
    "You are an intent reconstruction engine. The operator typed a prompt to an AI coding assistant "
    "but deleted some words/phrases before submitting. Your job: reconstruct what they ACTUALLY "
    "wanted to say — the full unfiltered intent combining both the submitted text and deleted fragments.\n\n"
    "Rules:\n"
    "- Output a single sentence: the reconstructed full intent\n"
    "- Be specific and actionable — this will be injected as a custom instruction\n"
    "- If deleted words seem like typos, ignore them\n"
    "- If deleted words reveal a suppressed request, surface it\n"
    "- No explanations, no preamble — just the reconstructed intent sentence"
)
