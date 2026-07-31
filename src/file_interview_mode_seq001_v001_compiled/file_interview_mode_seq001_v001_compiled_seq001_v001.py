"""file_interview_mode_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq002_v001 import _answer_file
from .file_interview_mode_seq001_v001_compiled_seq002_v001 import _select_files
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _summarize_answers
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _write_outputs
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import DEFAULT_QUESTIONS
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _utcnow
from pathlib import Path
from typing import Any
import re

def interview_files(
    root: Path,
    question: str = "",
    files: list[str] | None = None,
    limit: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    """Ask selected files a question using local codebase memory."""
    root = Path(root).resolve()
    selected = _select_files(root, files or [], limit)
    questions = [question.strip()] if question.strip() else DEFAULT_QUESTIONS
    answers = [_answer_file(root, path, questions) for path in selected]
    report = {
        "schema": "file_interview/v1",
        "ts": _utcnow(),
        "question": question.strip() or " / ".join(DEFAULT_QUESTIONS),
        "files_interviewed": len(answers),
        "answers": answers,
        "summary": _summarize_answers(answers),
    }
    if write:
        _write_outputs(root, report)
    return report
