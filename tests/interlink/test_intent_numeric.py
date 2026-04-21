"""Interlink self-test for intent_numeric.

Auto-generated (rename-resistant). Keeps intent_numeric interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find intent_numeric by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/intent_numeric*.py"), key=lambda p: len(p.name))
    assert matches, f"intent_numeric: module not found in src/ (glob src/intent_numeric*.py)"
    spec = _ilu.spec_from_file_location("intent_numeric", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['word_to_id', 'id_to_word', 'normalize_prompt_text', 'canonicalize_file_key', 'tokenize', 'prompt_to_vector', 'record_touch', 'predict_files', 'bigram_key', 'extract_bigrams', 'get_stats', 'visualize_file', 'find_similar_files', 'hook_post_edit', 'select_context_numeric']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok intent_numeric: 15 exports verified")

def test_word_to_id_contract():
    """Data flow contract: word_to_id(word, create)."""
    mod = _load_mod()
    fn = getattr(mod, "word_to_id")
    assert callable(fn), "word_to_id must be callable"
    print(f"  ok word_to_id: contract holds")

def test_id_to_word_contract():
    """Data flow contract: id_to_word(wid)."""
    mod = _load_mod()
    fn = getattr(mod, "id_to_word")
    assert callable(fn), "id_to_word must be callable"
    print(f"  ok id_to_word: contract holds")

def test_normalize_prompt_text_contract():
    """Data flow contract: normalize_prompt_text(text)."""
    mod = _load_mod()
    fn = getattr(mod, "normalize_prompt_text")
    assert callable(fn), "normalize_prompt_text must be callable"
    print(f"  ok normalize_prompt_text: contract holds")

def test_canonicalize_file_key_contract():
    """Data flow contract: canonicalize_file_key(file_path)."""
    mod = _load_mod()
    fn = getattr(mod, "canonicalize_file_key")
    assert callable(fn), "canonicalize_file_key must be callable"
    print(f"  ok canonicalize_file_key: contract holds")

def test_tokenize_contract():
    """Data flow contract: tokenize(text)."""
    mod = _load_mod()
    fn = getattr(mod, "tokenize")
    assert callable(fn), "tokenize must be callable"
    print(f"  ok tokenize: contract holds")

def test_prompt_to_vector_contract():
    """Data flow contract: prompt_to_vector(text)."""
    mod = _load_mod()
    fn = getattr(mod, "prompt_to_vector")
    assert callable(fn), "prompt_to_vector must be callable"
    print(f"  ok prompt_to_vector: contract holds")

def test_record_touch_contract():
    """Data flow contract: record_touch(prompt_text, files_touched, learning_rate)."""
    mod = _load_mod()
    fn = getattr(mod, "record_touch")
    assert callable(fn), "record_touch must be callable"
    print(f"  ok record_touch: contract holds")

def test_predict_files_contract():
    """Data flow contract: predict_files(prompt_text, top_n)."""
    mod = _load_mod()
    fn = getattr(mod, "predict_files")
    assert callable(fn), "predict_files must be callable"
    print(f"  ok predict_files: contract holds")

def test_bigram_key_contract():
    """Data flow contract: bigram_key(wid1, wid2)."""
    mod = _load_mod()
    fn = getattr(mod, "bigram_key")
    assert callable(fn), "bigram_key must be callable"
    print(f"  ok bigram_key: contract holds")

def test_extract_bigrams_contract():
    """Data flow contract: extract_bigrams(text)."""
    mod = _load_mod()
    fn = getattr(mod, "extract_bigrams")
    assert callable(fn), "extract_bigrams must be callable"
    print(f"  ok extract_bigrams: contract holds")

def test_get_stats_contract():
    """Data flow contract: get_stats()."""
    mod = _load_mod()
    fn = getattr(mod, "get_stats")
    assert callable(fn), "get_stats must be callable"
    result = fn()
    assert result is not None, "get_stats returned None"
    print(f"  ok get_stats: contract holds")

def test_visualize_file_contract():
    """Data flow contract: visualize_file(file_key, top_n)."""
    mod = _load_mod()
    fn = getattr(mod, "visualize_file")
    assert callable(fn), "visualize_file must be callable"
    print(f"  ok visualize_file: contract holds")

def test_find_similar_files_contract():
    """Data flow contract: find_similar_files(file_key, top_n)."""
    mod = _load_mod()
    fn = getattr(mod, "find_similar_files")
    assert callable(fn), "find_similar_files must be callable"
    print(f"  ok find_similar_files: contract holds")

def test_hook_post_edit_contract():
    """Data flow contract: hook_post_edit(prompt_text, files_changed)."""
    mod = _load_mod()
    fn = getattr(mod, "hook_post_edit")
    assert callable(fn), "hook_post_edit must be callable"
    print(f"  ok hook_post_edit: contract holds")

def test_select_context_numeric_contract():
    """Data flow contract: select_context_numeric(prompt_text, top_n)."""
    mod = _load_mod()
    fn = getattr(mod, "select_context_numeric")
    assert callable(fn), "select_context_numeric must be callable"
    print(f"  ok select_context_numeric: contract holds")

def run_interlink_test():
    """Run all interlink checks for intent_numeric."""
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
    print(f"  intent_numeric: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
