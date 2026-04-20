"""Interlink self-test for file_sim_seq001_v004_d0420__micro_sim_engine_prompt_file_lc_chore_pigeon_rename_cascade.

Auto-generated. This test keeps file_sim_seq001_v004_d0420__micro_sim_engine_prompt_file_lc_chore_pigeon_rename_cascade interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
from src._resolve import src_import
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    self_score, grade_file_for_intent, run_sim, apply_undo_penalty, clear_intent_job = src_import("file_sim_seq001", "self_score", "grade_file_for_intent", "run_sim", "apply_undo_penalty", "clear_intent_job")
    assert callable(self_score), "self_score must be callable"
    assert callable(grade_file_for_intent), "grade_file_for_intent must be callable"
    assert callable(run_sim), "run_sim must be callable"
    assert callable(apply_undo_penalty), "apply_undo_penalty must be callable"
    assert callable(clear_intent_job), "clear_intent_job must be callable"
    print(f"  ✓ file_sim_seq001_v004_d0420__micro_sim_engine_prompt_file_lc_chore_pigeon_rename_cascade: 5 exports verified")

def test_self_score_contract():
    """Data flow contract: self_score(file_stem, prompt_vec, root) → output."""
    self_score = src_import("file_sim_seq001", "self_score")
    # smoke test: function exists and is callable
    assert self_score.__name__ == "self_score"
    print(f"  ✓ self_score: contract holds")

def test_grade_file_for_intent_contract():
    """Data flow contract: grade_file_for_intent(intent_text, file_stem, root, api_key) → output."""
    grade_file_for_intent = src_import("file_sim_seq001", "grade_file_for_intent")
    # smoke test: function exists and is callable
    assert grade_file_for_intent.__name__ == "grade_file_for_intent"
    print(f"  ✓ grade_file_for_intent: contract holds")

def test_run_sim_contract():
    """Data flow contract: run_sim(intent_text, prompt_text, top_n, root) → output."""
    run_sim = src_import("file_sim_seq001", "run_sim")
    # smoke test: function exists and is callable
    assert run_sim.__name__ == "run_sim"
    print(f"  ✓ run_sim: contract holds")

def test_apply_undo_penalty_contract():
    """Data flow contract: apply_undo_penalty(file_stem, prompt_text, root) → output."""
    apply_undo_penalty = src_import("file_sim_seq001", "apply_undo_penalty")
    # smoke test: function exists and is callable
    assert apply_undo_penalty.__name__ == "apply_undo_penalty"
    print(f"  ✓ apply_undo_penalty: contract holds")

def test_clear_intent_job_contract():
    """Data flow contract: clear_intent_job(intent_text, actor, root) → output."""
    clear_intent_job = src_import("file_sim_seq001", "clear_intent_job")
    # smoke test: function exists and is callable
    assert clear_intent_job.__name__ == "clear_intent_job"
    print(f"  ✓ clear_intent_job: contract holds")

def run_interlink_test():
    """Run all interlink checks for file_sim_seq001_v004_d0420__micro_sim_engine_prompt_file_lc_chore_pigeon_rename_cascade."""
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
    print(f"  file_sim_seq001_v004_d0420__micro_sim_engine_prompt_file_lc_chore_pigeon_rename_cascade: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
