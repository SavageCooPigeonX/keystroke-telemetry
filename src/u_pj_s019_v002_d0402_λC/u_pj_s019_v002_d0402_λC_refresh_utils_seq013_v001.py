"""u_pj_s019_v002_d0402_λC_refresh_utils_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _refresh_prompt_compositions(root: Path) -> None:
    try:
        import importlib.util

        prompt_recon_path = root / 'src' / 'prompt_recon_seq016_v001.py'
        if not prompt_recon_path.exists():
            return

        spec = importlib.util.spec_from_file_location('_prompt_recon_runtime', prompt_recon_path)
        if spec is None or spec.loader is None:
            return

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        reconstruct_latest = getattr(mod, 'reconstruct_latest', None)
        if callable(reconstruct_latest):
            reconstruct_latest(root)
    except Exception:
        return


def _force_fresh_composition(root: Path) -> None:
    """Force a fresh composition analysis from raw keystrokes before binding.

    This ensures the CURRENT prompt's deleted words are available for binding,
    rather than waiting for the classify_bridge flush timer (~60s).
    """
    try:
        import importlib.util
        analyzer_path = root / 'client' / 'chat_composition_analyzer.py'
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
