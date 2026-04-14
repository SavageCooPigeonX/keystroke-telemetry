"""codebase_detector_pigeon_state_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 51 lines | ~553 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

def _pigeon_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    reg_path = profile.structured_files.get('pigeon_registry')
    if reg_path:
        try:
            data = json.loads(reg_path.read_text('utf-8', errors='ignore'))
            files = data.get('files', [])
            by_ver = sorted(files, key=lambda f: f.get('ver', 0), reverse=True)[:10]
            active = ', '.join(f"{f['name']}(v{f['ver']})" for f in by_ver)
            parts.append(f'Most active: {active}')
            intents = {}
            for f in files:
                ic = f.get('intent_code', 'OT')
                intents[ic] = intents.get(ic, 0) + 1
            top = sorted(intents.items(), key=lambda x: -x[1])[:5]
            parts.append(f'Intent spread: {", ".join(f"{k}={v}" for k,v in top)}')
        except Exception:
            pass
    heat_path = profile.structured_files.get('file_heat_map')
    if heat_path:
        try:
            heat = json.loads(heat_path.read_text('utf-8', errors='ignore'))
            hot = []
            for mod, d in heat.items():
                samples = d.get('samples', [])
                if samples:
                    avg = sum(s.get('hes', 0) for s in samples) / len(samples)
                    if avg > 0.5:
                        hot.append((mod, avg))
            hot.sort(key=lambda x: -x[1])
            if hot:
                parts.append(f'High cognitive load: {", ".join(f"{m}({h:.2f})" for m,h in hot[:5])}')
        except Exception:
            pass
    prof_path = profile.structured_files.get('file_profiles')
    if prof_path:
        try:
            profiles = json.loads(prof_path.read_text('utf-8', errors='ignore'))
            fears = {}
            for mod, p in profiles.items():
                for fear in p.get('fears', []):
                    fears[fear] = fears.get(fear, 0) + 1
            top_fears = sorted(fears.items(), key=lambda x: -x[1])[:5]
            if top_fears:
                parts.append(f'Common fears: {", ".join(f"{f}({c})" for f,c in top_fears)}')
        except Exception:
            pass
    return parts
