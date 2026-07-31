"""compile_lineage_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .compile_lineage_compiled_seq003_v001 import _cut_symbols
from .compile_lineage_compiled_seq003_v001 import _merge_aliases
from .compile_lineage_compiled_seq004_v001 import _aliases_for_cut
from .compile_lineage_compiled_seq004_v001 import _identity_key
from .compile_lineage_compiled_seq004_v001 import _line_count
from .compile_lineage_compiled_seq004_v001 import _render_lineage
from .compile_lineage_compiled_seq004_v001 import _seq_from_name
from .compile_lineage_compiled_seq004_v001 import _version_from_name
from .compile_lineage_compiled_seq005_v001 import SCHEMA
from .compile_lineage_compiled_seq005_v001 import _append_jsonl
from .compile_lineage_compiled_seq005_v001 import _rel
from .compile_lineage_compiled_seq005_v001 import _write_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def write_compile_lineage(
    root: Path,
    source_file: Path,
    target_dir: Path,
    plan: dict[str, Any],
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Write per-compile lineage plus the global file identity alias map."""
    root = Path(root).resolve()
    source_file = Path(source_file).resolve()
    target_dir = Path(target_dir).resolve()
    source_rel = _rel(root, source_file)
    target_rel = _rel(root, target_dir)
    result_by_file = {
        str(row.get("file") or ""): row
        for row in (results or [])
        if isinstance(row, dict)
    }
    now = datetime.now(timezone.utc).isoformat()
    entries = []
    for index, cut in enumerate(plan.get("cuts") or [], 1):
        if not isinstance(cut, dict):
            continue
        generated_file = str(cut.get("new_file") or "").strip()
        if not generated_file:
            continue
        generated_rel = f"{target_rel}/{generated_file}".replace("\\", "/")
        generated_path = target_dir / generated_file
        symbols = _cut_symbols(cut)
        row = result_by_file.get(generated_file, {})
        line_count = row.get("lines")
        if line_count is None:
            line_count = _line_count(generated_path)
        entries.append({
            "seq": _seq_from_name(generated_file) or index,
            "version": _version_from_name(generated_file) or 1,
            "source_file": source_rel,
            "source_symbols": symbols,
            "generated_file": generated_rel,
            "generated_module": generated_path.stem,
            "identity_key": _identity_key(source_rel, symbols),
            "aliases": _aliases_for_cut(source_rel, symbols, generated_rel),
            "line_count": line_count,
            "status": row.get("status") or ("OK" if generated_path.exists() else "MISSING"),
            "reason": cut.get("reason", ""),
        })
    lineage = {
        "schema": SCHEMA,
        "compiled_at": now,
        "source_file": source_rel,
        "source_stem": source_file.stem,
        "target_dir": target_rel,
        "plan_strategy": plan.get("strategy", ""),
        "file_count": len(entries),
        "files": entries,
    }

    target_dir.mkdir(parents=True, exist_ok=True)
    _write_json(target_dir / "COMPILE_LINEAGE.json", lineage)
    (target_dir / "COMPILE_LINEAGE.md").write_text(_render_lineage(lineage), encoding="utf-8")

    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _append_jsonl(logs / "compile_lineage.jsonl", lineage)
    _merge_aliases(logs / "file_identity_aliases.json", lineage)
    return lineage
