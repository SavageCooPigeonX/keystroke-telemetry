"""漂p_dw_s005_v004_d0321_踪稿析_λ18_context_budget_loader_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 12 lines | ~133 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import glob as _glob
import importlib.util

def _load_context_budget():
    matches = sorted(_glob.glob('src/境w_cb_s004*.py'))
    if not matches:
        raise ImportError('No src/context_budget_seq004*.py found')
    spec = importlib.util.spec_from_file_location('_cb', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.score_context_budget, mod.estimate_tokens
