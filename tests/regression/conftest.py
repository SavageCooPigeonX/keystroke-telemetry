"""Compatibility path for legacy sibling imports in moved root tests."""

from pathlib import Path
import sys


REGRESSION_DIR = Path(__file__).resolve().parent
if str(REGRESSION_DIR) not in sys.path:
    sys.path.insert(0, str(REGRESSION_DIR))
