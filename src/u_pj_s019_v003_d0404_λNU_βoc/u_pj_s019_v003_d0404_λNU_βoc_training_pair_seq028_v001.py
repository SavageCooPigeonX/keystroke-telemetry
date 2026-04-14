"""u_pj_s019_v003_d0404_λNU_βoc_training_pair_seq028_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 028 | VER: v001 | 21 lines | ~220 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _log_enriched_entry_write_training_pair(root: Path, msg: str) -> None:
    try:
        import importlib.util as _tw_ilu
        _tw_matches = sorted(root.glob('src/训w_trwr_s028*.py'))
        if _tw_matches:
            _tw_spec = _tw_ilu.spec_from_file_location('_tw', _tw_matches[-1])
            if _tw_spec is not None and _tw_spec.loader is not None:
                _tw_mod = _tw_ilu.module_from_spec(_tw_spec)
                _tw_spec.loader.exec_module(_tw_mod)
                _tw_mod.write_training_pair(
                    root,
                    prompt=msg[:500],
                    response='(pending — response not yet captured)',
                    verdict='pending',
                )
    except Exception:
        pass
