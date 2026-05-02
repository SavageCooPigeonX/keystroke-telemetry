"""Pigeon compliance facade for src/管w_cpm_s020_v005_d0404_缩分话_λNU_βoc.py."""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(__name__, globals(), 'src/管w_cpm_s020_v005_d0404_缩分话_λNU_βoc.py')

if __name__ == "__main__":
    _entry = globals().get("main") or globals().get("_main")
    raise SystemExit(_entry() if callable(_entry) else 0)
