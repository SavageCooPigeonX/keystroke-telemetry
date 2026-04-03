"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_mutate_compressed_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def mutate_compressed_stem(stem: str, new_ver: int | None = None,
                           new_date: str | None = None,
                           new_state: str | None = None,
                           new_intent: str | None = None,
                           new_bugs: str | None = None) -> str | None:
    """Mutate a compressed filename stem in-place, updating specified fields.

    Returns the new filename (with .py) or None if stem doesn't parse.

    mutate_compressed_stem('改名f_rr_s006_v005_d0401_追跑拆谱建_λFX_βochi',
                           new_ver=6, new_date='0402', new_intent='FX', new_bugs='oc')
    → '改名f_rr_s006_v006_d0402_追跑拆谱建_λFX_βoc.py'
    """
    parsed = parse_pigeon_stem(stem)
    if not parsed or not parsed.get('compressed'):
        return None
    return build_compressed_filename(
        glyph=parsed['glyph'],
        state=new_state or parsed['state'],
        abbrev=parsed['abbrev'],
        seq=parsed['seq'],
        ver=new_ver if new_ver is not None else parsed['ver'],
        date=new_date or parsed['date'],
        deps=parsed.get('deps', ''),
        intent=new_intent or parsed.get('intent', ''),
        bugs=parsed.get('bugs', '') if new_bugs is None else new_bugs,
    )
