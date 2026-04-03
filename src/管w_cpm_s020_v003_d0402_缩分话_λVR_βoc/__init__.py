"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc/ — Pigeon-compliant module.

Decomposed shards have broken cross-imports (missing COPILOT_PATH etc).
Route everything through the monolith via importlib until shards are fixed.
"""
import importlib.util
import sys
from pathlib import Path

_MONOLITH = Path(__file__).parent.parent / '管w_cpm_s020_v003_d0402_缩分话_λVR_βoc.py'
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
