"""录p_lo_s003_v005_d0322_译改名踪_λω_load_src_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 14 lines | ~158 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _load_src(pattern: str, *symbols):
    """Dynamic pigeon import — finds latest src/ file matching glob."""
    import importlib.util as _ilu, glob as _g
    matches = sorted(_g.glob(f'src/{pattern}'))
    if not matches:
        raise ImportError(f'No src/ file matches {pattern!r}')
    spec = _ilu.spec_from_file_location('_dyn', matches[-1])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0])
    return tuple(getattr(mod, s) for s in symbols)
