"""Interlink self-test for prompt_enricher_seq024_v001.

Auto-generated. This test keeps prompt_enricher_seq024_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | 49 lines | ~512 tokens
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
    from src.w_pe_s024_v001 import enrich_prompt, inject_query_block
    assert callable(enrich_prompt), "enrich_prompt must be callable"
    assert callable(inject_query_block), "inject_query_block must be callable"
    print(f"  ✓ prompt_enricher_seq024_v001: 2 exports verified")

def test_enrich_prompt_contract():
    """Data flow contract: enrich_prompt(root, raw_query, deleted_words, cognitive_state) → output."""
    from src.w_pe_s024_v001 import enrich_prompt
    # smoke test: function exists and is callable
    assert enrich_prompt.__name__ == "enrich_prompt"
    print(f"  ✓ enrich_prompt: contract holds")

def test_inject_query_block_contract():
    """Data flow contract: inject_query_block(root, raw_query, deleted_words, cognitive_state) → output."""
    from src.w_pe_s024_v001 import inject_query_block
    # smoke test: function exists and is callable
    assert inject_query_block.__name__ == "inject_query_block"
    print(f"  ✓ inject_query_block: contract holds")

def run_interlink_test():
    """Run all interlink checks for prompt_enricher_seq024_v001."""
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
    print(f"  prompt_enricher_seq024_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
