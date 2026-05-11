"""Pigeon compliance facade for src/thought_completer.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if __name__ == "__main__" and "--opus-runtime" in sys.argv:
    import json
    idx = sys.argv.index("--opus-runtime")
    prompt = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else ""
    from src.opus_orchestrator_runtime_seq001_v001 import build_opus_orchestrator_runtime
    print(json.dumps(build_opus_orchestrator_runtime(_ROOT, prompt), indent=2))
    raise SystemExit(0)

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(__name__, globals(), 'src/thought_completer.py')

if __name__ == "__main__":
    _entry = globals().get("main") or globals().get("_main")
    raise SystemExit(_entry() if callable(_entry) else 0)
