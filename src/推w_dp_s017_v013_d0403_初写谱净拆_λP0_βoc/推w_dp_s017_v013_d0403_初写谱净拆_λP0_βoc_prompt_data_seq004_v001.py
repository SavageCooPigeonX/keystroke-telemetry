"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_prompt_data_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 66 lines | ~617 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _latest_prompt(root):
    snap = _json(root / 'logs' / 'prompt_telemetry_latest.json') or {}
    latest_prompt = snap.get('latest_prompt') or {}
    return latest_prompt, snap


def _latest_composition(root, comps):
    latest_prompt, _ = _latest_prompt(root)
    latest_prompt_ts = _parse_ts(latest_prompt.get('ts'))
    if latest_prompt_ts is None:
        return comps[-1] if comps else None
    for comp in reversed(comps):
        comp_ts = _parse_ts(comp.get('ts'))
        if comp_ts and abs((latest_prompt_ts - comp_ts).total_seconds()) <= 300:
            return comp
    return None


def _unsaid(root, comps):
    _, snap = _latest_prompt(root)
    if 'deleted_words' in snap:
        return _signal_words(snap.get('deleted_words') or [])[:6]
    comp = _latest_composition(root, comps)
    if not comp:
        return []
    primary = comp.get('intent_deleted_words') or comp.get('deleted_words') or []
    return _signal_words(primary)[:6]


def _unsaid_reconstructions(root, current_unsaid):
    """Load LLM-reconstructed intents from high-deletion prompts."""
    if not current_unsaid:
        return []
    latest_prompt, _ = _latest_prompt(root)
    latest_prompt_ts = _parse_ts(latest_prompt.get('ts'))
    target_words = {word.lower() for word in current_unsaid}
    recs = _jsonl(root / 'logs' / 'unsaid_reconstructions.jsonl', n=40)
    good = []
    seen = set()
    for r in reversed(recs):
        if r.get('trigger') == 'enricher':
            continue
        rec_ts = _parse_ts(r.get('ts'))
        if latest_prompt_ts and rec_ts and abs((latest_prompt_ts - rec_ts).total_seconds()) > 300:
            continue
        deleted_words = _signal_words(r.get('deleted_words', []))
        if not deleted_words:
            continue
        rec_words = {word.lower() for word in deleted_words}
        if rec_words.isdisjoint(target_words):
            continue
        tc = r.get('thought_completion', r.get('reconstructed_intent', ''))
        if not _is_novel_unsaid_reconstruction(tc):
            continue
        deleted = tuple(sorted(rec_words))
        key = (_normalize_unsaid_text(tc), deleted)
        if key in seen:
            continue
        seen.add(key)
        good.append({**r, 'deleted_words': deleted_words})
        if len(good) >= 3:
            break
    return list(reversed(good))
