"""file_interview_mode_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _append_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _codex_takeaway(rel: str, fix: str, risk: dict[str, Any]) -> str:
    return f"{rel} says: {fix} Risk is {risk.get('level')}."


def _summarize_answers(answers: list[dict[str, Any]]) -> dict[str, Any]:
    high = [a["file"] for a in answers if (a.get("risk") or {}).get("level") == "high"]
    pending = [a["file"] for a in answers if (a.get("evidence") or {}).get("pending_context_questions")]
    return {
        "high_risk_files": high,
        "files_with_pending_questions": pending,
        "top_takeaways": [a.get("codex_takeaway", "") for a in answers[:5]],
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _append_jsonl(logs / "file_interviews.jsonl", report)
    (logs / "file_interview_latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (logs / "file_interview_latest.md").write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# File Interview",
        "",
        f"- ts: `{report.get('ts')}`",
        f"- question: {report.get('question')}",
        "",
    ]
    for answer in report.get("answers") or []:
        lines.extend([
            f"## `{answer.get('file')}`",
            f"- file says: {answer.get('file_says')}",
            f"- I think the fix is: {answer.get('i_think_fix_is')}",
            f"- risk: `{(answer.get('risk') or {}).get('level')}` {', '.join((answer.get('risk') or {}).get('items') or [])}",
            f"- current identity: `{(answer.get('rename_identity') or {}).get('current_file', '')}`",
            "",
        ])
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
