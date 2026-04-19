"""Drift detection for live LLM coding loops.

Monitors a directory of pigeon-compliant files. When a file crosses
its context budget (after an agent edit), emits a drift signal that
an LLM agent can act on or ignore.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──


import glob as _glob
import importlib.util
import json
import os
from pathlib import Path


def _load_context_budget():
    matches = sorted(_glob.glob('src/境w_cb_s004*.py'))
    if not matches:
        raise ImportError('No src/context_budget_seq004*.py found')
    spec = importlib.util.spec_from_file_location('_cb', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.score_context_budget, mod.estimate_tokens


try:
    score_context_budget, estimate_tokens = _load_context_budget()
except ImportError:
    def score_context_budget(*a, **kw): return {}  # type: ignore
    def estimate_tokens(*a, **kw): return 0  # type: ignore

# Inline dependency line-count lookup (avoids AST — just wc -l)
def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _parse_pigeon_preamble(path: Path) -> dict:
    """Extract @pigeon metadata from the first line of a file."""
    first_line = path.read_text(encoding="utf-8").split("\n", 1)[0]
    meta = {}
    if "# @pigeon:" not in first_line:
        return meta
    raw = first_line.split("# @pigeon:", 1)[1]
    for pair in raw.split("|"):
        pair = pair.strip()
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        meta[k] = v
    return meta


class DriftWatcher:
    def __init__(self, watch_dir: str, coupling_score: float = 0.0):
        self.watch_dir = Path(watch_dir)
        self.coupling_score = coupling_score
        self._baselines: dict[str, int] = {}  # filename -> last known line count

    def snapshot(self):
        """Take baseline measurements of all .py files."""
        for py in self.watch_dir.glob("*.py"):
            self._baselines[py.name] = _line_count(py)

    def check_drift(self) -> list[dict]:
        """Compare current state to baseline. Return drift signals."""
        signals = []
        for py in self.watch_dir.glob("*.py"):
            if py.name == "__init__.py":
                continue
            current = _line_count(py)
            baseline = self._baselines.get(py.name, current)

            meta = _parse_pigeon_preamble(py)
            deps = meta.get("depends", [])
            dep_lines = []
            for d in deps:
                # find dep file by prefix match
                matches = list(self.watch_dir.glob(f"{d}*.py"))
                if matches:
                    dep_lines.append(_line_count(matches[0]))

            score = score_context_budget(
                current, dep_lines, self.coupling_score
            )

            if score["verdict"] in ("OVER_HARD_CAP", "OVER_BUDGET"):
                signals.append({
                    "file": py.name,
                    "was": baseline,
                    "now": current,
                    "tokens": score["total_tokens"],
                    "budget": score["budget"],
                    "verdict": score["verdict"],
                    "suggestion": f"split {py.stem} — context cost {score['total_tokens']} exceeds budget {score['budget']}",
                })

            self._baselines[py.name] = current

        return signals

    def check_and_print(self) -> list[dict]:
        """Check drift and print signals live."""
        signals = self.check_drift()
        for s in signals:
            print(f"[DRIFT] {s['file']}: {s['was']}→{s['now']} lines, "
                  f"{s['tokens']}/{s['budget']} tokens — {s['verdict']}")
            print(f"  → {s['suggestion']}")
        if not signals:
            print("[DRIFT] All files within budget ✓")
        return signals
