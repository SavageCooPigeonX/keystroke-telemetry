"""folder_context_coupling_seq001_v001_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import _IDENTITY_STOPWORDS
from pathlib import Path

def _path_identity_tokens(folder: str) -> list[str]:
    if folder in {"", "."}:
        return ["root", "manifest"]
    if folder == "src":
        return ["source", "warehouse"]
    leaf = folder.replace("\\", "/").rstrip("/").split("/")[-1]
    tokens = [token for token in _split_identity_text(leaf) if token not in _IDENTITY_STOPWORDS]
    return tokens or [token for token in _split_identity_text(folder) if token not in _IDENTITY_STOPWORDS]


def _read_prefix(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def _split_identity_text(text: str) -> list[str]:
    chars = []
    for ch in text.replace("\\", "/"):
        if ch.isalnum():
            chars.append(ch.lower())
        else:
            chars.append(" ")
    raw = "".join(chars).split()
    pieces = []
    for token in raw:
        pieces.extend(_split_camel(token))
    return [piece for piece in pieces if len(piece) >= 3 and not piece.isdigit()]


def _split_camel(token: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    for idx in range(1, len(token)):
        if token[idx].isupper() and not token[idx - 1].isupper():
            pieces.append(token[start:idx].lower())
            start = idx
    pieces.append(token[start:].lower())
    return pieces
