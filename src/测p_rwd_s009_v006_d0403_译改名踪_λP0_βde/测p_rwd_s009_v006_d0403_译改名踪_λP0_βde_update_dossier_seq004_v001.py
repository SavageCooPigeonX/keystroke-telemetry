"""测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_update_dossier_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 33 lines | ~346 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _update_dossier_scores(root: Path, verdict: str):
    """Feed rework verdict back into registry dossier_score for active bug entries."""
    dossier_path = root / 'logs' / 'active_dossier.json'
    if not dossier_path.exists(): return
    try:
        d = json.loads(dossier_path.read_text('utf-8'))
    except Exception: return
    focus = d.get('focus_modules', [])
    if not focus or d.get('confidence', 0) < 0.3: return
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists(): return
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception: return
    files = reg if isinstance(reg, list) else reg.get('files', [])
    # Reward signal: ok → +0.05, partial → -0.02, miss → -0.1
    delta = {'ok': 0.05, 'partial': -0.02, 'miss': -0.1}.get(verdict, 0)
    if delta == 0: return
    changed = False
    for f in files:
        name = f.get('file', '') or f.get('desc', '')
        if name in focus:
            old = f.get('dossier_score', 0)
            f['dossier_score'] = round(max(-1.0, min(1.0, old + delta)), 3)
            changed = True
    if changed:
        try:
            reg_path.write_text(json.dumps(reg, indent=2, default=str), 'utf-8')
        except Exception: pass
