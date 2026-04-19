"""Dynamic import resolver for pigeon-named modules in src/.

Eliminates hardcoded version/date/description imports that break on every
pigeon rename. Import by seq identifier only — the resolver finds either
the legacy long filename or the compact renamed module at runtime.

Usage:
    from src._resolve import src_import
    TelemetryLogger = src_import("logger_seq003", "TelemetryLogger")
    mod = src_import("drift_watcher_seq005")  # returns module
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, Iterable

_SRC_DIR = Path(__file__).parent
_CACHE: dict[str, str] = {}
_LEGACY_SEQ_RE = re.compile(r'^(?P<base>.+?)_seq(?P<seq>\d{3})(?:$|_)', re.IGNORECASE)
_COMPACT_SEQ_RE = re.compile(r'(?:^|_)(?:seq|s)(?P<seq>\d{3})(?:$|_)', re.IGNORECASE)
_LEGACY_VERSION_RE = re.compile(r'_v\d+$', re.IGNORECASE)

_ABBREV_OVERRIDES = {
    'context_budget': 'cb',
    'context_router': 'cxr',
    'copilot_prompt_manager': 'cpm',
    'cognitive_reactor': 'cr',
    'drift_watcher': 'dw',
    'dynamic_prompt': 'dp',
    'file_consciousness': 'fc',
    'file_heat_map': 'fhm',
    'glyph_compiler': 'gc',
    'intent_simulator': 'is',
    'logger': 'lo',
    'models': 'mo',
    'operator_stats': 'ost',
    '.operator_stats': 'ops',
    'prompt_journal': 'pj',
    'prompt_recon': 'prc',
    'prompt_signal': 'psg',
    'push_narrative': 'pn',
    'query_memory': 'qm',
    'research_lab': 'rl',
    'resistance_bridge': 'rb',
    'rework_detector': 'rwd',
    'self_fix': 'sf',
    'session_handoff': 'sh',
    'shard_manager': 'sm',
    'task_queue': 'tq',
    'timestamp_utils': 'tu',
    'training_writer': 'trwr',
    'unified_signal': 'us',
    'voice_style': 'vs',
    'missing_context': 'mc',
}


def _iter_children(search_dir: Path) -> list[tuple[str, Path, bool]]:
    if not search_dir.is_dir():
        return []

    children: list[tuple[str, Path, bool]] = []
    for child in search_dir.iterdir():
        if child.name == '__pycache__':
            continue
        if child.is_dir():
            if child.name.isidentifier():
                children.append((child.name, child, True))
            continue
        if child.suffix == '.py' and child.stem != '__init__' and child.stem.isidentifier():
            children.append((child.stem, child, False))
    return children


def _split_legacy_seq(segment: str) -> tuple[str, str] | None:
    match = _LEGACY_SEQ_RE.match(segment)
    if not match:
        return None
    return match.group('base'), match.group('seq')


def _extract_seq_token(name: str) -> str | None:
    match = _COMPACT_SEQ_RE.search(name)
    if match:
        return match.group('seq')
    return None


def _abbrev_variants(base: str) -> set[str]:
    clean = re.sub(r'_seq\d{3}', '', base, flags=re.IGNORECASE).lstrip('.')
    words = [word for word in clean.split('_') if word]
    if not words:
        return set()

    variants: set[str] = set()
    override = _ABBREV_OVERRIDES.get(base) or _ABBREV_OVERRIDES.get(clean)
    if override:
        variants.add(override)

    initials = ''.join(word[0] for word in words)
    if len(initials) >= 2:
        variants.add(initials)
    if len(words) >= 2:
        variants.add(''.join(word[0] for word in words[:2]))
        variants.add(''.join(word[0] for word in words[-2:]))
        variants.add(words[0][0] + words[1][:2])
        variants.add(words[0][:2] + words[1][0])
    variants.add(words[0][:2])
    variants.add(words[-1][:2])

    return {variant.lower() for variant in variants if len(variant) >= 2}


def _score_candidate(segment: str, candidate_name: str, *, prefer_dir: bool, is_dir: bool) -> int:
    score = 0
    lowered = candidate_name.lower()
    exact_legacy = re.compile(rf'^{re.escape(segment)}(?:_v\d+.*)?$', re.IGNORECASE)
    if exact_legacy.match(candidate_name):
        score += 500

    if prefer_dir and is_dir:
        score += 100

    legacy = _split_legacy_seq(segment)
    if not legacy:
        return score

    base, seq = legacy
    candidate_seq = _extract_seq_token(candidate_name)
    if candidate_seq == seq:
        score += 200

    for variant in _abbrev_variants(base):
        if re.search(rf'(?:^|_){re.escape(variant)}(?:_|$)', lowered):
            score += 25
            break

    return score


def _resolve_candidates(search_dir: Path, segment: str, *, prefer_dir: bool) -> list[tuple[str, Path, bool]]:
    scored: list[tuple[int, str, Path, bool]] = []
    for name, path, is_dir in _iter_children(search_dir):
        if prefer_dir and not is_dir:
            continue
        score = _score_candidate(segment, name, prefer_dir=prefer_dir, is_dir=is_dir)
        if score > 0:
            scored.append((score, name, path, is_dir))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [(name, path, is_dir) for _, name, path, is_dir in scored]


def _pick_by_attrs(module_prefix: str, candidates: Iterable[tuple[str, Path, bool]], attrs: tuple[str, ...]) -> tuple[str, Path, bool] | None:
    for name, path, is_dir in candidates:
        try:
            mod = importlib.import_module(f'{module_prefix}.{name}')
        except Exception:
            continue
        if all(hasattr(mod, attr) for attr in attrs):
            return name, path, is_dir
    return None


def _resolve_module_name(seq_prefix: str, attrs: tuple[str, ...] = ()) -> str | None:
    cached = _CACHE.get(seq_prefix)
    if cached is not None:
        return cached

    parts = seq_prefix.split('.')
    search_dir = _SRC_DIR
    resolved_parts: list[str] = []

    for index, segment in enumerate(parts):
        prefer_dir = index < len(parts) - 1
        candidates = _resolve_candidates(search_dir, segment, prefer_dir=prefer_dir)
        if not candidates:
            return None

        chosen = candidates[0]
        if index == len(parts) - 1 and len(candidates) > 1 and attrs:
            module_prefix = 'src'
            if resolved_parts:
                module_prefix += '.' + '.'.join(resolved_parts)
            chosen = _pick_by_attrs(module_prefix, candidates, attrs) or chosen

        resolved_parts.append(chosen[0])
        search_dir = chosen[1]

    resolved = '.'.join(resolved_parts)
    _CACHE[seq_prefix] = resolved
    return resolved


def _find_module(seq_prefix: str) -> str | None:
    """Find the runtime module name for an old seq-based prefix."""
    return _resolve_module_name(seq_prefix)


def src_import(seq_prefix: str, *attrs: str) -> Any:
    """Import a src module by seq prefix, optionally extracting attributes.

    Returns module, single attribute, or tuple of attributes.
    """
    mod_name = _resolve_module_name(seq_prefix, attrs)
    if mod_name is None:
        raise ImportError(
            f"No pigeon module matching '{seq_prefix}' found in {_SRC_DIR}"
        )

    full = f"src.{mod_name}"
    mod = importlib.import_module(full)

    if not attrs:
        return mod
    if len(attrs) == 1:
        return getattr(mod, attrs[0])
    return tuple(getattr(mod, a) for a in attrs)
