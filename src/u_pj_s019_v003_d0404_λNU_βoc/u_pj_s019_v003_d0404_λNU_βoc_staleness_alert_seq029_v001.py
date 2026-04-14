"""u_pj_s019_v003_d0404_λNU_βoc_staleness_alert_seq029_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 029 | VER: v001 | 15 lines | ~171 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _log_enriched_entry_run_staleness_alert(root: Path) -> None:
    try:
        import importlib.util as _sa_ilu
        _sa_matches = sorted(root.glob('src/警p_sa_s030*.py'))
        if _sa_matches:
            _sa_spec = _sa_ilu.spec_from_file_location('_staleness', _sa_matches[-1])
            if _sa_spec is not None and _sa_spec.loader is not None:
                _sa_mod = _sa_ilu.module_from_spec(_sa_spec)
                _sa_spec.loader.exec_module(_sa_mod)
                _sa_mod.inject_staleness_alert(root)
    except Exception:
        pass
