"""thought_completer_service — JSON-lines stdio bridge (Phase 3).

Spawned as a subprocess by the VS Code extension (or any frontend).
Protocol: one JSON request per line on stdin, one JSON response per line
on stdout. All non-protocol output goes to stderr.

Request schema (stdin line):
  {"op": "complete", "id": "r-1", "fragment": "...",
   "open_files": [...], "recent_keys": [...]}
  {"op": "accept",   "id": "r-2", "fragment": "...",
   "candidate_index": 0, "result_id": "r-1", "session_id": "..."}
  {"op": "reject",   "id": "r-3", "fragment": "...",
   "candidate_index": 0, "result_id": "r-1",
   "chosen_index": 1, "reason": "..."}
  {"op": "mark",     "id": "r-4", "intent_id": "...",
   "condition": "routed|acted|verified|stable"}
  {"op": "closure_rate", "id": "r-5"}
  {"op": "ping",     "id": "r-6"}
  {"op": "shutdown"}

Response schema (stdout line):
  {"id": "r-1", "ok": true, "result": {...}}
  {"id": "r-1", "ok": false, "error": "..."}

Design:
  - Result cache keyed by request id so accept/reject can reference
    candidates without resending them.
  - No blocking LLM calls; stays in live lane.
  - Single ShardStore for process lifetime.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations

import json
import sys
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Any

# ensure src/ is importable whether spawned from repo root or elsewhere
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thought_completer_seq001_v001 import (  # noqa: E402
    ShardStore,
    Candidate,
    complete,
    accept,
    reject,
    mark_condition,
    closure_rate_7d,
)


MAX_CACHED_RESULTS = 64


def _log(msg: str) -> None:
    sys.stderr.write(f"[completer] {msg}\n")
    sys.stderr.flush()


def _emit(resp: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _candidate_from_cache(cached: dict[str, Any], idx: int) -> Candidate:
    cs = cached.get("candidates") or []
    if not 0 <= idx < len(cs):
        raise IndexError(f"candidate_index {idx} out of range ({len(cs)})")
    c = cs[idx]
    return Candidate(
        completion=c["completion"],
        confidence=c["confidence"],
        source=c["source"],
        intent_key=c.get("intent_key"),
        file_targets=list(c.get("file_targets") or []),
        rationale=c.get("rationale", ""),
    )


def serve() -> int:
    store = ShardStore()
    cache: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    _log(f"ready db={store.db_path}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req_id: str | None = None
        try:
            req = json.loads(line)
            op = req.get("op")
            req_id = req.get("id")

            if op == "ping":
                _emit({"id": req_id, "ok": True, "result": {"pong": True}})

            elif op == "complete":
                result = complete(
                    fragment=req["fragment"],
                    store=store,
                    recent_session_keys=req.get("recent_keys") or None,
                    open_files=req.get("open_files") or None,
                )
                payload = result.to_dict()
                if req_id:
                    cache[req_id] = payload
                    if len(cache) > MAX_CACHED_RESULTS:
                        cache.popitem(last=False)
                _emit({"id": req_id, "ok": True, "result": payload})

            elif op == "accept":
                ref = req.get("result_id")
                cached = cache.get(ref) if ref else None
                if cached is None:
                    raise KeyError(f"result_id {ref!r} not in cache")
                cand = _candidate_from_cache(cached, int(req["candidate_index"]))
                intent_id = accept(
                    fragment=req.get("fragment") or cached.get("fragment", ""),
                    chosen=cand,
                    store=store,
                    session_id=req.get("session_id"),
                )
                _emit({"id": req_id, "ok": True, "result": {"intent_id": intent_id}})

            elif op == "reject":
                ref = req.get("result_id")
                cached = cache.get(ref) if ref else None
                if cached is None:
                    raise KeyError(f"result_id {ref!r} not in cache")
                rejected_cand = _candidate_from_cache(cached, int(req["candidate_index"]))
                chosen_cand = None
                if req.get("chosen_index") is not None:
                    chosen_cand = _candidate_from_cache(cached, int(req["chosen_index"]))
                reject(
                    fragment=req.get("fragment") or cached.get("fragment", ""),
                    rejected=rejected_cand,
                    chosen=chosen_cand,
                    reason=req.get("reason"),
                    store=store,
                    session_id=req.get("session_id"),
                )
                _emit({"id": req_id, "ok": True, "result": {}})

            elif op == "mark":
                mark_condition(store, req["intent_id"], req["condition"])
                _emit({"id": req_id, "ok": True, "result": {}})

            elif op == "closure_rate":
                rate = closure_rate_7d(store)
                _emit({"id": req_id, "ok": True, "result": {"rate_7d": rate}})

            elif op == "shutdown":
                _emit({"id": req_id, "ok": True, "result": {"bye": True}})
                break

            else:
                _emit({"id": req_id, "ok": False, "error": f"unknown op {op!r}"})

        except Exception as exc:
            _log(traceback.format_exc().strip())
            _emit({"id": req_id, "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    store.close()
    _log("shutdown")
    return 0


if __name__ == "__main__":
    sys.exit(serve())
