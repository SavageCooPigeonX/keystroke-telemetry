"""Naming policy helpers for the interlinked naming sim."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


def interlinked_queries() -> list[str]:
    return [
        "what_do_i_own",
        "what_number_key_am_i",
        "what_name_is_misleading",
        "who_could_break_if_i_rename",
        "what_standard_do_i_vote_for",
        "what_last_change_should_i_show",
        "what_proof_do_i_need",
    ]


def corrected_intent() -> dict[str, Any]:
    return {
        "schema": "interlinked_naming_correction/v1",
        "status": "operator_corrected",
        "downgrade": "prior_flatten_symbolic_names",
        "rule": "preserve Chinese/symbolic glyphs as semantic symbols; encode last change as file mutation state; give each file a stable number key and operator display name",
    }


def file_kind(file: str, stem: str) -> str:
    if file.startswith("test_") or "/test_" in file:
        return "test"
    if any(ord(ch) > 127 for ch in stem):
        return "symbolic_pigeon_name"
    if re.search(r"_seq\d+_v\d+", stem):
        return "versioned_module"
    return "stable_facade"


SEMANTIC_NAME_RE = re.compile(
    r"^(?P<base>.+?)(?:_seq(?P<seq>\d{3,})_v(?P<version>\d{3,})(?:__(?P<change>.+))?|_s(?P<sseq>\d{3,})_v(?P<sversion>\d{3,})(?:_d(?P<date>\d{4}))?(?:_(?P<glyph_change>.+))?)$"
)
LOOSE_SEQ_RE = re.compile(r"^(?P<base>.+?)_seq(?P<seq>\d{3,})_v(?P<version>\d{3,})(?:_|$)")
LOOSE_S_RE = re.compile(r"^(?P<base>.+?)_s(?P<seq>\d{3,})_v(?P<version>\d{3,})(?:_|$)")


def proposed_name(
    file: str,
    kind: str,
    *,
    sibling_files: list[str] | None = None,
    last_change: str = "",
) -> str:
    path = Path(file)
    if kind in {"test", "stable_facade", "symbolic_pigeon_name"}:
        return path.name
    identity = semantic_name_identity(path.stem, sibling_files=sibling_files or [])
    change = _mutation_key(last_change)
    suffix = f"__{change}" if change else ""
    return f"{identity['base']}_seq{identity['seq']:03d}_v{identity['next_version']:03d}{suffix}.py"


def discrepancy(file: str, stem: str, kind: str) -> str:
    if kind == "symbolic_pigeon_name":
        return "symbolic/Chinese glyphs are intentional identity, not noise to flatten"
    if kind == "versioned_module" and len(stem) > 70:
        return "versioned descriptive name is long; shorten only non-symbolic mutation prose"
    if kind == "test" and not Path(file).name.startswith("test_"):
        return "test does not mirror pytest naming"
    return "name is acceptable, but should declare facade/internal and mutation state"


def standard(rows: list[dict[str, Any]]) -> dict[str, Any]:
    kinds = Counter(row["declared_kind"] for row in rows)
    return {
        "convention": "preserve Chinese/symbolic glyphs; add F##### stable number keys; keep readable public facades; internals carry domain_capability_seqNNN_vMMM plus last_change mutation state",
        "rationale": "The symbolic layer is semantic memory, the number key is the stable address, and the last-change layer makes the repo read like a changelog.",
        "votes": dict(kinds),
        "accepted_now": False,
        "corrected_intent": corrected_intent(),
        "next_gate": "generate import map, mutation-state map, and per-file rename/no-rename plan, then ask operator approval",
    }


def semantic_name_identity(stem: str, *, sibling_files: list[str] | None = None) -> dict[str, Any]:
    """Parse a semantic filename and allocate sequence/version from local siblings."""
    clean = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_").lower() or "module"
    match = SEMANTIC_NAME_RE.match(clean) or LOOSE_SEQ_RE.match(clean) or LOOSE_S_RE.match(clean)
    if match:
        base = re.sub(r"_+$", "", match.group("base")) or "module"
        seq = int(_group(match, "seq") or _group(match, "sseq") or 1)
        version = int(_group(match, "version") or _group(match, "sversion") or 1)
        source = "parsed_existing_name"
    else:
        base = re.sub(r"_(?:seq|s)?\d{3,}.*$", "", clean) or clean
        seq = _next_sequence(base, sibling_files or [])
        version = 0
        source = "allocated_from_siblings"
    return {
        "base": base,
        "seq": seq,
        "version": version,
        "next_version": max(1, version + 1),
        "source": source,
    }


def _next_sequence(base: str, sibling_files: list[str]) -> int:
    used = []
    exact_family_seen = False
    for sibling in sibling_files:
        sstem = Path(sibling).stem.lower()
        match = SEMANTIC_NAME_RE.match(re.sub(r"[^A-Za-z0-9_]+", "_", sstem))
        if not match:
            match = LOOSE_SEQ_RE.match(re.sub(r"[^A-Za-z0-9_]+", "_", sstem))
        if not match:
            match = LOOSE_S_RE.match(re.sub(r"[^A-Za-z0-9_]+", "_", sstem))
        if not match:
            continue
        sibling_base = re.sub(r"_+$", "", match.group("base"))
        sibling_seq = int(_group(match, "seq") or _group(match, "sseq") or 0)
        if sibling_seq:
            used.append(sibling_seq)
        if sibling_base == base:
            exact_family_seen = True
    if exact_family_seen:
        return max((seq for seq in used), default=0) + 1
    return max(used, default=0) + 1


def _group(match: re.Match[str], name: str) -> str:
    try:
        return match.group(name) or ""
    except IndexError:
        return ""


def _mutation_key(last_change: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", str(last_change or "").lower())
    stop = {"the", "and", "for", "with", "that", "this", "into", "from", "keep", "state", "change"}
    words = [word for word in words if len(word) > 2 and word not in stop]
    return "lc_" + "_".join(words[:6]) if words else ""
