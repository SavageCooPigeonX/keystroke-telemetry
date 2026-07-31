"""Compatibility facade for the registry identity bridge."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(
    __name__,
    globals(),
    "src/registry_identity_bridge_seq001_v002_d0605__seq_pairing_aliases_md_anchors_lc_patch_registry.py",
)
