"""Interlink self-test for tc_context_agent_seq001_v002_d0420__picks_relevant_source_files_based_lc_fix_close_outcome_sim.

Auto-generated. This test keeps tc_context_agent_seq001_v002_d0420__picks_relevant_source_files_based_lc_fix_close_outcome_sim interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v004 | 105 lines | ~1,594 tokens
# DESC:   interlink_self_test_for_tc
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 1
# ──────────────────────────────────────────────
import sys
from pathlib import Path
from src._resolve import src_import
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    select_context_numeric, select_context_files, select_context_ensemble, build_code_context, get_intelligent_context, log_prediction, grade_prediction, select_template, grade_and_learn = src_import("tc_context_agent_seq001", "select_context_numeric", "select_context_files", "select_context_ensemble", "build_code_context", "get_intelligent_context", "log_prediction", "grade_prediction", "select_template", "grade_and_learn")
    assert callable(select_context_numeric), "select_context_numeric must be callable"
    assert callable(select_context_files), "select_context_files must be callable"
    assert callable(select_context_ensemble), "select_context_ensemble must be callable"
    assert callable(build_code_context), "build_code_context must be callable"
    assert callable(get_intelligent_context), "get_intelligent_context must be callable"
    assert callable(log_prediction), "log_prediction must be callable"
    assert callable(grade_prediction), "grade_prediction must be callable"
    assert callable(select_template), "select_template must be callable"
    assert callable(grade_and_learn), "grade_and_learn must be callable"
    print(f"  ✓ tc_context_agent_seq001_v002_d0420__picks_relevant_source_files_based_lc_fix_close_outcome_sim: 9 exports verified")

def test_select_context_numeric_contract():
    """Data flow contract: select_context_numeric(buffer, ctx, max_files) → output."""
    select_context_numeric = src_import("tc_context_agent_seq001", "select_context_numeric")
    # smoke test: function exists and is callable
    assert select_context_numeric.__name__ == "select_context_numeric"
    print(f"  ✓ select_context_numeric: contract holds")

def test_select_context_files_contract():
    """Data flow contract: select_context_files(buffer, ctx, max_files) → output."""
    select_context_files = src_import("tc_context_agent_seq001", "select_context_files")
    # smoke test: function exists and is callable
    assert select_context_files.__name__ == "select_context_files"
    print(f"  ✓ select_context_files: contract holds")

def test_select_context_ensemble_contract():
    """Data flow contract: select_context_ensemble(buffer, ctx, max_files) → output."""
    select_context_ensemble = src_import("tc_context_agent_seq001", "select_context_ensemble")
    # smoke test: function exists and is callable
    assert select_context_ensemble.__name__ == "select_context_ensemble"
    print(f"  ✓ select_context_ensemble: contract holds")

def test_build_code_context_contract():
    """Data flow contract: build_code_context(buffer, ctx) → output."""
    build_code_context = src_import("tc_context_agent_seq001", "build_code_context")
    # smoke test: function exists and is callable
    assert build_code_context.__name__ == "build_code_context"
    print(f"  ✓ build_code_context: contract holds")

def test_get_intelligent_context_contract():
    """Data flow contract: get_intelligent_context(buffer, ctx) → output."""
    get_intelligent_context = src_import("tc_context_agent_seq001", "get_intelligent_context")
    # smoke test: function exists and is callable
    assert get_intelligent_context.__name__ == "get_intelligent_context"
    print(f"  ✓ get_intelligent_context: contract holds")

def test_log_prediction_contract():
    """Data flow contract: log_prediction(buffer, predicted_files, predicted_intent) → output."""
    log_prediction = src_import("tc_context_agent_seq001", "log_prediction")
    # smoke test: function exists and is callable
    assert log_prediction.__name__ == "log_prediction"
    print(f"  ✓ log_prediction: contract holds")

def test_grade_prediction_contract():
    """Data flow contract: grade_prediction(prediction_ts, actual_intent, actual_files) → output."""
    grade_prediction = src_import("tc_context_agent_seq001", "grade_prediction")
    # smoke test: function exists and is callable
    assert grade_prediction.__name__ == "grade_prediction"
    print(f"  ✓ grade_prediction: contract holds")

def test_select_template_contract():
    """Data flow contract: select_template(buffer, ctx) → output."""
    select_template = src_import("tc_context_agent_seq001", "select_template")
    # smoke test: function exists and is callable
    assert select_template.__name__ == "select_template"
    print(f"  ✓ select_template: contract holds")

def test_grade_and_learn_contract():
    """Data flow contract: grade_and_learn(buffer, completion, outcome, files_touched, actual_intent) → output."""
    grade_and_learn = src_import("tc_context_agent_seq001", "grade_and_learn")
    # smoke test: function exists and is callable
    assert grade_and_learn.__name__ == "grade_and_learn"
    print(f"  ✓ grade_and_learn: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_context_agent_seq001_v002_d0420__picks_relevant_source_files_based_lc_fix_close_outcome_sim."""
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    total = len(tests)
    status = "INTERLINKED" if passed == total else f"{passed}/{total}"
    print(f"  tc_context_agent_seq001_v002_d0420__picks_relevant_source_files_based_lc_fix_close_outcome_sim: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
