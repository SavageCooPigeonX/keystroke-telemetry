"""weakness_surfacer_seq001_v001 — what the codebase is trying to tell you, surfaced.

Deterministic scanner. Zero LLM calls. Produces a ranked list of weaknesses
Copilot should announce at the START of a response.

Run: py -m src.weakness_surfacer_seq001_v001_seq001_v001  (prints + writes logs/weaknesses_now.json)
"""
from __future__ import annotations
import json, time
from datetime import datetime, timezone
from pathlib import Path

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-16T00:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  trim under 200-line cap
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

ROOT = Path(__file__).resolve().parent.parent


def _age_minutes(p: Path) -> float | None:
    return (time.time() - p.stat().st_mtime) / 60.0 if p.exists() else None


def _read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_stale_telemetry() -> dict | None:
    p = ROOT / "logs" / "prompt_telemetry_latest.json"
    age = _age_minutes(p)
    if age is None:
        return {"severity": "high", "msg": "prompt_telemetry_latest.json missing — journal pipeline never ran"}
    if age > 60:
        return {"severity": "high", "msg": f"telemetry stale ({age:.0f}min) — copilot not calling log_enriched_entry"}
    if age > 15:
        return {"severity": "medium", "msg": f"telemetry stale ({age:.0f}min) — likely skipped journal call"}
    return None


def check_master_test() -> dict | None:
    run = _read_json(ROOT / "logs" / "master_run.json")
    if run is None:
        return {"severity": "high", "msg": "master_test never run — health score has no integrity gate"}
    if not run.get("integrity_ok"):
        return {"severity": "critical", "msg": "master_test integrity FAILED — master_test.py modified without resealing"}
    if not run.get("passed"):
        failed = [r["name"] for r in run.get("results", []) if not r.get("passed")]
        return {"severity": "high", "msg": f"master_test failing: {failed}"}
    age = _age_minutes(ROOT / "logs" / "master_run.json")
    if age and age > 1440:
        return {"severity": "medium", "msg": f"master_test last passed {age/60:.0f}h ago — re-run"}
    return None


def check_health_score() -> dict | None:
    snap = _read_json(ROOT / "logs" / "push_snapshot_seq001_v001s" / "_latest.json")
    if snap is None:
        return {"severity": "medium", "msg": "no push snapshot — health score never computed"}
    score = snap.get("health_score")
    caps = snap.get("applied_caps", [])
    if score is None:
        return {"severity": "low", "msg": "snapshot exists but no health_score field"}
    if caps:
        reasons = [c[0] if isinstance(c, list) else c for c in caps]
        return {"severity": "high", "msg": f"health={score} CAPPED by {reasons} — fix vetos before claiming healthy"}
    if score < 70:
        return {"severity": "medium", "msg": f"health={score} below 70 — outcome/drift weak"}
    return None


def check_overcap_budget() -> dict | None:
    bf = ROOT / ".overcap_budget"
    if not bf.exists():
        return None
    budget = int(bf.read_text(encoding="utf-8").strip() or 0)
    if budget > 50:
        return {"severity": "medium", "msg": f"{budget} files over 200-line cap — pigeon compiler not enforcing on push"}
    if budget > 0:
        return {"severity": "low", "msg": f"{budget} files over cap — ratchet active, no regressions allowed"}
    return None


def check_cold_intents() -> dict | None:
    tq = _read_json(ROOT / "task_queue.json")
    if tq is None:
        return None
    tasks = tq if isinstance(tq, list) else tq.get("tasks", [])
    pending = [t for t in tasks if t.get("status") == "pending"]
    if not pending:
        return None
    gen = ROOT / "tests" / "generated"
    untested = [t["id"] for t in pending if not (gen / f"test_intent_{t['id'].replace('-', '_')}.py").exists()]
    if untested:
        return {"severity": "high", "msg": f"{len(untested)} pending intents have no test: {untested[:5]}"}
    if len(pending) > 5:
        return {"severity": "medium", "msg": f"{len(pending)} cold intents — tests exist but never flip green"}
    return None


def check_self_fix_outcomes() -> dict | None:
    log = ROOT / "logs" / "self_fix_verification_seq001_v001.jsonl"
    if not log.exists():
        return {"severity": "medium", "msg": "self_fix_verification_seq001_v001.jsonl missing — fixes write but never verify"}
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        return {"severity": "low", "msg": "verification log empty — no fixes attempted"}
    recent = [json.loads(l) for l in lines[-10:]]
    closed = sum(r.get("closed_count", 0) for r in recent)
    touched = sum(r.get("touched_count", 0) for r in recent)
    regressions = sum(r.get("regression_count", 0) for r in recent)
    if regressions > 0:
        return {"severity": "high", "msg": f"self_fix introduced {regressions} regressions — rollback not wired"}
    if touched > 0 and closed / touched < 0.3:
        return {"severity": "medium", "msg": f"self_fix close rate {closed/touched:.0%} — fixes don't actually fix"}
    return None


def check_deleted_words_unanswered() -> dict | None:
    snap = _read_json(ROOT / "logs" / "prompt_telemetry_latest.json")
    if not snap:
        return None
    deleted = snap.get("deleted_words") or []
    real = [w for w in deleted if isinstance(w, str) and len(w) > 4]
    if not real and isinstance(deleted, list):
        real = [d.get("word") for d in deleted if isinstance(d, dict) and len(d.get("word", "")) > 4]
    if real:
        return {"severity": "medium", "msg": f"operator deleted: {real} — address completed thought"}
    return None


CHECKS = [check_stale_telemetry, check_master_test, check_health_score, check_overcap_budget,
          check_cold_intents, check_self_fix_outcomes, check_deleted_words_unanswered]
_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def surface() -> list[dict]:
    fired = []
    for ch in CHECKS:
        try:
            r = ch()
        except Exception as e:
            r = {"severity": "low", "msg": f"{ch.__name__} crashed: {e}"}
        if r:
            r["check"] = ch.__name__
            fired.append(r)
    fired.sort(key=lambda x: _RANK.get(x["severity"], 99))
    return fired


def render_block(weaknesses: list[dict]) -> str:
    if not weaknesses:
        return "[weaknesses] all checks green."
    lines = [f"[weaknesses] {len(weaknesses)} fired:"]
    for w in weaknesses[:6]:
        lines.append(f"  [{w['severity']}] {w['msg']}")
    return "\n".join(lines)


def main() -> int:
    ws = surface()
    out = ROOT / "logs" / "weaknesses_now.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "count": len(ws), "weaknesses": ws}, indent=2), encoding="utf-8")
    print(render_block(ws))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
