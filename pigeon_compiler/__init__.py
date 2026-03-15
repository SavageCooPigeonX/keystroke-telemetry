"""pigeon_compiler — Self-Documenting Codebase Engine.

Filenames mutate on every commit to carry intent, description,
version, and token metadata.  The filename IS the changelog.

  noise_filter_seq007_v004_d0316__filter_live_noise_lc_fixed_timeout.py
  ├─ filter_live_noise     = what the file DOES  (from docstring)
  └─ fixed_timeout         = what was LAST DONE  (from commit message)

Components:
  - git_plugin       — Post-commit hook: auto-rename + prompt box + session log
  - session_logger   — Per-file JSONL mutation audit trail
  - pre_commit_audit — Advisory compliance checking (never blocks)
  - rename_engine    — Registry, import rewriter, manifest builder
  - cli              — `pigeon init/status/heal/sessions/uninstall`
  - state_extractor  — AST analysis, produces Ether Map JSON
  - cut_executor     — Deterministic file splitting + import fixing
"""

__version__ = "1.0.0"
__author__ = "SavageCooPigeonX"

from pigeon_compiler.state_extractor import build_ether_map

__all__ = ["build_ether_map"]
