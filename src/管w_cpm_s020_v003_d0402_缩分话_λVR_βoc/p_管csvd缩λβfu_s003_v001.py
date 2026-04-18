"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_file_utils_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _latest_runtime_module(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _run_refresher(root: Path, relative_path: str | None, function_name: str) -> bool:
    try:
        import importlib.util

        if relative_path is None:
            return False
        mod_path = root / relative_path
        if not mod_path.exists():
            latest = _latest_runtime_module(root, relative_path)
            if latest is None:
                return False
            mod_path = latest
        spec = importlib.util.spec_from_file_location(f'_prompt_refresh_{function_name}', mod_path)
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, function_name, None)
        if not callable(func):
            return False
        return bool(func(root))
    except Exception:
        return False
