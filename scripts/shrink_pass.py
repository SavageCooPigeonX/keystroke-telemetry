"""scripts/shrink_pass.py — enforce "every push the files should shrink".

Intent (reconstructed from prompt history 2026-04-01 / 2026-04-04):
  - "by the end of tonight i want this codebase at maximum compression"
  - "activate python compression on push not compiler but compression layer"
  - "every push the files should shrink"

This is a measured gate, not a hope. Runs pre-push (or manually) and:
  1. Counts total src/ tokens (rough: bytes / 4)
  2. Compares to logs/shrink_baseline.json
  3. If tokens went UP: exit 1 (block push) unless --allow-grow
  4. If tokens went DOWN: ratchet baseline DOWN (locks in the gain)
  5. Also ratchets .overcap_budget DOWN to current count (hard cap never regresses)
  6. Writes a readable report to logs/shrink_report.json

Zero LLM calls. Pure measurement.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
SCAN_PATTERNS = ("src/**/*.py", "pigeon_compiler/**/*.py")
BASELINE = ROOT / "logs" / "shrink_baseline.json"
REPORT = ROOT / "logs" / "shrink_report.json"
BUDGET = ROOT / ".overcap_budget"

# Pigeon hard cap (line count). Matches pigeon_compiler.pigeon_limits.PIGEON_MAX.
PIGEON_MAX_LINES = 200


def _measure() -> dict:
    total_bytes = 0
    total_files = 0
    total_lines = 0
    overcap_files: list[tuple[str, int]] = []
    seen: set[Path] = set()
    for pattern in SCAN_PATTERNS:
        for p in ROOT.glob(pattern):
            if "__pycache__" in p.parts or p.name.startswith("_tmp_"):
                continue
            if p in seen:
                continue
            seen.add(p)
            try:
                text = p.read_text("utf-8", errors="ignore")
            except Exception:
                continue
            total_files += 1
            total_bytes += len(text.encode("utf-8"))
            lines = len(text.splitlines())
            total_lines += lines
            if lines > PIGEON_MAX_LINES:
                overcap_files.append((p.relative_to(ROOT).as_posix(), lines))
    overcap_files.sort(key=lambda x: -x[1])
    return {
        "files": total_files,
        "bytes": total_bytes,
        "lines": total_lines,
        "approx_tokens": total_bytes // 4,
        "overcap_count": len(overcap_files),
        "overcap_worst": overcap_files[:10],
    }


def _load_baseline() -> dict:
    if not BASELINE.exists():
        return {}
    try:
        return json.loads(BASELINE.read_text("utf-8"))
    except Exception:
        return {}


def _save_baseline(m: dict) -> None:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(m, indent=2), encoding="utf-8")


def _current_budget() -> int:
    if not BUDGET.exists():
        return 10**9
    try:
        return int(BUDGET.read_text("utf-8").strip())
    except Exception:
        return 10**9


def main(argv: list[str]) -> int:
    allow_grow = "--allow-grow" in argv
    verbose = "--verbose" in argv or "-v" in argv

    current = _measure()
    baseline = _load_baseline()
    prev_tokens = int(baseline.get("approx_tokens", 0) or 0)
    prev_overcap = int(baseline.get("overcap_count", 10**9) or 10**9)

    token_delta = current["approx_tokens"] - prev_tokens if prev_tokens else 0
    overcap_delta = current["overcap_count"] - prev_overcap if prev_overcap < 10**9 else 0

    # Ratchet the overcap budget DOWN if we improved
    cur_budget = _current_budget()
    new_budget = min(cur_budget, current["overcap_count"])
    if new_budget < cur_budget:
        BUDGET.write_text(str(new_budget), encoding="utf-8")

    shrunk = (prev_tokens > 0) and (current["approx_tokens"] < prev_tokens)
    grew = (prev_tokens > 0) and (current["approx_tokens"] > prev_tokens)

    status = "ok"
    reasons: list[str] = []
    if grew and not allow_grow:
        status = "blocked"
        reasons.append(
            f"src/ grew by {token_delta:+,} tokens since last baseline "
            f"({prev_tokens:,} -> {current['approx_tokens']:,}). "
            "Shrink or decompose before push. Pass --allow-grow to override."
        )
    if current["overcap_count"] > cur_budget:
        status = "blocked"
        reasons.append(
            f"overcap count {current['overcap_count']} exceeds ratchet "
            f"budget {cur_budget}. Split files or raise the ratchet."
        )

    # If clean and shrunk, lock in the new baseline (ratchet).
    # With --allow-grow, also reseat the baseline at current (operator accepts
    # the growth as the new high-water mark).
    if status == "ok" and (shrunk or not baseline or (grew and allow_grow)):
        _save_baseline({
            "ts": datetime.now(timezone.utc).isoformat(),
            **current,
        })

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reasons": reasons,
        "prev": {
            "approx_tokens": prev_tokens,
            "overcap_count": prev_overcap if prev_overcap < 10**9 else None,
        },
        "current": {
            "approx_tokens": current["approx_tokens"],
            "overcap_count": current["overcap_count"],
            "files": current["files"],
            "lines": current["lines"],
        },
        "deltas": {
            "approx_tokens": token_delta,
            "overcap_count": overcap_delta,
        },
        "ratchet_budget_before": cur_budget if cur_budget < 10**9 else None,
        "ratchet_budget_after": new_budget,
        "overcap_worst_10": current["overcap_worst"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Print short summary
    arrow = "↓" if shrunk else ("↑" if grew else "=")
    print(
        f"[shrink] {arrow} {current['approx_tokens']:,} tok "
        f"({token_delta:+,}) · overcap {current['overcap_count']} "
        f"(budget {new_budget}) · status={status}"
    )
    if verbose or status != "ok":
        for r in reasons:
            print(f"  - {r}")
        if verbose and current["overcap_worst"]:
            print("  worst overcap:")
            for path, n in current["overcap_worst"][:5]:
                print(f"    {n:>4} lines  {path}")

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
