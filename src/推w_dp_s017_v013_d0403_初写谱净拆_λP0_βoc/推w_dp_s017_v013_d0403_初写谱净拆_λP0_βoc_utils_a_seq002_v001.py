"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_utils_a_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 50 lines | ~361 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json, re, subprocess

def _parse_ts(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def _normalize_signal_phrase(value):
    text = re.sub(r'\s+', ' ', str(value)).strip().strip('"\'.,;:!?-')
    if len(text) < 4:
        return None
    alnum = sum(ch.isalnum() for ch in text)
    if alnum < 3 or alnum / max(len(text), 1) < 0.6:
        return None
    if not any(ch.isalpha() for ch in text):
        return None
    return text


def _signal_words(values):
    words = []
    seen = set()
    for value in values:
        word = value.get('word', value) if isinstance(value, dict) else value
        clean = _normalize_signal_phrase(word)
        if clean and clean not in seen:
            words.append(clean)
            seen.add(clean)
    return words


def _jsonl(path, n=0):
    if not path.exists(): return []
    ll = path.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
    if n: ll = ll[-n:]
    out = []
    for l in ll:
        try: out.append(json.loads(l))
        except Exception: pass
    return out


def _json(path):
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception: return None
