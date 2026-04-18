"""learning_loop_seq013/ — Pigeon-compliant module."""
import importlib, re
from pathlib import Path as _P

def _r(glyph_code, *attrs):
    """Resolve pigeon-named files by glyph code (e.g., 'cu' for catch_up)."""
    d = _P(__file__).parent
    # Pattern: 学f_ll_{glyph}_s{seq}_v{ver}*.py
    pat = re.compile(rf"^学f_ll_{re.escape(glyph_code)}_s\d+_v\d+.*\.py$", re.I)
    candidates = [f for f in d.iterdir() if f.suffix == ".py" and f.stem != "__init__" and pat.match(f.name)]
    if not candidates:
        raise ImportError(f"No module matching glyph {glyph_code}")
    # Pick latest version
    best = sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    m = importlib.import_module(f".{best.stem}", __package__)
    return tuple(getattr(m, a) for a in attrs) if len(attrs) > 1 else getattr(m, attrs[0])

# Glyph mappings: cu=catch_up, ml=main_loop, pc=prediction_cycle, sc=single_cycle, su=state_utils, jl=journal_loader
catch_up = _r("cu", "catch_up")
run_loop = _r("ml", "run_loop")
MAX_ENTRIES_PER_WAKE = _r("ml", "MAX_ENTRIES_PER_WAKE")
POLL_INTERVAL = _r("ml", "POLL_INTERVAL")
PREDICT_EVERY = _r("ml", "PREDICT_EVERY")
run_prediction_cycle = _r("pc", "run_prediction_cycle")
run_single_cycle = _r("sc", "run_single_cycle")
LOOP_STATE_FILE = _r("su", "LOOP_STATE_FILE")

# Also re-export private helpers for gemini_chat_seq001_v001 + submodule lazy imports
_load_state = _r("su", "_load_state")
_save_state = _r("su", "_save_state")
_load_journal_entries = _r("jl", "_load_journal_entries")
