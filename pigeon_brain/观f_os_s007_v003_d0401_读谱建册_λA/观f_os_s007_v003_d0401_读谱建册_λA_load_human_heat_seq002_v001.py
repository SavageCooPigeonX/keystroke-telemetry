"""观f_os_s007_v003_d0401_读谱建册_λA_load_human_heat_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 21 lines | ~188 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_human_heat(root: Path) -> dict:
    """Load the human file_heat_map for dual-substrate comparison."""
    heat_path = root / "file_heat_map.json"
    if not heat_path.exists():
        return {}
    try:
        import importlib.util as ilu
        import glob
        matches = sorted(glob.glob(str(root / "src" / "热p_fhm_s011*.py")))
        if not matches:
            return {}
        spec = ilu.spec_from_file_location("_fhm", matches[-1])
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.load_heat_map(root)
    except Exception:
        return {}
