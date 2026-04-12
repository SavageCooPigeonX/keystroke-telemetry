"""backward_seq007/ — Pigeon-compliant module."""
import importlib, re
from pathlib import Path as _P

def _r(glyph_code, *attrs):
    """Resolve pigeon-named files by glyph code (e.g., 'bp' for backward_pass)."""
    d = _P(__file__).parent
    # Pattern: 逆f_ba_{glyph}_s{seq}_v{ver}*.py
    pat = re.compile(rf"^逆f_ba_{re.escape(glyph_code)}_s\d+_v\d+.*\.py$", re.I)
    candidates = [f for f in d.iterdir() if f.suffix == ".py" and f.stem != "__init__" and pat.match(f.name)]
    if not candidates:
        raise ImportError(f"No module matching glyph {glyph_code}")
    # Pick latest version
    best = sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    m = importlib.import_module(f".{best.stem}", __package__)
    return tuple(getattr(m, a) for a in attrs) if len(attrs) > 1 else getattr(m, attrs[0])

# Glyph mappings: bp=backward_pass, fl=flow_log, lc=loss_compute, to=tokenize, da=deepseek_analyze
backward_pass = _r("bp", "backward_pass")
FLOW_LOG, log_forward_pass, _load_forward_path = _r("fl", "FLOW_LOG", "log_forward_pass", "_load_forward_path")
STATE_FRUSTRATION, compute_loss = _r("lc", "STATE_FRUSTRATION", "compute_loss")
_tokenize = _r("to", "_tokenize")
_deepseek_analyze_backward = _r("da", "_deepseek_analyze_backward")
