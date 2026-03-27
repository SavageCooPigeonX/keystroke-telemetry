"""prediction_scorer_seq014_edit_session_analyzer_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 21 lines | ~187 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from typing import Any
import re

def _get_edit_session_modules(
    edit_pairs: list[dict[str, Any]], after_session_n: int, window: int,
) -> tuple[set[str], list[dict[str, Any]]]:
    """Get modules edited in the evaluation window after a prediction.

    Returns (module_names, matching_edit_pairs).
    """
    modules = set()
    matching = []
    for ep in edit_pairs:
        sn = ep.get("session_n", 0)
        if after_session_n < sn <= after_session_n + window:
            mod = extract_module_name(ep.get("file", ""))
            if mod:
                modules.add(mod)
            matching.append(ep)
    return modules, matching
