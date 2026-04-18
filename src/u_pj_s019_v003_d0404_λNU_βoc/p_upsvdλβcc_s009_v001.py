"""u_pj_s019_v003_d0404_λNU_βoc_candidate_comps_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 32 lines | ~304 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_u_pj_s001_v001 import COMPS_PATH, PROMPT_COMPS_PATH
from .p_u_pj_s002_v001 import _parse_timestamp_ms, _read_jsonl
from .p_upsvdλβck_s004_v001 import _composition_key
from .p_upsvdλβtm_s003_v001 import _text_match_score

def _candidate_compositions(root: Path, now_ms: int, msg: str) -> list[dict]:
    candidates = []
    sources = [
        ('prompt_compositions', root / PROMPT_COMPS_PATH),
        ('chat_compositions', root / COMPS_PATH),
    ]
    for source, path in sources:
        for entry in _read_jsonl(path):
            comp_ts = (
                _parse_timestamp_ms(entry.get('last_key_ts'))
                or _parse_timestamp_ms(entry.get('first_key_ts'))
                or _parse_timestamp_ms(entry.get('ts'))
            )
            if comp_ts is None or comp_ts > now_ms:
                continue
            candidates.append({
                'source': source,
                'entry': entry,
                'ts_ms': comp_ts,
                'age_ms': now_ms - comp_ts,
                'key': _composition_key(entry),
                'match_score': _text_match_score(msg, entry),
            })
    candidates.sort(
        key=lambda item: (-item['match_score'], item['age_ms'], 0 if item['source'] == 'prompt_compositions' else 1)
    )
    return candidates
