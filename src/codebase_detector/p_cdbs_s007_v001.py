"""codebase_detector_seq001_v001_build_state_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 9 lines | ~118 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _build_state_text(profile: CodebaseProfile) -> str:
    parts = [f'Project: {profile.name} ({profile.kind}, {profile.modules} modules, naming={profile.naming_pattern})']
    builders = {'pigeon': _pigeon_state, 'python': _python_state, 'node': _node_state}
    builder = builders.get(profile.kind)
    if builder:
        parts.extend(builder(profile))
    return '\n'.join(parts)
