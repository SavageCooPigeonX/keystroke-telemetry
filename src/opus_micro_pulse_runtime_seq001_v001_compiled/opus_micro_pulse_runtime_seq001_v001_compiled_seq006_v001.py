"""opus_micro_pulse_runtime_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001 import _deepseek_note
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001 import _file_solution
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001 import _mismatch
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001 import _persistent_faults
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq007_v001 import _why_opus_called
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _identity_from_path
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _intent_keys
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _tokens
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _numeric
from pathlib import Path
from typing import Any
import re

def _file_interrogation(root: Path, rel: str, fragment: str, classification: dict[str, Any], pulse_index: int) -> dict[str, Any]:
    profile = _file_profile(root, rel)
    intent_keys = _intent_keys(fragment, classification)
    reason = _why_opus_called(rel, fragment, classification)
    self_claim = profile.get("identity") or _identity_from_path(rel)
    mismatch = _mismatch(reason, self_claim)
    solution = _file_solution(rel, classification, mismatch)
    faults = _persistent_faults(root, rel)
    comment = (
        f"I was touched by Opus on pause {pulse_index} because it thinks I am {reason}. "
        f"I am really {self_claim}. {mismatch} Solution: {solution}. "
        f"Persistent faults: {faults}."
    )
    return {
        "file": rel,
        "opus_reason": reason,
        "file_self_model": self_claim,
        "mismatch": mismatch,
        "intent_keys": intent_keys,
        "file_comment": comment,
        "coding_agent_note": (
            f"If Codex touches `{rel}`, verify whether Opus prediction `{reason}` matched actual role `{self_claim}`. "
            f"After execution, write touched/predicted/missed status into the backward learning packet."
        ),
        "deepseek_folder_manager_note": _deepseek_note(rel, solution),
        "persistent_faults": faults,
        "numeric_encoding": _numeric(_tokens(" ".join([rel, fragment, self_claim]))),
    }


def _file_profile(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if path.exists() and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:5000]
        except Exception:
            text = ""
        doc = ""
        for line in text.splitlines()[:20]:
            stripped = line.strip().strip('"')
            if stripped and not stripped.startswith(("from ", "import ")):
                doc = stripped
                break
        return {"identity": doc or _identity_from_path(rel)}
    return {"identity": _identity_from_path(rel)}
