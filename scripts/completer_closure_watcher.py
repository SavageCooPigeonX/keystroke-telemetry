"""completer_closure_watcher — auto-mark intent ledger conditions (Phase 4).

Scans pending intents in `intent_ledger` and applies closure rules:
  - cond_routed: queue record exists (emitted to logs/completer_intent_queue.jsonl)
  - cond_acted : any file_target mtime > emitted_at
  - cond_verified: no self_fix HIGH/CRITICAL regression for file_targets since emission
  - cond_stable: cond_verified + 1 hour of quiet (no new touches to file_targets)

Runs either once (--once) or as a slow poll (--watch, 30s interval).
Lane C (background).
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from operator_profile_shards_seq001_v001 import (  # noqa: E402
    ShardStore,
    closure_rate_7d,
    mark_condition,
)

QUEUE_PATH = REPO_ROOT / "logs" / "completer_intent_queue.jsonl"
STABLE_QUIET_SECS = 3600.0


def _load_queue_index() -> dict[str, dict]:
    if not QUEUE_PATH.exists():
        return {}
    idx: dict[str, dict] = {}
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        iid = rec.get("intent_id")
        if iid:
            idx[iid] = rec
    return idx


def _max_target_mtime(file_targets: list[str]) -> float:
    best = 0.0
    for rel in file_targets:
        fp = REPO_ROOT / rel
        try:
            m = fp.stat().st_mtime
            if m > best:
                best = m
        except OSError:
            continue
    return best


def sweep_once(store: ShardStore) -> dict[str, int]:
    queue_idx = _load_queue_index()
    counts = {"routed": 0, "acted": 0, "stable": 0, "scanned": 0}
    rows = store.conn.execute(
        "SELECT intent_id, file_targets_json, emitted_at, "
        "  cond_routed, cond_acted, cond_verified, cond_stable "
        "FROM intent_ledger WHERE closed_at IS NULL"
    ).fetchall()
    now = time.time()
    for r in rows:
        counts["scanned"] += 1
        iid = r["intent_id"]
        targets = json.loads(r["file_targets_json"] or "[]")

        if not r["cond_routed"] and iid in queue_idx:
            mark_condition(store, iid, "routed")
            counts["routed"] += 1

        if not r["cond_acted"] and targets:
            mtime = _max_target_mtime(targets)
            if mtime > float(r["emitted_at"]):
                mark_condition(store, iid, "acted")
                counts["acted"] += 1

        # cond_verified is conservatively left to external scanner integration.
        # For now, if acted AND no quieter than STABLE_QUIET_SECS → stable.
        if r["cond_verified"] and not r["cond_stable"] and targets:
            mtime = _max_target_mtime(targets)
            if mtime > 0 and (now - mtime) >= STABLE_QUIET_SECS:
                mark_condition(store, iid, "stable")
                counts["stable"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="completer closure watcher")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()

    store = ShardStore()
    if args.once or not args.watch:
        counts = sweep_once(store)
        rate = closure_rate_7d(store)
        print(json.dumps({"counts": counts, "closure_rate_7d": rate}, indent=2))
        store.close()
        return 0

    try:
        while True:
            counts = sweep_once(store)
            rate = closure_rate_7d(store)
            sys.stderr.write(
                f"[watcher] {time.strftime('%H:%M:%S')} "
                f"scanned={counts['scanned']} routed+{counts['routed']} "
                f"acted+{counts['acted']} stable+{counts['stable']} "
                f"rate_7d={rate:.2%}\n"
            )
            sys.stderr.flush()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
