"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_consciousness_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 78 lines | ~893 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _file_consciousness(root):
    """Load file consciousness report from cached profiles, including slumber party warnings."""
    try:
        fp = root / 'file_profiles.json'
        if not fp.exists(): return ''
        profiles = json.loads(fp.read_text('utf-8'))
        if not profiles: return ''
        drama = sorted(profiles.items(), key=lambda x: x[1].get('version', 0), reverse=True)[:4]
        feared = {}
        for _, p in profiles.items():
            for f in p.get('fears', []):
                feared[f] = feared.get(f, 0) + 1
        top_fears = sorted(feared.items(), key=lambda x: x[1], reverse=True)[:3]
        lines = ['### File Consciousness', f'*{len(profiles)} modules profiled*']
        if drama:
            lines.append('\n**High-drama (most mutations):**')
            for name, p in drama:
                partners = p.get('partners', [])
                top_p = f' \u2194 {partners[0]["name"]}' if partners else ''
                lines.append(f'- `{name}` v{p["version"]}{top_p}')
        if top_fears:
            lines.append('\n**Codebase fears:**')
            for fear, count in top_fears:
                lines.append(f'- {fear} ({count} modules)')
        # Slumber party: surface high-score coupling warnings
        hot_couples = []
        for name, p in profiles.items():
            for partner in p.get('partners', []):
                if partner.get('score', 0) >= 0.45:
                    hot_couples.append((name, partner['name'], partner['score'], partner.get('reason', '')))
        hot_couples.sort(key=lambda x: x[2], reverse=True)
        if hot_couples:
            lines.append('\n**Slumber party warnings (high coupling):**')
            for a, b, score, reason in hot_couples[:3]:
                lines.append(f'- `{a}` ↔ `{b}` (score={score:.2f}, {reason})')
        return '\n'.join(lines)
    except Exception:
        return ''


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
