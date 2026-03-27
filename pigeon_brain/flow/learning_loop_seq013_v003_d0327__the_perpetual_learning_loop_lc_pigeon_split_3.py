# ┌──────────────────────────────────────────────┐
# │  learning_loop — perpetual forward → backward  │
# │  training loop. Never stops. pigeon_brain/flow │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-27T08:45:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  wire prediction scoring into cycle
# ── /pulse ──
"""
The perpetual learning loop.

Watches the prompt journal for new entries. For each new entry:
  1. Fires a forward pass (task_seed = operator's message)
  2. Logs the electron
  3. Runs a DeepSeek-powered backward pass (journal entry = ground truth)
  4. Node memory accumulates. Policies rebuild. Nodes get smarter.
  5. Loop sleeps. Wakes. Repeats. Forever.

The loop also fires phantom electrons every N cycles to predict
what the operator will need before they ask.

Run:
  py -m pigeon_brain.flow loop          # start the loop (foreground)
  py -m pigeon_brain.flow loop --once   # single iteration then exit
  py -m pigeon_brain.flow loop --catch-up  # process all unprocessed entries

Cost: ~$0.003 per forward+backward cycle (DeepSeek-chat).
"""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v003 | 315 lines | ~2,874 tokens
# DESC:   the_perpetual_learning_loop
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 2
# ──────────────────────────────────────────────
# ── pigeon: SEQ 013 | v001 | deepseek_backprop | 2026-03-27 ──
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOOP_STATE_FILE = "learning_loop_state.json"
POLL_INTERVAL = 5.0        # seconds between journal checks
PREDICT_EVERY = 10         # fire phantoms every N cycles
MAX_ENTRIES_PER_WAKE = 5   # process at most N entries per wake cycle


def _state_path(root: Path) -> Path:
    return root / "pigeon_brain" / LOOP_STATE_FILE


def _load_state(root: Path) -> dict[str, Any]:
    """Load loop state: tracks which journal entries have been processed."""
    p = _state_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "last_processed_ts": None,
        "last_processed_line": 0,
        "total_cycles": 0,
        "total_forward": 0,
        "total_backward": 0,
        "total_predictions": 0,
        "total_cost": 0.0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def _save_state(root: Path, state: dict[str, Any]) -> None:
    p = _state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def _load_journal_entries(root: Path, after_line: int = 0) -> list[dict[str, Any]]:
    """Load prompt journal entries after a given line number."""
    journal = root / "logs" / "prompt_journal.jsonl"
    if not journal.exists():
        return []
    lines = journal.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for i, line in enumerate(lines):
        if i < after_line:
            continue
        try:
            entry = json.loads(line)
            entry["_line_num"] = i
            entries.append(entry)
        except json.JSONDecodeError:
            continue
    return entries


def run_single_cycle(
    root: Path, entry: dict[str, Any], state: dict[str, Any],
    use_deepseek: bool = True,
) -> dict[str, Any]:
    """Run one forward → backward cycle for a single journal entry.

    Returns cycle result dict.
    """
    from .flow_engine_seq003_v002_d0324__the_flow_engine_is_the_lc_flow_engine_context import (
        run_flow, run_multi, load_graph_data,
    )
    from .task_writer_seq005_v002_d0324__the_river_delta_where_all_lc_flow_engine_context import (
        write_task,
    )
    from .backward_seq007_v003_d0327__backward_pass_walks_electron_path_lc_pigeon_split_3 import (
        backward_pass, log_forward_pass,
    )

    task_seed = entry.get("msg", "")
    if not task_seed or len(task_seed) < 5:
        return {"skipped": True, "reason": "empty_msg"}

    graph_data = load_graph_data(root)
    if not graph_data.get("nodes"):
        return {"skipped": True, "reason": "no_graph_data"}

    # ── FORWARD PASS ──
    try:
        packet = run_flow(root, task_seed, mode="targeted", graph_data=graph_data)
    except Exception as e:
        logger.warning(f"[loop] Forward pass failed: {e}")
        return {"skipped": True, "reason": f"forward_error: {e}"}

    summary = packet.summary()
    summary["accumulated"] = [
        {"node": i.node, "fears": i.fears, "dual_score": i.dual_score,
         "relevance": i.relevance}
        for i in packet.accumulated
    ]
    electron_id = log_forward_pass(root, summary)
    state["total_forward"] += 1

    # Also run heat mode for richer learning signal
    try:
        heat_packet = run_flow(root, task_seed, mode="heat", graph_data=graph_data)
        heat_summary = heat_packet.summary()
        heat_summary["accumulated"] = [
            {"node": i.node, "fears": i.fears, "dual_score": i.dual_score,
             "relevance": i.relevance}
            for i in heat_packet.accumulated
        ]
        heat_eid = log_forward_pass(root, heat_summary)
    except Exception:
        heat_eid = None

    # ── BACKWARD PASS (DeepSeek-powered) ──
    backward_results = []
    try:
        backward_results = backward_pass(
            root, electron_id, entry,
            fix_context=task_seed,
            use_deepseek=use_deepseek,
        )
        state["total_backward"] += 1
    except Exception as e:
        logger.warning(f"[loop] Backward pass failed: {e}")

    # Backward for heat electron too
    heat_backward = []
    if heat_eid:
        try:
            heat_backward = backward_pass(
                root, heat_eid, entry,
                fix_context=task_seed,
                use_deepseek=False,  # save cost, heuristic is fine for second pass
            )
        except Exception:
            pass

    task_output = write_task(packet)

    return {
        "skipped": False,
        "electron_id": electron_id,
        "heat_electron_id": heat_eid,
        "path": packet.path,
        "nodes_awakened": len(packet.accumulated),
        "loss_from_backward": backward_results[0]["loss"] if backward_results else None,
        "nodes_trained": len(backward_results) + len(heat_backward),
        "task_preview": task_output[:200],
    }


def run_prediction_cycle(root: Path, state: dict[str, Any]) -> int:
    """Fire phantom electrons from cognitive profile."""
    from .predictor_seq009_v003_d0327__fires_phantom_electrons_using_cognitive_lc_pigeon_split_3 import (
        predict_next_needs,
    )
    from .flow_engine_seq003_v002_d0324__the_flow_engine_is_the_lc_flow_engine_context import (
        run_flow,
    )
    # Score any existing predictions against edit sessions (primary)
    try:
        from .prediction_scorer_seq014_v003_d0327__edit_session_based_lc_pigeon_split_3 import (
            score_predictions_post_edit,
        )
        score_result = score_predictions_post_edit(root)
        if score_result.get("status") == "scored":
            logger.info(
                f"[loop] Scored {score_result['predictions_scored']} predictions "
                f"avg_combined={score_result['avg_combined']:.3f} "
                f"avg_f1={score_result['avg_f1']:.3f} "
                f"overconf={score_result['overconfidence_rate']:.2f} "
                f"nodes_updated={score_result['nodes_updated']}"
            )
    except Exception as e:
        logger.warning(f"[loop] Prediction scoring failed: {e}")

    predictions = predict_next_needs(root, run_flow_fn=run_flow)
    state["total_predictions"] += len(predictions)
    return len(predictions)


def catch_up(root: Path, use_deepseek: bool = True) -> dict[str, Any]:
    """Process all unprocessed journal entries. Returns summary."""
    state = _load_state(root)
    entries = _load_journal_entries(root, after_line=state["last_processed_line"])

    results = []
    for entry in entries:
        result = run_single_cycle(root, entry, state, use_deepseek=use_deepseek)
        results.append(result)
        state["last_processed_line"] = entry["_line_num"] + 1
        state["last_processed_ts"] = entry.get("ts")
        state["total_cycles"] += 1
        _save_state(root, state)
        logger.info(
            f"[loop] cycle={state['total_cycles']} "
            f"eid={result.get('electron_id', 'skip')[:8]} "
            f"nodes_trained={result.get('nodes_trained', 0)}"
        )

    trained = sum(r.get("nodes_trained", 0) for r in results if not r.get("skipped"))
    return {
        "entries_processed": len(results),
        "entries_skipped": sum(1 for r in results if r.get("skipped")),
        "total_nodes_trained": trained,
        "cycles": state["total_cycles"],
    }


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
