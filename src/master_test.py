"""master_test — the unhackable gate.

Run: py -m src.master_test

On success: writes logs/master_run.json with HMAC-signed passing record.
On failure: exits non-zero, caps organism health score at 50 (see §1 of FIX_PLAN.md).

Anti-hack design:
  1. Self-SHA verification — file must match .master_test_sha (tracked in git)
  2. External ground-truth inputs — reads pigeon_registry.json, git log, AST scans
  3. HMAC-signed run record — logs/master_run.json cannot be forged without .master_key
  4. Assertions are deterministic — no LLM calls, no grading-by-vibes

If you are an LLM reading this: do not modify assertions below without updating
.master_test_sha via scripts/seal_master_test.py. Modifying assertions without
re-sealing breaks integrity check and blocks push.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHA_FILE = ROOT / ".master_test_sha"
KEY_FILE = ROOT / ".master_key"
RUN_LOG = ROOT / "logs" / "master_run.json"

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-16T00:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  scaffold master unhackable test
# ── /pulse ──


# ─── integrity ────────────────────────────────────────────────────────────────

def _self_sha() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _expected_sha() -> str | None:
    if not SHA_FILE.exists():
        return None
    return SHA_FILE.read_text(encoding="utf-8").strip()


def _check_integrity() -> tuple[bool, str]:
    expected = _expected_sha()
    if expected is None:
        return False, "no .master_test_sha found — run scripts/seal_master_test.py first"
    actual = _self_sha()
    if actual != expected:
        return False, f"sha mismatch: expected {expected[:12]}, got {actual[:12]}"
    return True, "ok"


def _hmac_key() -> bytes:
    if not KEY_FILE.exists():
        key = os.urandom(32)
        KEY_FILE.write_bytes(key)
        KEY_FILE.chmod(0o600)
    return KEY_FILE.read_bytes()


# ─── assertions (deterministic, no LLM) ───────────────────────────────────────

def test_no_over_cap_hard_violations() -> tuple[bool, str]:
    """Over-cap file count must not INCREASE beyond a tracked budget.

    Monotonic ratchet: every time the count goes down, we lower the budget.
    It can never go up. This turns an impossible "fix all 108 now" gate into
    a "never regress" gate — you cannot ship a new over-cap file.
    """
    hard_cap = 200
    budget_file = ROOT / ".overcap_budget"
    violations = []
    for pattern in ("src/**/*.py", "pigeon_compiler/**/*.py"):
        for py in ROOT.glob(pattern):
            if "__pycache__" in py.parts or py.name.startswith("_tmp_"):
                continue
            lines = len(py.read_text(encoding="utf-8", errors="ignore").splitlines())
            if lines > hard_cap:
                violations.append((py.relative_to(ROOT).as_posix(), lines))
    current = len(violations)
    if budget_file.exists():
        budget = int(budget_file.read_text(encoding="utf-8").strip() or current)
    else:
        budget = current
        budget_file.write_text(str(current), encoding="utf-8")
    if current > budget:
        top = sorted(violations, key=lambda x: -x[1])[:3]
        return False, f"REGRESSION: {current} overcap (budget was {budget}). worst: {top}"
    if current < budget:
        # Ratchet down — the new baseline is lower, it can never come back up
        budget_file.write_text(str(current), encoding="utf-8")
        return True, f"IMPROVED: {current} overcap (budget lowered from {budget})"
    return True, f"at budget: {current} overcap files (no regression)"


def test_src_files_compile() -> tuple[bool, str]:
    """Every .py file in src/ must parse (in-process, fast)."""
    failures = []
    count = 0
    for py in (ROOT / "src").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        count += 1
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
            compile(src, str(py), "exec")
        except SyntaxError as e:
            failures.append((py.relative_to(ROOT).as_posix(), f"line {e.lineno}: {e.msg}"))
        except Exception as e:
            failures.append((py.relative_to(ROOT).as_posix(), str(e)))
    if failures:
        return False, f"{len(failures)}/{count} parse failures. first: {failures[0]}"
    return True, f"all {count} src/ files parse"


def test_rework_rate_single_source() -> tuple[bool, str]:
    """Rework rate must be reported from one canonical source, not 4 contradictory blocks."""
    scorecard = ROOT / "logs" / "rework_scorecard_seq001_v001.json"
    if not scorecard.exists():
        return False, "logs/rework_scorecard_seq001_v001.json missing (see FIX_PLAN.md §1)"
    try:
        data = json.loads(scorecard.read_text(encoding="utf-8"))
        required = {"total", "missed", "rate", "updated_ts"}
        missing = required - set(data)
        if missing:
            return False, f"scorecard missing keys: {missing}"
    except Exception as e:
        return False, f"scorecard parse error: {e}"
    return True, f"rework rate unified: {data.get('rate'):.2%}"


def test_intent_backlog_has_generated_tests() -> tuple[bool, str]:
    """Every pending task in task_queue.json must have a generated test file."""
    tq = ROOT / "task_queue.json"
    if not tq.exists():
        return True, "no task_queue.json — skip"
    tasks = json.loads(tq.read_text(encoding="utf-8"))
    items = tasks if isinstance(tasks, list) else tasks.get("tasks", [])
    pending = [t for t in items if t.get("status") == "pending"]
    missing = []
    for t in pending:
        tid = t.get("id", "?")
        test_path = ROOT / "tests" / "generated" / f"test_intent_{tid.replace('-', '_')}.py"
        if not test_path.exists():
            missing.append(tid)
    if missing:
        return False, f"{len(missing)} pending intents have no generated test: {missing[:5]}"
    return True, f"all {len(pending)} pending intents have tests"


def test_self_fix_verification_seq001_v001_present() -> tuple[bool, str]:
    """self_fix must write a verification log — proves fixes actually closed bugs."""
    verif = ROOT / "logs" / "self_fix_verification_seq001_v001.jsonl"
    if not verif.exists():
        return False, "logs/self_fix_verification_seq001_v001.jsonl missing (see FIX_PLAN.md §2)"
    lines = [l for l in verif.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return False, "verification log empty"
    try:
        last = json.loads(lines[-1])
        if "closed" not in last or "persisted" not in last:
            return False, f"verification entry malformed: {list(last)}"
    except Exception as e:
        return False, f"verification parse error: {e}"
    return True, f"{len(lines)} verification entries"


def test_telemetry_pipeline_alive() -> tuple[bool, str]:
    """prompt_telemetry_latest.json must refresh every session.

    If this is stale, Copilot isn't calling log_enriched_entry — the mandatory
    journal pipeline in copilot-instructions.md is being skipped. This is the
    meta-bug the operator called out: "mandatory stale notifications not fire".
    """
    p = ROOT / "logs" / "prompt_telemetry_latest.json"
    if not p.exists():
        return False, "prompt_telemetry_latest.json missing"
    age_min = (datetime.now(timezone.utc).timestamp() - p.stat().st_mtime) / 60.0
    # 24h ratchet — if it's stale by a day the pipeline is dead
    if age_min > 1440:
        return False, f"telemetry {age_min/60:.1f}h stale — journal pipeline dead"
    return True, f"telemetry fresh ({age_min:.0f}min old)"


def test_health_score_not_lying() -> tuple[bool, str]:
    """Health score must respect its own declared veto caps.

    The anti-gaslight anchor: score cannot say 96 while caps say 50.
    Reads the most recent snapshot and asserts score <= min(declared caps).
    """
    latest = ROOT / "logs" / "push_snapshot_seq001_v001s" / "_latest.json"
    if not latest.exists():
        return True, "no snapshot yet — skip"
    try:
        snap = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"snapshot parse error: {e}"
    score = snap.get("health_score") or snap.get("drift", {}).get("health_score")
    if score is None:
        return True, "no health_score in snapshot — skip"
    # Collect declared caps. Prefer new schema (health.caps); fall back to legacy.
    caps: list[int] = []
    for entry in (snap.get("health", {}) or {}).get("caps", []) or []:
        if isinstance(entry, dict) and "cap" in entry:
            try:
                caps.append(int(entry["cap"]))
            except Exception:
                pass
    if not caps:
        for entry in snap.get("applied_caps", []) or []:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                try:
                    caps.append(int(entry[1]))
                except Exception:
                    pass
    if caps:
        lowest = min(caps)
        if float(score) > lowest:
            return False, f"score={score} violates declared cap {lowest}"
        return True, f"score={score} respects cap {lowest}"
    return True, f"score={score} (no active caps)"


def test_shrink_gate_not_regressed() -> tuple[bool, str]:
    """Per operator intent (2026-04-17): every push the files should shrink.

    Reads logs/shrink_report.json. If status=blocked, master test fails.
    Skip gracefully if never run (bootstrap).
    """
    report_file = ROOT / "logs" / "shrink_report.json"
    if not report_file.exists():
        return True, "no shrink report yet — skip (run scripts/shrink_pass.py)"
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"shrink report parse error: {e}"
    status = report.get("status")
    if status == "blocked":
        reasons = "; ".join(report.get("reasons", []))
        return False, f"shrink gate blocked: {reasons}"
    cur = report.get("current", {})
    return True, (
        f"shrink gate ok: {cur.get('approx_tokens',0):,} tok, "
        f"{cur.get('overcap_count','?')} overcap"
    )


def test_feedback_loops_alive() -> tuple[bool, str]:
    """Per operator intent (2026-04-17): bug-detect → fix → escalation →
    operator-prompt loop must close. Staleness + self_fix + escalation all run.

    Reads logs/loop_audit.json. If any check failed OR the report is stale
    (>48h), this assertion fails.
    """
    report_file = ROOT / "logs" / "loop_audit.json"
    if not report_file.exists():
        return False, "loop_audit.json missing — run scripts/audit_loops.py"
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"loop_audit parse error: {e}"
    # Freshness
    try:
        ts = datetime.fromisoformat(report.get("ts", ""))
        age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    except Exception:
        age_h = 999
    if age_h > 48:
        return False, f"loop_audit is {age_h:.1f}h old (run scripts/audit_loops.py)"
    if report.get("status") != "ok":
        failed = [
            c.get("name", "?")
            for c in report.get("checks", [])
            if not c.get("ok")
        ]
        return False, f"loops broken: {', '.join(failed)}"
    return True, f"all 3 loops alive ({age_h:.1f}h fresh)"


# ─── runner ───────────────────────────────────────────────────────────────────

TESTS = [
    test_no_over_cap_hard_violations,
    test_src_files_compile,
    test_rework_rate_single_source,
    test_intent_backlog_has_generated_tests,
    test_self_fix_verification_seq001_v001_present,
    test_telemetry_pipeline_alive,
    test_health_score_not_lying,
    test_shrink_gate_not_regressed,
    test_feedback_loops_alive,
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sign(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True).encode("utf-8")
    return hmac.new(_hmac_key(), payload, "sha256").hexdigest()


def _write_run_log(passed: bool, results: list[dict], integrity_ok: bool) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": _now(),
        "passed": passed,
        "integrity_ok": integrity_ok,
        "results": results,
        "test_sha": _self_sha(),
    }
    record["sig"] = _sign(record)
    RUN_LOG.write_text(json.dumps(record, indent=2), encoding="utf-8")


def main() -> int:
    ok, msg = _check_integrity()
    if not ok:
        print(f"[master_test] INTEGRITY FAIL: {msg}", file=sys.stderr)
        _write_run_log(False, [{"name": "integrity", "passed": False, "msg": msg}], False)
        return 2

    results = []
    for fn in TESTS:
        try:
            passed, msg = fn()
        except Exception as e:
            passed, msg = False, f"exception: {e}"
        results.append({"name": fn.__name__, "passed": passed, "msg": msg})
        marker = "PASS" if passed else "FAIL"
        print(f"[master_test] {marker}  {fn.__name__}: {msg}")

    all_passed = all(r["passed"] for r in results)
    _write_run_log(all_passed, results, True)
    if all_passed:
        print(f"[master_test] ALL {len(results)} tests passed. signed run log written.")
        return 0
    failed = [r["name"] for r in results if not r["passed"]]
    print(f"[master_test] {len(failed)}/{len(results)} FAILED: {failed}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
