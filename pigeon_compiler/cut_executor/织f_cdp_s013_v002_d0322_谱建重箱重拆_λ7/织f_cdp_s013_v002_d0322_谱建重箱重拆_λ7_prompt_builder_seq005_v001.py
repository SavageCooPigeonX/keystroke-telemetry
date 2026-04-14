"""织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_prompt_builder_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 37 lines | ~535 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _build_prompt(class_source: str, class_name: str,
                  line_count: int, context: str = "") -> str:
    """Build a CODING prompt to refactor one large class."""
    ctx_block = (
        f"EXISTING CODE ABOVE THE CLASS (DO NOT REPEAT THIS — it stays in the file):\n\n"
        f"{context}\n\n"
    ) if context else ""
    return (
        "You are the Pigeon Code Compiler. Refactor this oversized class "
        "into a THIN class + standalone module-level functions.\n\n"
        "RULES:\n"
        "- Extract methods that compute or render into STANDALONE module-level functions.\n"
        "  Replace self.xxx references with explicit parameters.\n"
        "- The class keeps: __init__, simple state-management methods,\n"
        "  and delegates to the extracted functions.\n"
        "- Each extracted function MUST be ≤50 lines.\n"
        "- The remaining class MUST be ≤80 lines.\n"
        "- Preserve EXACT behavior — no logic changes.\n"
        "- Extracted functions receive data as parameters, NOT self.\n"
        "- Keep the same class NAME and public API (method signatures unchanged from caller's view).\n"
        "- Private methods like _render, _compute, _format → module-level functions.\n"
        "- Return ONLY valid Python code — NO markdown fences, NO comments like '```python'.\n"
        "- Do NOT re-include imports, constants, or helper functions that exist ABOVE the class.\n"
        "  They already exist in the file. ONLY output the NEW extracted functions\n"
        "  and the refactored thin class.\n"
        "- If extracted functions need imports not already in context, add ONLY those new imports.\n\n"
        + ctx_block
        + f"CLASS TO REFACTOR ({line_count} lines):\n\n"
        f"{class_source}\n\n"
        "Output ONLY:\n"
        "1. Any NEW imports needed by extracted functions (not already above)\n"
        "2. The extracted standalone functions\n"
        "3. The thin class that delegates to them\n"
        "No markdown fences. No duplicate code."
    )
