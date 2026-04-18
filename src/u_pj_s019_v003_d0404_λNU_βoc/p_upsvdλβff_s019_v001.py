"""u_pj_s019_v003_d0404_λNU_βoc_force_fresh_seq019_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | 25 lines | ~241 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _force_fresh_composition(root: Path) -> None:
    """Force a fresh composition analysis from raw keystrokes before binding.

    This ensures the CURRENT prompt's deleted words are available for binding,
    rather than waiting for the classify_bridge flush timer (~60s).
    """
    try:
        import importlib.util
        analyzer_path = root / 'client' / 'chat_composition_analyzer_seq001_v001.py'
        if not analyzer_path.exists():
            return
        spec = importlib.util.spec_from_file_location('_comp_analyzer', analyzer_path)
        if spec is None or spec.loader is None:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, 'analyze_and_log', None)
        if callable(fn):
            fn(root)
    except Exception:
        pass
