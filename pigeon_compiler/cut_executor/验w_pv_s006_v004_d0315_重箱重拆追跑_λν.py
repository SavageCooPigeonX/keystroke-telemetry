"""plan_validator_seq006_v001.py — Validate cut plan before execution.

Checks: line limits, missing functions, naming convention, completeness.
Returns {valid: bool, errors: [], warnings: []}.
"""

from pathlib import Path
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED


def validate_plan(plan: dict, ether_map: dict) -> dict:
    """Pre-execution validation of a DeepSeek cut plan."""
    errors, warnings = [], []
    all_funcs = {f["name"] for f in ether_map.get("functions", [])}
    all_consts = {c["name"] for c in ether_map.get("constants", [])}
    all_names = all_funcs | all_consts
    placed = set()

    for i, cut in enumerate(plan.get("cuts", [])):
        fname = cut.get("new_file", f"cut_{i}")
        est = cut.get("estimated_lines", 0)
        names = set(cut.get("functions", []) + cut.get("constants", [])
                     + cut.get("contents", []))
        placed |= names
        # Check line estimate
        if est > PIGEON_MAX:
            errors.append(f"{fname}: estimated {est} lines > {PIGEON_MAX}")
        elif est > PIGEON_RECOMMENDED:
            warnings.append(f"{fname}: estimated {est} lines > {PIGEON_RECOMMENDED} recommended")
        # Check actual function sizes
        for n in names:
            fn = _find_func(n, ether_map)
            if fn and fn["line_count"] > PIGEON_MAX and len(names) > 1:
                warnings.append(f"{fname}: {n}() is {fn['line_count']} lines, "
                                f"should be alone or decomposed")
        # Check naming
        if not fname.endswith("_v001.py"):
            warnings.append(f"{fname}: missing _vNNN.py suffix")

    # Check completeness — every function should be placed
    missing = all_names - placed
    if missing:
        warnings.append(f"Unplaced names: {sorted(missing)}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _find_func(name: str, em: dict) -> dict | None:
    for f in em.get("functions", []):
        if f["name"] == name:
            return f
    return None
