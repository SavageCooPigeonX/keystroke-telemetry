"""u_pj_s019_v002_d0402_λC_candidate_compositions_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

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
