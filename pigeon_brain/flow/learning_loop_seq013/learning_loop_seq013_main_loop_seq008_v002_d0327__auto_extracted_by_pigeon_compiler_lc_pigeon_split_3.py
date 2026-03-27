"""learning_loop_seq013_main_loop_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 72 lines | ~706 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import time

def run_loop(root: Path, once: bool = False, use_deepseek: bool = True) -> None:
    """The perpetual learning loop. Watches journal, trains nodes, never stops.

    Args:
        root: project root
        once: if True, process new entries once then exit
        use_deepseek: use DeepSeek for rich backward analysis
    """
    state = _load_state(root)
    cycle_since_predict = 0

    logger.info(f"[loop] Starting perpetual learning loop (total_cycles={state['total_cycles']})")
    print(f"[learning_loop] Started — {state['total_cycles']} prior cycles, "
          f"{state['total_forward']} forward, {state['total_backward']} backward")

    while True:
        entries = _load_journal_entries(root, after_line=state["last_processed_line"])

        if not entries:
            if once:
                print("[learning_loop] No new entries. Done.")
                return
            time.sleep(POLL_INTERVAL)
            continue

        # Process up to MAX_ENTRIES_PER_WAKE
        batch = entries[:MAX_ENTRIES_PER_WAKE]
        for entry in batch:
            result = run_single_cycle(root, entry, state, use_deepseek=use_deepseek)
            state["last_processed_line"] = entry["_line_num"] + 1
            state["last_processed_ts"] = entry.get("ts")
            state["total_cycles"] += 1
            cycle_since_predict += 1
            _save_state(root, state)

            if result.get("skipped"):
                print(f"  [skip] {result.get('reason', '?')}")
            else:
                eid = result.get("electron_id", "?")[:8]
                nodes = result.get("nodes_trained", 0)
                loss = result.get("loss_from_backward")
                loss_str = f"{loss:.3f}" if loss is not None else "n/a"
                print(f"  [cycle {state['total_cycles']}] "
                      f"eid={eid} path={len(result.get('path', []))} "
                      f"nodes_trained={nodes} loss={loss_str}")

        # Prediction cycle
        if cycle_since_predict >= PREDICT_EVERY:
            try:
                n = run_prediction_cycle(root, state)
                if n:
                    print(f"  [predict] fired {n} phantom electrons")
                cycle_since_predict = 0
                _save_state(root, state)
            except Exception as e:
                logger.warning(f"[loop] Prediction failed: {e}")

        if once:
            print(f"[learning_loop] Processed {len(batch)} entries. Done.")
            return

        time.sleep(POLL_INTERVAL)

POLL_INTERVAL = 5.0        # seconds between journal checks

PREDICT_EVERY = 10         # fire phantoms every N cycles

MAX_ENTRIES_PER_WAKE = 5   # process at most N entries per wake cycle
