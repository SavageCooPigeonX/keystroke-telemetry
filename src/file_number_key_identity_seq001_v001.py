"""Stable file number keys plus operator-readable identity names."""
from __future__ import annotations

import re
import zlib
from pathlib import Path
from typing import Any


def file_identity_card(file: str, kind: str, last_change: str) -> dict[str, Any]:
    path = Path(file)
    ownership = ownership_from_name(path.stem)
    key = file_number_key(file)
    return {
        "schema": "file_number_key_identity/v1",
        "number_key": key,
        "stable_address": f"{key}:{file}",
        "operator_display_name": operator_display_name(ownership, kind),
        "mutation_name": mutation_name(ownership, last_change),
        "symbolic_identity": path.name if kind == "symbolic_pigeon_name" else "",
        "operator_rule": "imports bind to path/manifest; people talk to the number key and display name",
    }


def file_number_key(file: str) -> str:
    value = zlib.crc32(file.encode("utf-8")) % 100000
    return f"F{value:05d}"


def operator_display_name(ownership: str, kind: str) -> str:
    phrase = _slug_words(ownership)
    if kind == "symbolic_pigeon_name":
        phrase = f"Glyph-Preserving-{phrase}"
    elif kind == "test":
        phrase = f"Proof-That-{phrase}-Works"
    elif kind == "stable_facade":
        phrase = f"Public-Doorway-For-{phrase}"
    return f"The-{phrase}-Inator"


def mutation_name(ownership: str, last_change: str) -> str:
    change = _slug_words(last_change)
    owner = _slug_words(ownership)
    return f"{owner}__last-change__{change}"


def ownership_from_name(stem: str) -> str:
    tokens = [t for t in re.split(r"[_\W]+", stem) if t and not re.match(r"^(seq|v)?\d+$", t)]
    return " ".join(tokens[:6]) or "unknown ownership"


def identity_standard() -> str:
    return "F##### stable key + self-authored Inator display name + mutation_name + preserved symbolic identity"


def _slug_words(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text)
    if not words:
        words = ["Symbolic", "File"]
    return "-".join(word[:24] for word in words[:8])
