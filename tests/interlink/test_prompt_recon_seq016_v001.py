"""Interlink self-test for prompt_recon_seq016_v001.

Auto-generated. This test keeps prompt_recon_seq016_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 57 lines | ~621 tokens
# DESC:   interlink_self_test_for_prompt
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.p_prc_s016_v001 import reconstruct_latest, track_copilot_prompt_mutations
    assert callable(reconstruct_latest), "reconstruct_latest must be callable"
    assert callable(track_copilot_prompt_mutations), "track_copilot_prompt_mutations must be callable"
    print(f"  ✓ prompt_recon_seq016_v001: 2 exports verified")

def test_reconstruct_latest_contract():
    """Data flow contract: reconstruct_latest(root) → output."""
    from src.p_prc_s016_v001 import reconstruct_latest
    # smoke test: function exists and is callable
    assert reconstruct_latest.__name__ == "reconstruct_latest"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = reconstruct_latest(root)
    assert result is not None, "reconstruct_latest returned None"
    print(f"  ✓ reconstruct_latest: contract holds")

def test_track_copilot_prompt_mutations_contract():
    """Data flow contract: track_copilot_prompt_mutations(root) → output."""
    from src.p_prc_s016_v001 import track_copilot_prompt_mutations
    # smoke test: function exists and is callable
    assert track_copilot_prompt_mutations.__name__ == "track_copilot_prompt_mutations"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = track_copilot_prompt_mutations(root)
    assert result is not None, "track_copilot_prompt_mutations returned None"
    print(f"  ✓ track_copilot_prompt_mutations: contract holds")

def run_interlink_test():
    """Run all interlink checks for prompt_recon_seq016_v001."""
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
    print(f"  prompt_recon_seq016_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
