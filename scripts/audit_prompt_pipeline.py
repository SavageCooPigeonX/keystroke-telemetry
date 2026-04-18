"""One-shot audit: prompt logging pipeline + enricher failure mode + operator profile freshness."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


def _age_min(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / 60.0


def _parse_ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def audit(root: Path) -> dict:
    logs = root / "logs"
    report: dict = {"checks": [], "status": "ok"}

    pj = logs / "prompt_journal.jsonl"
    if pj.exists():
        lines = pj.read_text(encoding="utf-8", errors="replace").splitlines()
        first = json.loads(lines[0]) if lines else {}
        last = json.loads(lines[-1]) if lines else {}
        last_ts = _parse_ts(last.get("ts", ""))
        age_min = None
        if last_ts:
            age_min = (datetime.now(timezone.utc) - last_ts).total_seconds() / 60.0
        report["prompt_journal"] = {
            "exists": True,
            "entries": len(lines),
            "first_ts": first.get("ts"),
            "last_ts": last.get("ts"),
            "age_min": age_min,
            "last_msg_preview": last.get("msg", "")[:120],
        }
    else:
        report["prompt_journal"] = {"exists": False}
        report["status"] = "fail"

    ee = logs / "enricher_errors.jsonl"
    if ee.exists() and ee.stat().st_size:
        lines = ee.read_text(encoding="utf-8", errors="replace").splitlines()
        last_err = lines[-1] if lines else ""
        try:
            last_obj = json.loads(last_err)
        except Exception:
            last_obj = {"raw": last_err[:200]}
        report["enricher_errors"] = {
            "count": len(lines),
            "last": last_obj,
            "age_min": _age_min(ee),
        }
    else:
        report["enricher_errors"] = {"count": 0}

    pt = logs / "prompt_telemetry_latest.json"
    if pt.exists():
        report["prompt_telemetry_latest"] = {
            "age_min": _age_min(pt),
            "size": pt.stat().st_size,
        }

    tc = logs / "thought_completions.jsonl"
    if tc.exists():
        lines = tc.read_text(encoding="utf-8", errors="replace").splitlines()
        report["thought_completions"] = {
            "count": len(lines),
            "age_min": _age_min(tc),
        }

    op_json = logs / "operator_profile_tc.json"
    op_md = root / "operator_profile.md"
    report["operator_profile"] = {
        "json_exists": op_json.exists(),
        "json_age_min": _age_min(op_json) if op_json.exists() else None,
        "md_exists": op_md.exists(),
        "md_age_min": _age_min(op_md) if op_md.exists() else None,
    }

    uh = logs / "unsaid_history.jsonl"
    if uh.exists():
        lines = uh.read_text(encoding="utf-8", errors="replace").splitlines()
        report["unsaid_history"] = {
            "count": len(lines),
            "age_min": _age_min(uh),
        }

    return report


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parents[1]
    rep = audit(root)
    print(json.dumps(rep, indent=2, default=str))
