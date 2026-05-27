"""file_selector_seq001_v001.py — intent-driven file selection from heat map + coupling + recency.

Predicts which FILES the operator needs next based on:
  - Buffer fragment keyword matching against registry
  - Heat map (high hesitation = struggling = relevant)
  - Coupling scores (mention one module → pre-load its partners)
  - Recency (recently edited/mentioned files rank higher)
  - Intent simulation (predicted focus areas get a boost)

Zero LLM calls. Pure signal processing. Returns ranked file list
with scores and reasons for LLM A to feed into LLM B.

Usage:
    from src.file_selector_seq001_v001 import select_files
    ranked = select_files("the drift watcher should prob", context)
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── caches ───────────────────────────────────────────────────────────────────

_registry_cache: list[dict] = []
_registry_ts: float = 0
_profiles_cache: dict = {}
_profiles_ts: float = 0
_heat_cache: dict = {}
_heat_ts: float = 0

STOP_WORDS = frozenset({
    'this', 'that', 'with', 'from', 'have', 'what', 'when', 'where', 'then',
    'than', 'they', 'their', 'will', 'would', 'could', 'should', 'about',
    'been', 'into', 'some', 'also', 'just', 'like', 'more', 'need', 'want',
    'make', 'does', 'dont', 'here', 'were', 'each', 'which', 'prob', 'probably',
    'maybe', 'think', 'know', 'look', 'file', 'code', 'thing', 'stuff',
})


def _load_registry() -> list[dict]:
    global _registry_cache, _registry_ts
    now = time.time()
    if _registry_cache and (now - _registry_ts) < 300:
        return _registry_cache
    reg = ROOT / 'pigeon_registry.json'
    if not reg.exists():
        return []
    try:
        data = json.loads(reg.read_text('utf-8', errors='ignore'))
        _registry_cache = data.get('files', [])
        _registry_ts = now
    except Exception:
        pass
    return _registry_cache


def _load_profiles() -> dict:
    global _profiles_cache, _profiles_ts
    now = time.time()
    if _profiles_cache and (now - _profiles_ts) < 300:
        return _profiles_cache
    fp = ROOT / 'file_profiles.json'
    if not fp.exists():
        return {}
    try:
        _profiles_cache = json.loads(fp.read_text('utf-8', errors='ignore'))
        _profiles_ts = now
    except Exception:
        pass
    return _profiles_cache


def _load_heat_map() -> dict:
    global _heat_cache, _heat_ts
    now = time.time()
    if _heat_cache and (now - _heat_ts) < 120:
        return _heat_cache
    fh = ROOT / 'file_heat_map.json'
    if not fh.exists():
        return {}
    try:
        _heat_cache = json.loads(fh.read_text('utf-8', errors='ignore'))
        _heat_ts = now
    except Exception:
        pass
    return _heat_cache


def _extract_keywords(fragment: str) -> list[str]:
    """Extract meaningful keywords from a typing fragment."""
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', fragment.lower())
    keywords = [w for w in words if len(w) > 2 and w not in STOP_WORDS]
    # also catch underscore_joined terms
    compounds = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', fragment.lower())
    keywords.extend(compounds)
    return list(set(keywords))


def _get_recent_files(ctx: dict) -> list[str]:
    """Extract recently mentioned/edited file names from context."""
    recent = set()
    for p in ctx.get('recent_prompts', []):
        msg = p.get('msg', '').lower()
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)*', msg)
        recent.update(words)
    for m in ctx.get('hot_modules', []):
        recent.add(m.get('module', '').lower())
    return list(recent)


def _score_file(mod: dict, keywords: list[str], profiles: dict,
                heat_map: dict, recent: list[str],
                hot_modules: list[str]) -> tuple[float, list[str]]:
    """Score a module's relevance. Returns (score, reasons)."""
    name = mod.get('name', '').lower()
    desc = mod.get('desc', '').lower()
    path = mod.get('path', '').lower()
    score = 0.0
    reasons = []

    # 1. DIRECT NAME MATCH — strongest signal
    for kw in keywords:
        if kw == name:
            score += 5.0
            reasons.append(f'exact_name:{kw}')
        elif kw in name:
            score += 3.0
            reasons.append(f'name_contains:{kw}')
        elif kw in desc:
            score += 1.5
            reasons.append(f'desc_match:{kw}')
        elif kw in path:
            score += 1.0
            reasons.append(f'path_match:{kw}')

    # 2. HEAT MAP — high hesitation = operator struggles here = relevant
    heat_entry = heat_map.get(name, {})
    samples = heat_entry.get('samples', [])
    if samples:
        avg_hes = sum(s.get('hes', 0) for s in samples) / len(samples)
        if avg_hes > 0.5:
            score += 2.5
            reasons.append(f'high_heat:{avg_hes:.2f}')
        elif avg_hes > 0.3:
            score += 1.5
            reasons.append(f'med_heat:{avg_hes:.2f}')

    # 3. COUPLING — if ANY keyword matches a partner, boost this module
    profile = profiles.get(name, {})
    partners = profile.get('partners', [])
    for partner in partners:
        pname = partner.get('name', '').lower()
        pscore = partner.get('score', 0)
        for kw in keywords:
            if kw in pname or pname in kw:
                coupling_boost = pscore * 3.0
                score += coupling_boost
                reasons.append(f'coupled:{pname}({pscore:.2f})')
                break

    # 4. RECENCY — recently mentioned modules rank higher
    if name in recent:
        score += 2.0
        reasons.append('recent')

    # 5. HOT MODULE bonus — from telemetry
    if name in hot_modules:
        score += 2.0
        reasons.append('hot_module')

    # 6. VERSION/CHURN signal — high-version modules are actively worked on
    ver = mod.get('ver', 1)
    if ver >= 5:
        score += 0.5
        reasons.append(f'high_churn:v{ver}')

    return score, reasons


def select_files(fragment: str, ctx: dict, max_files: int = 4) -> list[dict]:
    """Select the most relevant files for a typing fragment.

    Args:
        fragment: what the operator has typed so far
        ctx: context dict with recent_prompts, hot_modules, etc.
        max_files: how many files to return

    Returns:
        List of {name, path, score, reasons, tokens, personality} dicts,
        sorted by score descending.
    """
    registry = _load_registry()
    if not registry:
        return []

    profiles = _load_profiles()
    heat_map = _load_heat_map()
    keywords = _extract_keywords(fragment)
    if not keywords:
        return []

    recent = _get_recent_files(ctx)
    hot_modules = [m.get('module', '').lower() for m in ctx.get('hot_modules', [])]

    scored = []
    seen_names = set()
    for mod in registry:
        name = mod.get('name', '').lower()
        if name in seen_names:
            continue
        seen_names.add(name)

        s, reasons = _score_file(mod, keywords, profiles, heat_map,
                                 recent, hot_modules)
        if s > 0:
            profile = profiles.get(name, {})
            scored.append({
                'name': mod.get('name', ''),
                'path': mod.get('path', ''),
                'score': round(s, 2),
                'reasons': reasons,
                'tokens': mod.get('tokens', 0),
                'personality': profile.get('personality', 'unknown'),
                'fears': profile.get('fears', [])[:3],
                'avg_hes': profile.get('avg_hes', 0),
            })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:max_files]


def select_partners(primary_module: str, max_partners: int = 3) -> list[dict]:
    """Given a primary module name, return its highest-coupling partners."""
    profiles = _load_profiles()
    profile = profiles.get(primary_module.lower(), {})
    partners = profile.get('partners', [])
    partners.sort(key=lambda p: p.get('score', 0), reverse=True)
    return partners[:max_partners]
