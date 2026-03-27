"""learning_loop_seq013_catch_up_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 30 lines | ~309 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any

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
