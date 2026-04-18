"""engagement_hooks_seq001_v001/ — Pigeon-compliant module.

Re-exports the public API from the monolith sibling file. The package shadows
the .py file at import time; this init restores callers' access to the public
functions without forcing a migration of every call site.
"""
import importlib.util as _ilu
from pathlib import Path as _Path

_mono = _Path(__file__).resolve().parent.parent / "engagement_hooks_seq001_v001.py"
if _mono.exists():
    _spec = _ilu.spec_from_file_location("_engagement_hooks_seq001_v001_mono", _mono)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    generate_hooks = _mod.generate_hooks
    build_hooks_block = _mod.build_hooks_block
    inject_hooks = _mod.inject_hooks

__all__ = ["generate_hooks", "build_hooks_block", "inject_hooks"]
