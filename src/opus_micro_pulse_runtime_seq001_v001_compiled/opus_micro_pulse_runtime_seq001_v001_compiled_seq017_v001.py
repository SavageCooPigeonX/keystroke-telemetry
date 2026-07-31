"""opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json
import re

def _epistemic_status(prompt_class: str) -> str:
    if prompt_class in {"conversation", "exploration", "correction", "planning"}:
        return "candidate_learning_not_durable_truth"
    if prompt_class == "audit":
        return "inspection_before_mutation"
    return "sealed_or_actionable_after_enter"


def _class_priority(name: str) -> int:
    return {"directive": 7, "debug": 6, "correction": 5, "audit": 4, "planning": 3, "exploration": 2, "conversation": 1}.get(name, 0)


def _composition_source(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_rewrites": bool(row.get("rewrites")),
        "rewrite_count": len(row.get("rewrites") or []),
        "hesitation_count": (row.get("signals") or {}).get("hesitation_count"),
        "source": row.get("source", ""),
    }


def _latest_prompt_row(root: Path) -> dict[str, Any]:
    path = root / "logs" / "prompt_journal.jsonl"
    if not path.exists():
        return {}
    for line in reversed(path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            return json.loads(line)
        except Exception:
            continue
    return {}


def _row_text(row: dict[str, Any]) -> str:
    return str(row.get("msg") or row.get("prompt") or row.get("text") or row.get("message") or "")


def _git_changed_files(root: Path) -> list[str]:
    import subprocess

    out: list[str] = []
    for cmd in (["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"]):
        try:
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except Exception:
            continue
        if proc.returncode == 0:
            out.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    return list(dict.fromkeys(out))


def _tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9]+", str(text).replace("_", " ").lower()) if len(tok) > 2]
