"""compile_lineage_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import re

def _aliases_for_cut(source_rel: str, symbols: list[str], generated_rel: str) -> list[str]:
    aliases = [generated_rel]
    for symbol in symbols:
        aliases.extend([
            f"{source_rel}::{symbol}",
            f"{Path(source_rel).stem}::{symbol}",
            symbol,
        ])
    return list(dict.fromkeys(aliases))


def _identity_key(source_rel: str, symbols: list[str]) -> str:
    if not symbols:
        return f"{source_rel}::*"
    return f"{source_rel}::{'|'.join(symbols)}"


def _render_lineage(lineage: dict[str, Any]) -> str:
    lines = [
        f"# Compile Lineage - {lineage.get('source_file')}",
        "",
        f"- schema: `{lineage.get('schema')}`",
        f"- compiled_at: `{lineage.get('compiled_at')}`",
        f"- target_dir: `{lineage.get('target_dir')}`",
        f"- file_count: `{lineage.get('file_count')}`",
        "",
        "| Source Symbols | Generated File | Identity |",
        "|---|---|---|",
    ]
    for entry in lineage.get("files") or []:
        symbols = ", ".join(entry.get("source_symbols") or ["*"])
        lines.append(
            f"| `{symbols}` | `{entry.get('generated_file')}` | `{entry.get('identity_key')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _seq_from_name(name: str) -> int | None:
    match = re.search(r"_seq(\d+)_", name)
    return int(match.group(1)) if match else None


def _version_from_name(name: str) -> int | None:
    match = re.search(r"_v(\d+)\.py$", name)
    return int(match.group(1)) if match else None


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
