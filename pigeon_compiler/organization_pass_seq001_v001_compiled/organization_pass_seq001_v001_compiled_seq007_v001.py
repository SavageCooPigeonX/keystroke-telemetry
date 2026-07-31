"""organization_pass_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from dataclasses import dataclass
from pathlib import Path
import json
import re

def main() -> int:
    from .organization_pass_seq001_v001_compiled_seq001_v001 import build_organization_plan

    root = Path.cwd()
    plan = build_organization_plan(root, write=True)
    summary = plan["summary"]
    print(
        f"scanned={summary['files_scanned']} folders={summary['folders_scanned']} "
        f"moves={summary['candidate_moves']} overcap={summary['overcap_files']}"
    )
    print(f"wrote {LATEST} and {MARKDOWN}")
    return 0


SCHEMA = "pigeon_codebase_organization_plan/v1"

LATEST = "logs/pigeon_codebase_organization_plan_latest.json"

HISTORY = "logs/pigeon_codebase_organization_plan.jsonl"

MARKDOWN = "logs/pigeon_codebase_organization_plan.md"

MAX_PY_LINES = 200

SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    ".venv",
}

TOP_SOURCE_DIRS = {"src", "pigeon_compiler", "pigeon_brain", "client", "scripts"}

ROOT_SRC_FAMILIES = {
    "batch": "src/batch_rewrite",
    "codex": "src/codex_runtime",
    "context": "src/context_orchestration",
    "deepseek": "src/deepseek_lane",
    "email": "src/dead_email_lane",
    "escalation": "src/escalation_engine",
    "file": "src/file_sim",
    "folder": "src/manifest_orchestration",
    "hush": "src/live_intent_runtime",
    "intent": "src/intent_keys",
    "manifest": "src/manifest_orchestration",
    "operator": "src/operator_state",
    "opus": "src/opus_orchestrator",
    "session": "src/session_macro_cycle",
    "tc": "src/thought_completer",
}


@dataclass(frozen=True)
class FileInfo:
    rel: str
    folder: str
    module: str
    line_count: int
    imports: tuple[str, ...]
    parse_error: str = ""
