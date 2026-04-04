"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc/ — Pigeon-compliant module.

Decomposed shards have broken cross-imports (missing COPILOT_PATH etc).
Route everything through the monolith via importlib until shards are fixed.
Monolith filename mutates on every commit — resolve via glob.
"""
import importlib.util
import sys
from pathlib import Path

_parent = Path(__file__).parent.parent
# Find monolith by glob — pigeon renames it every commit
_candidates = sorted(_parent.glob('管w_cpm_s020*.py'), key=lambda p: p.stat().st_mtime, reverse=True)
if not _candidates:
    raise ImportError('Cannot find 管w_cpm monolith .py file in src/')
_MONOLITH = _candidates[0]
_spec = importlib.util.spec_from_file_location(
    'src._管w_cpm_monolith', str(_MONOLITH))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export everything the monolith provides
refresh_managed_prompt = _mod.refresh_managed_prompt
audit_copilot_prompt = _mod.audit_copilot_prompt
inject_auto_index = _mod.inject_auto_index
inject_bug_voices = _mod.inject_bug_voices
inject_operator_state = _mod.inject_operator_state
inject_prompt_telemetry = _mod.inject_prompt_telemetry
COPILOT_PATH = _mod.COPILOT_PATH
BLOCK_MARKERS = _mod.BLOCK_MARKERS
