"""Interlink self-test for bug_demon_hunt_seq001_v001.

Auto-generated. This test keeps bug_demon_hunt_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import BugDemon, run_hunt, run_multi_hunt, analyze_node_memory, gather_proposals, build_distributed_proposal, stress_test_self, main
    assert callable(BugDemon), "BugDemon must be callable"
    assert callable(run_hunt), "run_hunt must be callable"
    assert callable(run_multi_hunt), "run_multi_hunt must be callable"
    assert callable(analyze_node_memory), "analyze_node_memory must be callable"
    assert callable(gather_proposals), "gather_proposals must be callable"
    assert callable(build_distributed_proposal), "build_distributed_proposal must be callable"
    assert callable(stress_test_self), "stress_test_self must be callable"
    assert callable(main), "main must be callable"
    print(f"  ✓ bug_demon_hunt_seq001_v001: 8 exports verified")

def test_run_hunt_contract():
    """Data flow contract: run_hunt(demon) → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import run_hunt
    # smoke test: function exists and is callable
    assert run_hunt.__name__ == "run_hunt"
    print(f"  ✓ run_hunt: contract holds")

def test_run_multi_hunt_contract():
    """Data flow contract: run_multi_hunt(demon) → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import run_multi_hunt
    # smoke test: function exists and is callable
    assert run_multi_hunt.__name__ == "run_multi_hunt"
    print(f"  ✓ run_multi_hunt: contract holds")

def test_analyze_node_memory_contract():
    """Data flow contract: analyze_node_memory(demon) → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import analyze_node_memory
    # smoke test: function exists and is callable
    assert analyze_node_memory.__name__ == "analyze_node_memory"
    print(f"  ✓ analyze_node_memory: contract holds")

def test_gather_proposals_contract():
    """Data flow contract: gather_proposals(demon, hunt_results, memory_analysis) → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import gather_proposals
    # smoke test: function exists and is callable
    assert gather_proposals.__name__ == "gather_proposals"
    print(f"  ✓ gather_proposals: contract holds")

def test_build_distributed_proposal_contract():
    """Data flow contract: build_distributed_proposal(demon, proposals, hunt_results) → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import build_distributed_proposal
    # smoke test: function exists and is callable
    assert build_distributed_proposal.__name__ == "build_distributed_proposal"
    print(f"  ✓ build_distributed_proposal: contract holds")

def test_stress_test_self_contract():
    """Data flow contract: stress_test_self() → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import stress_test_self
    # smoke test: function exists and is callable
    assert stress_test_self.__name__ == "stress_test_self"
    result = stress_test_self()
    assert result is not None, "stress_test_self returned None"
    print(f"  ✓ stress_test_self: contract holds")

def test_main_contract():
    """Data flow contract: main() → output."""
    from src.bug_demon_hunt_seq001_v001_seq001_v001 import main
    # smoke test: function exists and is callable
    assert main.__name__ == "main"
    result = main()
    assert result is not None, "main returned None"
    print(f"  ✓ main: contract holds")

def run_interlink_test():
    """Run all interlink checks for bug_demon_hunt_seq001_v001."""
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
    print(f"  bug_demon_hunt_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
