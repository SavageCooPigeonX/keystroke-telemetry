"""push_cycle_seq025_orchestrator_decomposed_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v003 | 89 lines | ~811 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: research_lab_autonomous
# LAST:   2026-03-30 @ 8888287
# SESSIONS: 2
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def run_push_cycle(root: Path, commit_hash: str, intent: str,
                   changed_files: list[str]) -> dict[str, Any]:
    """Run one push-based learning cycle. Called by git_plugin post-commit."""
    state = _load_state(root)

    # 1. Collect operator signal (all prompts since last push)
    entries = _load_journal_since(root, state["last_journal_line"])
    operator = _extract_operator_signal(entries)

    # 2. Collect copilot signal (what code changed)
    copilot = _extract_copilot_signal(changed_files)

    # 3. Compute sync
    sync = _compute_sync(operator, copilot)

    # 4. Generate dual coaching
    coaching = _generate_dual_coaching(operator, copilot, sync)

    # 5. Score old predictions from last cycle
    score_result = _score_old_predictions(root)

    # 6. Backward pass on key journal entries (gradient distribution)
    backward_results = _run_backward_on_entries(root, entries)

    # 7. Fire new predictions (what will operator want next push?)
    predictions = _fire_predictions(root)

    # 7b. Synthesize research log (the system studying itself)
    try:
        import glob, importlib
        rl_files = glob.glob(str(root / 'src' / 'research_lab_seq029*.py'))
        if rl_files:
            spec = importlib.util.spec_from_file_location('research_lab', rl_files[0])
            rl_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rl_mod)
            rl_mod.synthesize_research(root)
    except Exception:
        pass  # research log is optional — never block push cycle

    # 8. Build cycle record
    now = datetime.now(timezone.utc).isoformat()
    total_journal_lines = state["last_journal_line"] + len(entries)
    cycle = {
        "ts": now,
        "commit": commit_hash,
        "intent": intent,
        "cycle_number": state["total_cycles"] + 1,
        "operator_signal": operator,
        "copilot_signal": copilot,
        "sync": sync,
        "coaching": coaching,
        "prediction_score": score_result,
        "backward_runs": len(backward_results),
        "new_predictions": len(predictions),
    }

    # 8. Append to cycle log
    log_path = root / CYCLE_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle) + "\n")

    # 9. Update state
    state["last_journal_line"] = total_journal_lines
    state["total_cycles"] += 1
    state["last_commit"] = commit_hash
    state["last_sync_score"] = sync["score"]
    state["last_prediction_count"] = len(predictions)
    state["updated_at"] = now
    _save_state(root, state)

    # 10. Inject predictions + coaching into copilot-instructions.md
    _inject_predictions_into_prompt(root, predictions, coaching)

    return cycle
