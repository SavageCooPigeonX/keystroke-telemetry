"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 33 lines | ~301 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _module_key(raw_file: str) -> str:
    stem = Path(raw_file).stem
    mod = re.split(r'_s(?:eq)?\d{3}', stem)[0]
    return mod or stem


def _region_from_path(raw_file: str) -> str:
    folder = str(Path(raw_file).parent).replace('\\', '/')
    if folder.startswith('src/cognitive_reactor'):
        return 'motor'
    if folder.startswith('src/copilot_prompt_manager'):
        return 'language'
    if folder.startswith('src/cognitive'):
        return 'consciousness'
    if folder.startswith('src'):
        return 'cortex'
    if folder.startswith('pigeon_brain'):
        return 'stem'
    if folder.startswith('pigeon_compiler/rename_engine'):
        return 'naming'
    if folder.startswith('pigeon_compiler/cut_executor'):
        return 'spatial'
    if folder.startswith('pigeon_compiler/state_extractor') or folder.startswith('pigeon_compiler/bones'):
        return 'analysis'
    if folder.startswith('pigeon_compiler/runners'):
        return 'coordination'
    if folder.startswith('streaming_layer'):
        return 'transport'
    return 'cortex'
