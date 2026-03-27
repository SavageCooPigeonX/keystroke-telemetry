"""backward_seq007/ — Pigeon-compliant module."""
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

backward_pass = _r("backward_seq007_backward_pass_seq005", "backward_pass")
FLOW_LOG, log_forward_pass = _r("backward_seq007_flow_log_seq001", "FLOW_LOG", "log_forward_pass")
STATE_FRUSTRATION, compute_loss = _r("backward_seq007_loss_compute_seq002", "STATE_FRUSTRATION", "compute_loss")
