"""漂p_dw_s005_v004_d0321_踪稿析_λ18_drift_watcher_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 62 lines | ~604 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import os

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
