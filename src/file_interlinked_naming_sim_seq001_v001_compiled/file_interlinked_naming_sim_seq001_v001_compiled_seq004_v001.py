"""file_interlinked_naming_sim_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interlinked_naming_sim_seq001_v001_compiled_seq005_v001 import _last_change_state
from .file_interlinked_naming_sim_seq001_v001_compiled_seq005_v001 import _sibling_files
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _rename_risk
from pathlib import Path
from src.file_interlinked_naming_policy_seq001_v001 import (
    corrected_intent,
    discrepancy,
    file_kind,
    interlinked_queries,
    proposed_name,
    standard,
)
from src.file_number_key_identity_seq001_v001 import file_identity_card, ownership_from_name
from typing import Any
import re

def _query_file(root: Path, file: str) -> dict[str, Any]:
    path = root / file
    stem = path.stem
    kind = file_kind(file, stem)
    name_gap = discrepancy(file, stem, kind)
    last_change = _last_change_state(root, file, kind)
    proposed = proposed_name(file, kind, sibling_files=_sibling_files(root, file), last_change=last_change)
    identity = file_identity_card(file, kind, last_change)
    return {
        "schema": "interlinked_naming_query/v1",
        "file": file,
        "current_name": path.name,
        "declared_kind": kind,
        "identity": identity,
        "number_key": identity["number_key"],
        "operator_display_name": identity["operator_display_name"],
        "mutation_name": identity["mutation_name"],
        "answers": {
            "what_do_i_own": ownership_from_name(stem),
            "what_number_key_am_i": identity["number_key"],
            "what_name_is_misleading": name_gap,
            "who_could_break_if_i_rename": _rename_risk(file),
            "what_standard_do_i_vote_for": "F key + Inator display + symbolic glyphs + last_change mutation state",
            "what_last_change_should_i_show": last_change,
            "what_proof_do_i_need": ["import smoke test", "nearby unit test", "git grep old import path", "manifest refresh"],
        },
        "discrepancy": name_gap,
        "proposed_name": proposed,
        "last_change_state": last_change,
        "downgrade": "prior_flatten_symbolic_names" if kind == "symbolic_pigeon_name" else "",
        "approval": "approve_plan_not_rename",
        "file_text": f"I vote to plan `{path.name}` as `{proposed}` but only after import-map proof.",
    }


def _queries() -> list[str]:
    return interlinked_queries()
