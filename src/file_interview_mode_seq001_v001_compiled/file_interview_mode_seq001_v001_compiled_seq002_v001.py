"""file_interview_mode_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq003_v001 import _recent_learning_files
from .file_interview_mode_seq001_v001_compiled_seq003_v001 import _resolve_file
from .file_interview_mode_seq001_v001_compiled_seq004_v001 import _comments_for_file
from .file_interview_mode_seq001_v001_compiled_seq004_v001 import _file_profile
from .file_interview_mode_seq001_v001_compiled_seq005_v001 import _alias_for_file
from .file_interview_mode_seq001_v001_compiled_seq005_v001 import _context_questions_for_file
from .file_interview_mode_seq001_v001_compiled_seq006_v001 import _latest_push_cycle
from .file_interview_mode_seq001_v001_compiled_seq006_v001 import _proposed_fix
from .file_interview_mode_seq001_v001_compiled_seq006_v001 import _risk_for_file
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _codex_takeaway
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _rel
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _safe_read
from pathlib import Path
from typing import Any
import re

def _answer_file(root: Path, path: Path, questions: list[str]) -> dict[str, Any]:
    rel = _rel(root, path)
    text = _safe_read(path)
    profile = _file_profile(text)
    comments = _comments_for_file(root, rel)
    context_questions = _context_questions_for_file(root, rel)
    alias = _alias_for_file(root, rel)
    push = _latest_push_cycle(root)
    risk = _risk_for_file(rel, text, alias, context_questions)
    fix = _proposed_fix(rel, questions, comments, context_questions, alias, risk)
    return {
        "file": rel,
        "question": " / ".join(questions),
        "file_says": profile["says"],
        "i_think_fix_is": fix,
        "evidence": {
            "prior_file_comments": comments[:3],
            "pending_context_questions": context_questions[:5],
            "latest_push_cycle": push,
        },
        "rename_identity": alias,
        "risk": risk,
        "codex_takeaway": _codex_takeaway(rel, fix, risk),
    }


def _select_files(root: Path, requested: list[str], limit: int) -> list[Path]:
    selected: list[Path] = []
    for item in requested:
        resolved = _resolve_file(root, item)
        if resolved and resolved not in selected:
            selected.append(resolved)
    if selected:
        return selected[:limit]

    for candidate in _recent_learning_files(root):
        resolved = _resolve_file(root, candidate)
        if resolved and resolved not in selected:
            selected.append(resolved)
        if len(selected) >= limit:
            break
    return selected
