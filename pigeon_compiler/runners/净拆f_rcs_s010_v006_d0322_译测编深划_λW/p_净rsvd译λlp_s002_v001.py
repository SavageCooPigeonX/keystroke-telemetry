"""净拆f_rcs_s010_v006_d0322_译测编深划_λW_load_plan_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 11 lines | ~139 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, sys, argparse, shutil, traceback, importlib.util, glob as _glob

def _load_request_cut_plan():
    matches = sorted(PROJECT_ROOT.glob('weakness_planner/核w_dspp_s004*.py'))
    if not matches:
        raise ImportError('deepseek_plan_prompt_seq004 not found')
    spec = importlib.util.spec_from_file_location('_dsp', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.request_cut_plan
