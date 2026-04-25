r"""Priority closure loop: drive unresolved high-priority files toward 10Q/interlinked sleep state.

Flow per cycle:
  1) Pull pending intents from task_queue.json (highest-confidence first)
  2) Run file_sim on intent text to produce graded candidates + task_chain
  3) Trigger one deepseek daemon cycle to apply highest-priority fix work
  4) Record loop telemetry for observatory + auditing

Usage:
  .venv\Scripts\python.exe scripts/priority_closure_loop.py --cycles 10 --top-n 5
  .venv\Scripts\python.exe scripts/priority_closure_loop.py --dry-run --once
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "logs" / "priority_closure_loop.jsonl"
FILE_PROFILES_PATH = ROOT / "file_profiles.json"

TECH_KEYWORDS = {
    "sim", "simulation", "intent", "file", "files", "module", "bug", "fix",
    "deepseek", "runtime", "routing", "manifest", "task", "queue", "entropy",
    "interlink", "10q", "coder", "overwrite", "grade", "profile", "agent",
}
CONVERSATIONAL_MARKERS = {
    "you were about to",
    "conversation-summary",
    "hook blocked",
    "not yet marked the task",
    "chronological review",
}


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _latest(pattern: str) -> Path | None:
    matches = sorted((ROOT / "src").glob(pattern))
    return matches[-1] if matches else None


def _read_task_queue() -> list[dict]:
    path = ROOT / "task_queue.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text("utf-8"))
    except Exception:
        return []

    pending = [t for t in data.get("tasks", []) if t.get("status") != "done"]
    prio = {"high": 0, "medium": 1, "low": 2}
    pending.sort(key=lambda t: (
        prio.get(str(t.get("priority", "medium")).lower(), 9),
        -float(t.get("confidence", 0.0)),
    ))
    return pending


def _intent_text(task: dict) -> str:
    raw = str(task.get("intent") or task.get("title") or "").strip()
    return raw[:300]


def _intent_score(text: str, task: dict) -> float:
    txt = text.lower()
    if not txt:
        return -1.0
    if any(marker in txt for marker in CONVERSATIONAL_MARKERS):
        return -1.0
    words = set(txt.replace("-", " ").replace("_", " ").split())
    keyword_hits = sum(1 for k in TECH_KEYWORDS if k in words or k in txt)
    conf = float(task.get("confidence", 0.0) or 0.0)
    prio = str(task.get("priority", "medium")).lower()
    prio_bonus = {"high": 0.4, "medium": 0.2, "low": 0.1}.get(prio, 0.0)
    length_bonus = min(len(txt) / 250.0, 0.4)
    return keyword_hits * 0.25 + conf * 0.35 + prio_bonus + length_bonus


def _pick_best_task(pending: list[dict]) -> tuple[dict | None, str]:
    best_task = None
    best_intent = ""
    best_score = -1.0
    for task in pending[:20]:
        intent = _intent_text(task)
        score = _intent_score(intent, task)
        if score > best_score:
            best_score = score
            best_task = task
            best_intent = intent
    return best_task, best_intent


def _file_personas(stems: list[str], limit: int = 6) -> dict:
    if not FILE_PROFILES_PATH.exists() or not stems:
        return {}
    try:
        data = json.loads(FILE_PROFILES_PATH.read_text("utf-8"))
    except Exception:
        return {}
    out = {}
    for stem in stems[:limit]:
        p = data.get(stem, {}) if isinstance(data, dict) else {}
        if not isinstance(p, dict):
            continue
        out[stem] = {
            "personality": p.get("personality", "unknown"),
            "fears": p.get("fears", [])[:3],
            "partners": [x.get("name", "") for x in p.get("partners", [])[:3]],
        }
    return out


def _log(entry: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_loop(cycles: int, top_n: int, dry_run: bool, once: bool) -> dict:
    file_sim_path = _latest("file_sim_seq001*.py")
    deepseek_path = ROOT / "src" / "deepseek_daemon_seq001_v001.py"

    if not file_sim_path or not deepseek_path.exists():
        return {"ok": False, "reason": "required modules missing"}

    file_sim = _load_module(file_sim_path)
    deepseek = _load_module(deepseek_path)
    if file_sim is None or deepseek is None:
        return {"ok": False, "reason": "failed to import loop modules"}

    api_key = deepseek._load_api_key() if hasattr(deepseek, "_load_api_key") else None
    if not api_key and not dry_run:
        return {"ok": False, "reason": "DEEPSEEK_API_KEY missing"}

    attempted: set[str] = set()
    summaries = []

    for cycle_idx in range(1, cycles + 1):
        pending = _read_task_queue()
        if not pending:
            _log({"cycle": cycle_idx, "event": "idle", "reason": "no_pending_intents"})
            break

        task, intent_text = _pick_best_task(pending)
        if not task or not intent_text:
            _log({"cycle": cycle_idx, "event": "skip", "reason": "no_sim_eligible_task"})
            continue

        sim_error = ""
        try:
            sim_results = file_sim.run_sim(intent_text, top_n=top_n, root=ROOT)
        except BaseException as e:
            sim_results = []
            sim_error = f"{type(e).__name__}: {e}"
            _log({
                "cycle": cycle_idx,
                "event": "sim_error",
                "task_id": task.get("id", ""),
                "intent_preview": intent_text[:120],
                "error": sim_error[:300],
            })
        needs = [r for r in sim_results if r.get("needs_change")]
        unresolved = [
            r.get("file_stem", "") for r in needs
            if (not r.get("interlinked")) or (float(r.get("10q_score", 0.0)) < 1.0)
        ]
        sim_candidates = [r.get("file_stem", "") for r in sim_results[:top_n]]
        persona_advice = _file_personas([s for s in sim_candidates if s])

        processed = 0
        if hasattr(deepseek, "run_cycle"):
            processed = deepseek.run_cycle(api_key or "", dry_run, attempted)

        summary = {
            "cycle": cycle_idx,
            "task_id": task.get("id", ""),
            "intent_preview": intent_text[:120],
            "sim_candidates": sim_candidates,
            "unresolved_priority_files": unresolved[:10],
            "file_persona_advice": persona_advice,
            "sim_error": sim_error,
            "deepseek_processed": processed,
            "done_if_empty": len(unresolved) == 0,
        }
        _log(summary)
        summaries.append(summary)

        if once:
            break

    return {"ok": True, "cycles": len(summaries), "summaries": summaries[-3:]}


def main() -> int:
    p = argparse.ArgumentParser(description="Priority loop closure runner")
    p.add_argument("--cycles", type=int, default=10)
    p.add_argument("--top-n", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    out = run_loop(args.cycles, args.top_n, args.dry_run, args.once)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
