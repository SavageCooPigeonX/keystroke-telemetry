"""Grade thought-completer outputs vs real operator history.

Uses two ground-truth sources:
  1. logs/thought_completions.jsonl -- completion + final_text + accepted flag
  2. logs/prompt_journal.jsonl      -- full submitted messages (for retrospective grading)

Scoring:
  - acceptance_rate     : fraction of completions marked accepted
  - prefix_match_rate   : fraction where final_text starts with buffer + completion
  - token_overlap       : Jaccard over whitespace-split tokens (completion vs actual continuation)
  - avg_confidence      : derived from prefix_match + token_overlap
Writes logs/thought_completer_grading.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean


def _toks(s: str) -> set[str]:
    return {t for t in s.lower().split() if t}


def _actual_continuation(buffer: str, final_text: str) -> str:
    if final_text.startswith(buffer):
        return final_text[len(buffer):].strip()
    return final_text.strip()


def grade(root: Path) -> dict:
    tc = root / "logs" / "thought_completions.jsonl"
    if not tc.exists():
        return {"status": "no_data", "reason": "thought_completions.jsonl missing"}

    lines = tc.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return {"status": "no_data", "reason": "empty"}

    records = []
    for ln in lines:
        try:
            records.append(json.loads(ln))
        except Exception:
            continue

    if not records:
        return {"status": "no_data", "reason": "unparseable"}

    accepted = [r for r in records if r.get("accepted")]
    rejected = [r for r in records if not r.get("accepted")]

    prefix_matches = 0
    overlaps: list[float] = []
    per_record = []
    for r in records:
        buf = r.get("buffer", "")
        comp = r.get("completion", "")
        final = r.get("final_text", "")
        if not (buf and comp and final):
            continue
        predicted_full = (buf + " " + comp).strip()
        prefix_ok = final.startswith(predicted_full[: min(len(predicted_full), len(final))])
        if prefix_ok:
            prefix_matches += 1
        actual_cont = _actual_continuation(buf, final)
        ct, at = _toks(comp), _toks(actual_cont)
        if ct or at:
            j = len(ct & at) / max(1, len(ct | at))
            overlaps.append(j)
        per_record.append({
            "ts": r.get("ts"),
            "buffer": buf[:60],
            "completion": comp[:60],
            "actual": actual_cont[:60],
            "accepted": bool(r.get("accepted")),
            "prefix_match": prefix_ok,
            "token_overlap": round(j, 3) if (ct or at) else None,
        })

    gradeable = [r for r in per_record if r["token_overlap"] is not None]
    summary = {
        "status": "ok",
        "total_records": len(records),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "acceptance_rate": round(len(accepted) / max(1, len(records)), 3),
        "gradeable": len(gradeable),
        "prefix_match_rate": round(prefix_matches / max(1, len(records)), 3),
        "avg_token_overlap": round(mean(overlaps), 3) if overlaps else None,
        "top5_best": sorted(gradeable, key=lambda r: r["token_overlap"] or 0, reverse=True)[:5],
        "top5_worst": sorted(gradeable, key=lambda r: r["token_overlap"] or 0)[:5],
    }

    # Cross-reference: does the operator actually USE these completions in later prompts?
    pj = root / "logs" / "prompt_journal.jsonl"
    if pj.exists():
        jl = pj.read_text(encoding="utf-8", errors="replace").splitlines()
        msgs = []
        for ln in jl:
            try:
                msgs.append(json.loads(ln).get("msg", ""))
            except Exception:
                continue
        echoed = 0
        for r in accepted:
            comp = r.get("completion", "").strip().lower()
            if len(comp) < 8:
                continue
            if any(comp in m.lower() for m in msgs):
                echoed += 1
        summary["accepted_echoed_in_journal"] = echoed
        summary["echo_rate"] = round(echoed / max(1, len(accepted)), 3)

    out = root / "logs" / "thought_completer_grading.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    rep = grade(root)
    print(json.dumps(rep, indent=2, default=str))
