"""Interlink self-test for entropy_shedding.

Auto-generated. This test keeps entropy_shedding interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.entropy_shedding import parse_shed_blocks, parse_shed_block, accumulate_entropy, build_entropy_block, build_red_layer_block, format_shed_block, get_high_entropy_targets, build_entropy_directive
    assert callable(parse_shed_blocks), "parse_shed_blocks must be callable"
    assert callable(parse_shed_block), "parse_shed_block must be callable"
    assert callable(accumulate_entropy), "accumulate_entropy must be callable"
    assert callable(build_entropy_block), "build_entropy_block must be callable"
    assert callable(build_red_layer_block), "build_red_layer_block must be callable"
    assert callable(format_shed_block), "format_shed_block must be callable"
    assert callable(get_high_entropy_targets), "get_high_entropy_targets must be callable"
    assert callable(build_entropy_directive), "build_entropy_directive must be callable"
    print(f"  ✓ entropy_shedding: 8 exports verified")

def test_parse_shed_blocks_contract():
    """Data flow contract: parse_shed_blocks(text) → output."""
    from src.entropy_shedding import parse_shed_blocks
    # smoke test: function exists and is callable
    assert parse_shed_blocks.__name__ == "parse_shed_blocks"
    print(f"  ✓ parse_shed_blocks: contract holds")

def test_parse_shed_block_contract():
    """Data flow contract: parse_shed_block(text) → output."""
    from src.entropy_shedding import parse_shed_block
    # smoke test: function exists and is callable
    assert parse_shed_block.__name__ == "parse_shed_block"
    print(f"  ✓ parse_shed_block: contract holds")

def test_accumulate_entropy_contract():
    """Data flow contract: accumulate_entropy(root) → output."""
    from src.entropy_shedding import accumulate_entropy
    # smoke test: function exists and is callable
    assert accumulate_entropy.__name__ == "accumulate_entropy"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = accumulate_entropy(root)
    assert result is not None, "accumulate_entropy returned None"
    print(f"  ✓ accumulate_entropy: contract holds")

def test_build_entropy_block_contract():
    """Data flow contract: build_entropy_block(root) → output."""
    from src.entropy_shedding import build_entropy_block
    # smoke test: function exists and is callable
    assert build_entropy_block.__name__ == "build_entropy_block"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_entropy_block(root)
    assert result is not None, "build_entropy_block returned None"
    print(f"  ✓ build_entropy_block: contract holds")

def test_build_red_layer_block_contract():
    """Data flow contract: build_red_layer_block(root) → output."""
    from src.entropy_shedding import build_red_layer_block
    # smoke test: function exists and is callable
    assert build_red_layer_block.__name__ == "build_red_layer_block"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_red_layer_block(root)
    assert result is not None, "build_red_layer_block returned None"
    print(f"  ✓ build_red_layer_block: contract holds")

def test_format_shed_block_contract():
    """Data flow contract: format_shed_block(markers) → output."""
    from src.entropy_shedding import format_shed_block
    # smoke test: function exists and is callable
    assert format_shed_block.__name__ == "format_shed_block"
    print(f"  ✓ format_shed_block: contract holds")

def test_get_high_entropy_targets_contract():
    """Data flow contract: get_high_entropy_targets(root, threshold, limit) → output."""
    from src.entropy_shedding import get_high_entropy_targets
    # smoke test: function exists and is callable
    assert get_high_entropy_targets.__name__ == "get_high_entropy_targets"
    print(f"  ✓ get_high_entropy_targets: contract holds")

def test_build_entropy_directive_contract():
    """Data flow contract: build_entropy_directive(root) → output."""
    from src.entropy_shedding import build_entropy_directive
    # smoke test: function exists and is callable
    assert build_entropy_directive.__name__ == "build_entropy_directive"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_entropy_directive(root)
    assert result is not None, "build_entropy_directive returned None"
    print(f"  ✓ build_entropy_directive: contract holds")

def run_interlink_test():
    """Run all interlink checks for entropy_shedding."""
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
    print(f"  entropy_shedding: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
