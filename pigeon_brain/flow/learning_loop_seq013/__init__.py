"""learning_loop_seq013/ — Pigeon-compliant module."""
import importlib, re
from pathlib import Path as _P

def _r(prefix, *attrs):
    d = _P(__file__).parent
    pat = re.compile(rf"^{re.escape(prefix)}_v\d+", re.I)
    for f in d.iterdir():
        if f.suffix == ".py" and f.stem != "__init__" and pat.match(f.stem):
            m = importlib.import_module(f".{f.stem}", __package__)
            return tuple(getattr(m, a) for a in attrs) if len(attrs) > 1 else getattr(m, attrs[0])
    raise ImportError(f"No module matching {prefix}")

catch_up = _r("learning_loop_seq013_catch_up_seq006", "catch_up")
run_loop = _r("learning_loop_seq013_main_loop_seq008", "run_loop")
MAX_ENTRIES_PER_WAKE = _r("learning_loop_seq013_main_loop_seq008", "MAX_ENTRIES_PER_WAKE")
POLL_INTERVAL = _r("learning_loop_seq013_main_loop_seq008", "POLL_INTERVAL")
PREDICT_EVERY = _r("learning_loop_seq013_main_loop_seq008", "PREDICT_EVERY")
run_prediction_cycle = _r("learning_loop_seq013_prediction_cycle_seq003", "run_prediction_cycle")
run_single_cycle = _r("learning_loop_seq013_single_cycle_seq005", "run_single_cycle")
LOOP_STATE_FILE = _r("learning_loop_seq013_state_utils_seq001", "LOOP_STATE_FILE")

# Also re-export private helpers for gemini_chat + submodule lazy imports
_load_state = _r("learning_loop_seq013_state_utils_seq001", "_load_state")
_save_state = _r("learning_loop_seq013_state_utils_seq001", "_save_state")
_load_journal_entries = _r("learning_loop_seq013_journal_loader_seq002", "_load_journal_entries")
