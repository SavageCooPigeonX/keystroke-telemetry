"""deepseek_plan_prompt_seq004_v001.py — Build and send DeepSeek cut plan.

Takes ether map + source, builds prompt with HARD line constraints,
calls DeepSeek, validates response, returns JSON cut plan.

v0.2.0 fixes:
- Bug 1: Hard line counts injected (no hallucination)
- Bug 2: Recursive decomposition for >50 line functions
- Bug 3: Naming convention enforced via prefix
- Bug 4: PROMPT_BLOB extraction strategy demanded
- Bug 5: Cluster depth replaces binary clustering
- Bug 6: Post-validation of estimated_lines vs actual
"""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v003 | 251 lines | ~2,407 tokens
# DESC:   build_and_send_deepseek_cut
# INTENT: desc_upgrade
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _oversized_table(funcs: list) -> str:
    """Build warning table for functions >50 lines."""
    big = [f for f in funcs if f['line_count'] > 50]
    if not big:
        return "None — all functions fit in ≤50 lines."
    lines = []
    for f in sorted(big, key=lambda x: -x['line_count']):
        lines.append(f"  - {f['name']}(): {f['line_count']} lines ← MUST DECOMPOSE")
    return "\n".join(lines)


def _line_count_map(funcs: list) -> str:
    """Build exact line count reference for all functions."""
    return "\n".join(
        f"  {f['name']}: {f['line_count']} lines"
        for f in sorted(funcs, key=lambda x: -x['line_count'])
    )


def _class_line_count_map(classes: list) -> str:
    """Build exact line count reference for all classes."""
    if not classes:
        return "  (no classes)"
    lines = []
    for c in sorted(classes, key=lambda x: -(x.get('end_line', 0) - x.get('start_line', 0))):
        lc = c.get('end_line', 0) - c.get('start_line', 0) + 1
        methods = c.get('methods', [])
        lines.append(f"  {c['name']}: {lc} lines, methods: {methods}")
    return "\n".join(lines)


def _call_depth_section(ether_map: dict) -> str:
    """Build call depth section showing extraction difficulty per function."""
    depths = ether_map.get('call_depth', {})
    if not depths:
        return "No call depth data available."
    lines = []
    for fn, d in sorted(depths.items(), key=lambda x: -x[1]):
        label = "GOD" if d == 0 else f"depth {d}" if d < 999 else "ISOLATED"
        ease = "🟢 easy" if d >= 2 else "🟡 moderate" if d == 1 else "🔴 core"
        lines.append(f"  {fn}: {label} — {ease} extraction target")
    return "\n".join(lines)


def _prompt_blob_section(resistance: dict) -> str:
    """Build PROMPT_BLOB extraction strategy demand."""
    blobs = [p for p in resistance.get('patterns', [])
             if p['pattern'] == 'PROMPT_BLOB']
    if not blobs:
        return "No PROMPT_BLOBs detected."
    lines = ["PROMPT_BLOBs detected — you MUST specify an extraction strategy:"]
    for b in blobs:
        lines.append(f"  - {b['detail']}")
    lines.append("")
    lines.append("For EACH blob, choose ONE strategy:")
    lines.append("  a) Extract to a constants file (PROMPT_TEMPLATES dict)")
    lines.append("  b) Builder function that returns the string (<30 lines)")
    lines.append("  c) Template loaded from file at runtime")
    lines.append("Include your choice in the cut's 'reason' field.")
    return "\n".join(lines)


def _dead_exports_section(exclude_symbols: list[str]) -> str:
    """Build dead-export exclusion block for the prompt."""
    if not exclude_symbols:
        return ''
    names = ', '.join(f'`{n}`' for n in exclude_symbols)
    return f"""\n═══════════════ DEAD EXPORTS — PRUNE THESE (never include in any cut) ═══════════════

The following functions are confirmed dead exports — no caller exists anywhere in the
codebase. DO NOT include them in any cut's "functions" list. DO NOT add them to
init_exports. They should be deleted, not moved.

DEAD (omit entirely): {names}
"""


def build_plan_prompt(ether_map: dict, source: str,
                      folder_name: str = None,
                      exclude_symbols: list[str] | None = None) -> str:
    """Build the DeepSeek compiler prompt from an ether map."""
    em = ether_map
    r = em.get("resistance", {})
    stem = Path(em['file']).stem
    prefix = folder_name or stem

    return f"""You are the Pigeon Code Compiler. Produce an EXACT file-split plan as JSON.

🐦 HARD RULES (violating ANY = rejected plan):
- MAX 50 lines per file (imports + docstring + code = ≤50)
- Imports + docstring overhead = ~8 lines. So function code MUST total ≤35 lines per file.
- NEVER group functions whose combined line_count > 35
- If a single function is >35 lines, it MUST be the ONLY code in its file
- If a single function is >50 lines, you MUST decompose it into sub-functions
- Naming: {prefix}_[desc]_seqNNN_v001.py  ← PREFIX IS MANDATORY
- One responsibility per file
- No circular imports
- __init__.py re-exports all public names
- seqNNN = execution order in the pipeline

═══════════════ MEASURED LINE COUNTS (AST — exact, not estimates) ═══════════════

FUNCTIONS:
{_line_count_map(em['functions'])}

CLASSES (each class = ONE file, use "classes" key in JSON):
{_class_line_count_map(em.get('classes', []))}

⚠️  GROUPING BUDGET: If you put functions A (20 lines) + B (18 lines) in one file,
that's 38 lines of code + ~8 lines imports/docstring = 46 total. BARELY fits.
If combined code > 35, use SEPARATE files. Do the math for every proposed group.

⚠️  OVERSIZED FUNCTIONS (>50 lines — MUST be decomposed into sub-functions):
{_oversized_table(em['functions'])}

For each oversized function:
  1. Propose sub-functions the wrapper calls
  2. Each sub-function ≤30 lines
  3. Wrapper ≤20 lines
  4. Group sub-functions + wrapper in same seq file only if total ≤50

═══════════════ CALL DEPTH (extraction difficulty — GOD = hardest) ═══════════════

{_call_depth_section(em)}

Functions at depth ≥2 or ISOLATED are the EASIEST to extract first.
Functions at depth 0-1 are tightly coupled to the orchestrator.

═══════════════ PROMPT_BLOB STRATEGY ═══════════════

{_prompt_blob_section(r)}

{_dead_exports_section(exclude_symbols or [])}
═══════════════ ETHER MAP ═══════════════

File: {em['file']} ({em['total_lines']} lines)
Resistance: {r.get('score', '?')}/1.0 → {r.get('verdict', '?')}

CALL GRAPH:
{json.dumps(em['call_graph'], indent=2)}

CLUSTERS: {json.dumps(em['clusters'])}

CONSTANTS: {json.dumps(em['constants'], indent=2)}

SHARED STATE: {json.dumps(em['shared_state'], indent=2, default=str)}

RESISTANCE PATTERNS: {json.dumps(r.get('patterns', []), indent=2)}

IMPORTS (outbound): {json.dumps(em['imports']['outbound'], indent=2)}
IMPORTS (inbound): {json.dumps(em['imports']['inbound'], indent=2)}

═══════════════ SOURCE CODE ═══════════════

```python
{source}
```

═══════════════ OUTPUT FORMAT (strict JSON, no markdown) ═══════════════

{{
  "source_file": "{em['file']}",
  "target_folder": "{prefix}/",
  "strategy": "<one-line>",
  "cuts": [
    {{
      "new_file": "{prefix}_desc_seqNNN_v001.py",
      "functions": ["function names to MOVE here"],
      "classes": ["class names to MOVE here"],
      "constants": ["NAMES to MOVE here"],
      "new_helpers": ["new sub-functions YOU create to decompose oversized funcs"],
      "estimated_lines": <int>,
      "reason": "WHY (include PROMPT_BLOB strategy if applicable)"
    }}
  ],
  "init_exports": ["public function AND class names"],
  "breaking_changes": ["import path changes"]
}}

RULES:
1. estimated_lines MUST be ≤50. Use the MEASURED LINE COUNTS above — do not guess.
2. If function X is 131 lines, you CANNOT put it in a 50-line file. Split it.
3. Constants/config → seq001. Orchestrator → highest seq.
4. Group functions that call each other (CALL GRAPH).
5. For each RESISTANCE PATTERN, describe your solution.
6. EVERY public function must appear in init_exports.
7. Prefix ALL filenames with: {prefix}_
8. VALIDATE your math: sum line_counts of grouped functions + 8 overhead ≤ 50.
9. For PROMPT_BLOBs: state extraction strategy (a/b/c) in reason field.
10. Prefer extracting depth ≥2 functions FIRST (easiest, lowest coupling).
11. EVERY class MUST appear in exactly one cut's "classes" list. One class per file unless tiny.
12. Classes with many methods may exceed 50 lines — use the class line count above to verify.
"""


def _validate_plan_lines(plan: dict, ether_map: dict) -> list:
    """Post-validation: check if estimated_lines are plausible against AST data."""
    warnings = []
    func_sizes = {f['name']: f['line_count'] for f in ether_map['functions']}

    for cut in plan.get('cuts', []):
        funcs = cut.get('functions', []) + cut.get('constants', [])
        actual = sum(func_sizes.get(n, 0) for n in funcs) + 8  # overhead
        estimated = cut.get('estimated_lines', 0)

        if actual > 50:
            warnings.append(
                f"❌ {cut['new_file']}: actual ~{actual} lines "
                f"(est {estimated}) — WILL EXCEED 50")
        elif actual > estimated + 10:
            warnings.append(
                f"⚠️ {cut['new_file']}: actual ~{actual} lines "
                f"but estimated {estimated}")
    return warnings


def request_cut_plan(ether_map: dict, source_code: str,
                     folder_name: str = None,
                     exclude_symbols: list[str] | None = None) -> dict:
    """Send prompt to DeepSeek and return the response with validation."""
    from pigeon_compiler.integrations.deepseek_adapter_seq001_v004_d0315__deepseek_api_client_lc_verify_pigeon_plugin import deepseek_query

    prompt = build_plan_prompt(ether_map, source_code, folder_name, exclude_symbols=exclude_symbols)
    result = deepseek_query(prompt, max_tokens=2000)

    # Post-validation of the plan
    content = result.get("content", "")
    validation_warnings = []
    try:
        import json as _json
        # Try to parse and validate
        plan_start = content.find("{")
        plan_end = content.rfind("}") + 1
        if plan_start >= 0 and plan_end > plan_start:
            plan_data = _json.loads(content[plan_start:plan_end])
            validation_warnings = _validate_plan_lines(plan_data, ether_map)
            if validation_warnings:
                print("  POST-VALIDATION WARNINGS:")
                for w in validation_warnings:
                    print(f"    {w}")
    except Exception:
        pass  # Validation is best-effort

    return {
        "prompt_length": len(prompt),
        "response": result,
        "ether_map_file": ether_map.get("file", "?"),
        "validation_warnings": validation_warnings,
    }
