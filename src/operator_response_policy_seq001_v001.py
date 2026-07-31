"""Stable facade combining the v1 response API with file-comment policy."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(
    __name__,
    globals(),
    "src/operator_response_policy_seq001_v001.py",
)

from src.operator_response_policy_builder_seq002_v001 import (
    build_operator_response_policy as _build_file_comment_policy,
)

_legacy_build_operator_response_policy = build_operator_response_policy


def build_operator_response_policy(
    root: Path,
    prompt: str,
    surface: str = "codex",
    context_pack: dict[str, Any] | None = None,
    inject: bool = True,
    write: bool = True,
) -> dict[str, Any]:
    """Keep v1 routing/reward behavior and append the v2 file-comment contract."""
    result = _legacy_build_operator_response_policy(
        root,
        prompt,
        surface=surface,
        context_pack=context_pack,
        inject=inject,
        write=write,
    )
    extension = _build_file_comment_policy(
        root,
        prompt,
        surface=surface,
        context_pack=context_pack,
        inject=inject,
        write=write,
    )
    result["status"] = "ok"
    for key in ("file_comments", "deepseek_response_policy_audit", "response_contract"):
        result[key] = extension[key]
    if extension["file_comments"]:
        sections = list(result.get("required_sections") or [])
        if "File Comments" not in sections:
            sections.append("File Comments")
        result["required_sections"] = sections
    return result
