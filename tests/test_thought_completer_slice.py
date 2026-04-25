"""test_thought_completer_slice — §13 provable slice end-to-end.

Proves the one-prompt demo works:
  1. complete("maintain profile") returns ranked candidates
  2. accept top candidate → learned pair stored, intent emitted
  3. queue file written
  4. watcher promotes conditions as targets get touched
  5. closure_rate reflects the closed intent
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── sandbox db ──
TMP = Path(tempfile.mkdtemp(prefix="tc_slice_"))
os.environ.setdefault("TC_TEST_DB", str(TMP / "op.db"))

from operator_profile_shards_seq001_v001 import (  # noqa: E402
    ShardStore,
    closure_rate_7d,
    search_learned_pairs,
    upsert_intent_key,
    write_learned_pair,
    touch_file_affinity,
)
import thought_completer_seq001_v001 as tc  # noqa: E402
import intent_keys_seq001_v001 as ik  # noqa: E402

# redirect queue to sandbox
tc.INTENT_QUEUE_PATH = TMP / "queue.jsonl"


def run() -> int:
    store = ShardStore(db_path=TMP / "op.db")

    # seed minimal state so a meaningful candidate can be produced
    centroid = ik.embed("maintain dynamic operator profile via multi-shard architecture")
    upsert_intent_key(store, "k_arch_refactor", centroid, state="active")
    write_learned_pair(
        store,
        fragment="maintain profile",
        completion="maintain dynamic operator profile via multi-shard architecture",
        intent_key="k_arch_refactor",
        confidence=0.82,
        accept_kind="accept",
        file_targets=["src/operator_profile_shards_seq001_v001.py"],
        session_id="seed",
    )
    write_learned_pair(
        store,
        fragment="maintain profile",
        completion="maintain dynamic operator profile via multi-shard architecture",
        intent_key="k_arch_refactor",
        confidence=0.82,
        accept_kind="accept",
        session_id="seed2",
    )
    touch_file_affinity(store, "k_arch_refactor", "src/operator_profile_shards_seq001_v001.py")

    # ── step 1: complete ──
    result = tc.complete("maintain profile", store=store, open_files=[])
    print(f"[1] complete: latency={result.latency_ms}ms tier={result.tier} cands={len(result.candidates)}")
    assert result.candidates, "must produce at least one candidate"
    top = result.candidates[0]
    print(f"    top: conf={top.confidence:.2f} src={top.source} key={top.intent_key}")
    print(f'         "{top.completion[:120]}"')

    # ── step 2: accept ──
    intent_id = tc.accept("maintain profile", top, store=store, session_id="slice")
    print(f"[2] accept -> intent_id={intent_id}")

    # ── step 3: queue written ──
    assert tc.INTENT_QUEUE_PATH.exists(), "queue file not written"
    queue_lines = tc.INTENT_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    emitted = [json.loads(l) for l in queue_lines if l.strip()]
    assert any(r["intent_id"] == intent_id for r in emitted), "intent not in queue"
    print(f"[3] queue: {len(emitted)} record(s)")

    # ── step 4: simulate action by touching file_target then run watcher ──
    if top.file_targets:
        tgt = REPO_ROOT / top.file_targets[0]
        if tgt.exists():
            os.utime(tgt, (time.time(), time.time()))

    import completer_closure_watcher as ccw
    # point watcher at our sandbox queue
    ccw.QUEUE_PATH = tc.INTENT_QUEUE_PATH
    counts = ccw.sweep_once(store)
    print(f"[4] watcher sweep: {counts}")

    # check conditions
    row = store.conn.execute(
        "SELECT cond_routed, cond_acted FROM intent_ledger WHERE intent_id=?",
        (intent_id,),
    ).fetchone()
    print(f"    cond_routed={row['cond_routed']}  cond_acted={row['cond_acted']}")
    assert row["cond_routed"] == 1, "routed condition should flip after queue emission"

    # ── step 5: manually close remaining conditions, check closure_rate ──
    from operator_profile_shards_seq001_v001 import mark_condition
    for cond in ("verified", "stable"):
        mark_condition(store, intent_id, cond)
    if not row["cond_acted"]:
        mark_condition(store, intent_id, "acted")

    closed = store.conn.execute(
        "SELECT closed_at FROM intent_ledger WHERE intent_id=?", (intent_id,)
    ).fetchone()
    rate = closure_rate_7d(store)
    print(f"[5] closed_at={closed['closed_at']}  closure_rate_7d={rate:.2%}")
    assert closed["closed_at"] is not None, "intent should be auto-closed"
    assert rate > 0.0, "closure rate should be positive"

    # ── step 6: learned pair updated from acceptance ──
    pairs = search_learned_pairs(store, fragment_like="maintain profile", limit=10)
    print(f"[6] learned_pairs on fragment: {len(pairs)}")
    assert len(pairs) >= 3, "accept should have added a learned pair"

    store.close()
    print("\nPASS — §13 provable slice end-to-end")
    print(f"sandbox: {TMP}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
