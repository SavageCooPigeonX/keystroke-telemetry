"""codebase_detector_seq001_v001_python_state_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 15 lines | ~141 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _python_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    pp = profile.structured_files.get('pyproject')
    if pp:
        try:
            text = pp.read_text('utf-8', errors='ignore')
            for line in text.split('\n'):
                if line.strip().startswith('name'):
                    parts.append(f'Name: {line.split("=")[-1].strip().strip(chr(34))}')
                    break
        except Exception:
            pass
    return parts
