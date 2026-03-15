"""func_decomposer_seq008_v001.py — Decompose oversized functions via DeepSeek.

For functions >50 lines, sends a CODING prompt to DeepSeek asking it to
rewrite the function as sub-functions + wrapper. Returns modified source.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v004 | 67 lines | ~641 tokens
# DESC:   decompose_oversized_functions_via_deepseek
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import json, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED


def find_oversized(ether_map: dict) -> list:
    """Return functions that exceed PIGEON_MAX lines."""
    return [f for f in ether_map.get("functions", [])
            if f["line_count"] > PIGEON_MAX]


def build_decompose_prompt(func_source: str, func_name: str,
                           line_count: int, context: str = "") -> str:
    """Build a CODING prompt to decompose one large function."""
    return f"""You are the Pigeon Code Compiler. Decompose this oversized function
into MULTIPLE smaller functions.

RULES:
- Each helper function ≤30 lines
- Wrapper function (same name: {func_name}) ≤25 lines — just calls helpers
- Preserve EXACT behavior — no logic changes
- Keep the same function signature for {func_name}()
- Prefix helpers with _{func_name}_ (private)
- Return ONLY Python code, no markdown

FUNCTION TO DECOMPOSE ({line_count} lines → needs {line_count // 30 + 1} pieces):

```python
{func_source}
```

{f"CONTEXT (imports/constants this function uses):{chr(10)}{context}" if context else ""}

Write the decomposed Python code. Include ALL helpers + the wrapper.
No markdown fences. Just Python."""


def decompose_function(func_source: str, func_name: str,
                       line_count: int, context: str = "") -> str:
    """Send function to DeepSeek for decomposition. Returns Python code."""
    from pigeon_compiler.integrations.deepseek_adapter_seq001_v004_d0315__deepseek_api_client_lc_verify_pigeon_plugin import deepseek_query

    prompt = build_decompose_prompt(func_source, func_name, line_count, context)
    result = deepseek_query(prompt, max_tokens=6000)
    code = result.get("content", "")
    # Strip any markdown fences DeepSeek might add
    if code.startswith("```"):
        lines = code.split('\n')
        code = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    return code.strip()
