"""learning_loop_seq013_single_cycle_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v002 | 95 lines | ~826 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any

def run_single_cycle(
    root: Path, entry: dict[str, Any], state: dict[str, Any],
    use_deepseek: bool = True,
) -> dict[str, Any]:
    """Run one forward → backward cycle for a single journal entry.

    Returns cycle result dict.
    """
    from pigeon_brain.flow._resolve import flow_import
    run_flow, run_multi, load_graph_data = flow_import(
        "flow_engine_seq003", "run_flow", "run_multi", "load_graph_data",
    )
    write_task = flow_import("task_writer_seq005", "write_task")
    backward_pass, log_forward_pass = flow_import(
        "backward_seq007", "backward_pass", "log_forward_pass",
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
