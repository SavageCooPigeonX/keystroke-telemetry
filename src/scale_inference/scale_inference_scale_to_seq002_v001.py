"""scale_inference_scale_to_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 32 lines | ~308 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def scale_to_token_budget(scale: int) -> int:
    """Map scale to approximate max output tokens for LLM B."""
    return {1: 150, 2: 600, 3: 2000, 4: 4000}.get(scale, 600)


def scale_to_instructions(scale: int) -> str:
    """Generate scale-specific instructions for LLM B."""
    if scale == 1:
        return (
            "Output: ONE sentence. The insight, the answer, the fact. "
            "No code unless the answer IS code. No explanation."
        )
    elif scale == 2:
        return (
            "Output: ONE paragraph. Explanation + code sketch if relevant + "
            "affected files. Enough to understand before committing."
        )
    elif scale == 3:
        return (
            "Output: FULL implementation. Complete code patch + test cases + "
            "manifest updates + push narrative. Don't explain — DO."
        )
    elif scale == 4:
        return (
            "Output: FULL technical document. Architecture rationale. "
            "Alternatives considered. Migration plan. Risk analysis. "
            "Code examples. Integration steps."
        )
    return "Output: brief, contextual response."
