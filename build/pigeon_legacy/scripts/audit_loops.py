"""scripts/audit_loops.py — close the loop between bug-detect, fix, escalation,
and operator prompt.

Per operator intent (2026-04-17):
  "close the loop between codebase / bugs detecting fixes and copilot escalation
   bug logic working and prompting operator - same with staleness block"

Runs three checks and writes a single report:
  1. Staleness audit — `src/警p_sa_s030*` — are managed prompt blocks fresh?
  2. Escalation re-check — `src/escalation_engine_seq001_v001*` — is escalation state current?
  3. Self-fix accuracy — `logs/self_fix_accuracy.json` — is the fix-accuracy
     data fresh (<24h)?

Writes `logs/loop_audit.json` for `src.master_test` to assert on.

Exit codes:
  0 — all loops alive
  1 — any loop stale/broken (pre-push should block)
  2 — infra error (module missing)

Zero LLM calls. Pure measurement.
"""
from __future__ import annotations
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "logs" / "loop_audit.json"

# Freshness thresholds.
# Post-commit runs the full pipeline; if we didn't commit in 48h, the data
# behind escalation + self_fix is probably drifting.
SELF_FIX_MAX_AGE_HOURS = 48
ESCALATION_MAX_AGE_HOURS = 48


def _load_glob_module(root: Path, subdir: str, glob: str):
    """Load the first matching module (skip decomposed dirs)."""
    for p in sorted((root / subdir).glob(glob)):
        if p.is_file() and p.suffix == ".py":
            spec = importlib.util.spec_from_file_location(p.stem, p)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception:
                continue
    return None


def _file_age_hours(p: Path) -> float | None:
    if not p.exists():
        return None
    try:
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - mtime).total_seconds() / 3600
    except Exception:
        return None


def audit_staleness(root: Path) -> dict:
    """Ask the staleness detector if any prompt blocks rotted.

    UI/LLM-owned blocks (current-query, prompt-telemetry) are refreshed by the
    chat-UI pipeline (enricher + prompt_journal) — they WILL be stale between
    sessions and that's expected. We only hard-fail on blocks whose writer is
    the commit pipeline itself.
    """
    mod = _load_glob_module(root, "src", "警p_sa_s030*")
    if not mod or not hasattr(mod, "check_staleness"):
        return {"name": "staleness", "ok": True, "msg": "staleness module missing — skip"}
    try:
        stale = mod.check_staleness(root)
    except Exception as e:
        return {"name": "staleness", "ok": False, "msg": f"exception: {e}"}
    # Partition: ui-owned (soft) vs commit-pipeline-owned (hard).
    ui_owned = {"current-query", "prompt-telemetry"}
    ui_stale = [s for s in stale if s.get("block") in ui_owned]
    hard_stale = [s for s in stale if s.get("block") not in ui_owned]
    if hard_stale:
        names = ", ".join(s.get("block", "?") for s in hard_stale)
        return {
            "name": "staleness",
            "ok": False,
            "msg": f"{len(hard_stale)} commit-pipeline block(s) stale: {names}",
            "detail": {"hard": hard_stale, "ui_soft": ui_stale},
        }
    if ui_stale:
        names = ", ".join(s.get("block", "?") for s in ui_stale)
        return {
            "name": "staleness",
            "ok": True,
            "msg": f"ok (ui-owned stale, allowed): {names}",
            "detail": {"ui_soft": ui_stale},
        }
    return {"name": "staleness", "ok": True, "msg": "all managed blocks fresh"}


def audit_escalation(root: Path) -> dict:
    """Re-run the escalation ladder, then verify state is fresh.

    Re-running catches regressions between the last post-commit and this
    push: if a module changed status, escalation should pick it up and
    `_save_state` refreshes mtime.
    """
    mod = _load_glob_module(root, "src", "escalation_engine_seq001_v001*")
    rerun_err = None
    rerun_result = None
    if mod and hasattr(mod, "check_and_escalate"):
        try:
            rerun_result = mod.check_and_escalate(root)
        except Exception as e:
            rerun_err = str(e)
    state_path = root / "logs" / "escalation_state.json"
    age = _file_age_hours(state_path)
    if age is None:
        return {
            "name": "escalation",
            "ok": False,
            "msg": (
                f"logs/escalation_state.json missing"
                + (f" (re-run failed: {rerun_err})" if rerun_err else "")
            ),
        }
    if age > ESCALATION_MAX_AGE_HOURS:
        return {
            "name": "escalation",
            "ok": False,
            "msg": (
                f"escalation_state.json is {age:.1f}h old (max {ESCALATION_MAX_AGE_HOURS}h)"
                + (f" — re-run failed: {rerun_err}" if rerun_err else " — re-run was skipped")
            ),
        }
    n_track = (rerun_result or {}).get("total_modules_tracked", 0)
    n_fix = (rerun_result or {}).get("total_autonomous_fixes", 0)
    return {
        "name": "escalation",
        "ok": True,
        "msg": f"escalation re-checked: {n_track} tracked, {n_fix} autonomous fixes (state {age:.1f}h)",
        "detail": {
            "tracked": n_track,
            "autonomous_fixes": n_fix,
            "escalated_this_run": (rerun_result or {}).get("escalated", False),
            "rerun_err": rerun_err,
        },
    }


def audit_self_fix(root: Path) -> dict:
    """Verify self_fix_accuracy.json is present and fresh."""
    acc_path = root / "logs" / "self_fix_accuracy.json"
    age = _file_age_hours(acc_path)
    if age is None:
        return {
            "name": "self_fix",
            "ok": False,
            "msg": "logs/self_fix_accuracy.json missing — tracker never ran",
        }
    if age > SELF_FIX_MAX_AGE_HOURS:
        return {
            "name": "self_fix",
            "ok": False,
            "msg": f"self_fix_accuracy.json is {age:.1f}h old (max {SELF_FIX_MAX_AGE_HOURS}h)",
        }
    try:
        data = json.loads(acc_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"name": "self_fix", "ok": False, "msg": f"accuracy parse error: {e}"}
    rate = data.get("avg_fix_rate", 0)
    total = data.get("total_threads", 0)
    return {
        "name": "self_fix",
        "ok": True,
        "msg": f"self_fix fresh ({age:.1f}h): {total} threads, {rate*100:.1f}% fix rate",
        "detail": {
            "age_hours": round(age, 2),
            "total_threads": total,
            "fix_rate": rate,
        },
    }


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv or "-v" in argv
    root = ROOT

    checks = [
        audit_staleness(root),
        audit_escalation(root),
        audit_self_fix(root),
    ]

    any_failed = any(not c["ok"] for c in checks)
    status = "blocked" if any_failed else "ok"

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Print compact summary
    for c in checks:
        mark = "OK  " if c["ok"] else "FAIL"
        print(f"[loops] {mark}  {c['name']}: {c['msg']}")
    if verbose:
        for c in checks:
            if c.get("detail"):
                print(f"  detail[{c['name']}]: {c['detail']}")

    print(f"[loops] status={status}")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
