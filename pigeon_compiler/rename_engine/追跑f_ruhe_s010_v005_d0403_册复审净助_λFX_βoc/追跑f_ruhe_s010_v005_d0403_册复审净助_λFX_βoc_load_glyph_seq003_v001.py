"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_load_glyph_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json

def _load_glyph_context(root: Path) -> tuple[dict, dict, dict]:
    """Load glyph map, confidence map, and partner data for glyph drift detection."""
    import json as _json
    glyph_map: dict[str, str] = {}
    confidence_map: dict[str, str] = {}
    partners: dict[str, list[dict]] = {}
    try:
        from src.典w_sd_s031_v002_d0401_缩分话_λG import (
            _MNEMONIC_MAP,
        )
        glyph_map = dict(_MNEMONIC_MAP)
    except Exception:
        pass
    try:
        from src.u_cs_s033_v001 import score_module_confidence
        confidence_map = score_module_confidence(root)
    except Exception:
        pass
    try:
        fp = root / 'file_profiles.json'
        if fp.exists():
            profiles = _json.loads(fp.read_text('utf-8'))
            for mod, data in profiles.items():
                p = data.get('partners', [])
                if p:
                    partners[mod] = p
    except Exception:
        pass
    return glyph_map, confidence_map, partners
