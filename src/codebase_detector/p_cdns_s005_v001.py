"""codebase_detector_seq001_v001_node_state_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 16 lines | ~146 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

def _node_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    pkg = profile.structured_files.get('package_json')
    if pkg:
        try:
            data = json.loads(pkg.read_text('utf-8', errors='ignore'))
            parts.append(f'Name: {data.get("name", "?")}')
            deps = list(data.get('dependencies', {}).keys())[:10]
            if deps:
                parts.append(f'Deps: {", ".join(deps)}')
        except Exception:
            pass
    return parts
