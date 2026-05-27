"""Pigeon compliance facade for test_training_pairs.py."""
from pathlib import Path
import shutil
import sys

import pytest

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(__name__, globals(), 'test_training_pairs.py')


@pytest.fixture
def n() -> int:
    return 10


@pytest.fixture
def count() -> int:
    return 5


@pytest.fixture
def sandbox(n: int):
    path = setup_sandbox(n)
    capture_training_pair(path)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

if __name__ == "__main__":
    _entry = globals().get("main") or globals().get("_main")
    raise SystemExit(_entry() if callable(_entry) else 0)
