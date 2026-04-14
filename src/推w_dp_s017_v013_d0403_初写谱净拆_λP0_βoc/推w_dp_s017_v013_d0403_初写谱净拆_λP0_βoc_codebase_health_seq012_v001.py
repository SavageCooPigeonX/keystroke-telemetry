"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_codebase_health_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 38 lines | ~418 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _codebase_health(root):
    """Load context_veins.json and build a Codebase Health section for CoT injection."""
    vp = root / 'pigeon_brain' / 'context_veins.json'
    if not vp.exists():
        return ''
    try:
        data = json.loads(vp.read_text('utf-8'))
    except Exception:
        return ''
    stats = data.get('stats', {})
    clots = data.get('clots', [])
    recs = data.get('trim_recommendations', [])
    arteries = data.get('arteries', [])
    if not clots and not recs:
        return ''
    lines = ['### Codebase Health (Veins / Clots)',
             f'*{stats.get("alive", 0)}/{stats.get("total_nodes", 0)} alive, '
             f'{stats.get("clots", 0)} clots, '
             f'avg vein health {stats.get("avg_vein_health", 0):.2f}*']
    if clots:
        lines.append('\n**Clots (dead/bloated — trim candidates):**')
        for c in clots[:6]:
            sigs = ', '.join(c.get('clot_signals', []))
            lines.append(f'- `{c["module"]}` (score={c["clot_score"]:.2f}): {sigs}')
    if recs:
        lines.append('\n**Self-trim recommendations:**')
        for r in recs[:4]:
            lines.append(f'- [{r["action"]}] `{r["target"]}`: {r["reason"]}')
    if arteries:
        top_art = [a for a in arteries[:3] if a.get('vein_score', 0) >= 0.8]
        if top_art:
            lines.append('\n**Critical arteries (do NOT break):**')
            for a in top_art:
                lines.append(f'- `{a["module"]}` (vein={a["vein_score"]:.2f}, in={a["in_degree"]})')
    return '\n'.join(lines)
