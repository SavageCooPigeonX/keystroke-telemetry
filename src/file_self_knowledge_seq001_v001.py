"""Stable facade for file self-knowledge with source-quote enrichment."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "src").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.file_self_knowledge_source_quote_seq002_v001 import read_source_quote
from src.pigeon_legacy_loader_seq001_v001 import load_legacy_module

load_legacy_module(
    __name__,
    globals(),
    "src/file_self_knowledge_seq001_v001.py",
)

_legacy_build_file_self_knowledge = build_file_self_knowledge
_legacy_write_file_self_knowledge = _write_outputs


def build_file_self_knowledge(
    root: Path,
    files: list[Any] | None = None,
    prompt: str = "",
    limit: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    """Preserve the rich v1 packet contract and quote the live source."""
    root = Path(root)
    result = _legacy_build_file_self_knowledge(
        root,
        files=files,
        prompt=prompt,
        limit=limit,
        write=False,
    )
    for packet in result.get("packets") or []:
        quote = read_source_quote(root / str(packet.get("file") or ""))
        if quote:
            packet["file_quote"] = quote
    if write:
        _legacy_write_file_self_knowledge(root, result)
    return result
