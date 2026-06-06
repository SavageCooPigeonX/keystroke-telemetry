"""file_self_sim_learning_seq001_seq039_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
import re

def _stem_key(rel: str) -> str:
    stem = Path(str(rel)).stem.lower()
    stem = re.sub(r"_seq\d+(?=_|$)", "", stem)
    stem = re.sub(r"_s\d{3}(?=_|$)", "", stem)
    stem = re.sub(r"_v\d+(?=_|$)", "", stem)
    stem = re.sub(r"_d\d{4}(?=_|$)", "", stem)
    stem = stem.split("__", 1)[0]
    stem = re.sub(r"[^a-z0-9_]+", "_", stem)
    return re.sub(r"_+", "_", stem).strip("_") or Path(str(rel)).stem.lower()


def _fallback_intent_key(tokens: list[str]) -> str:
    unique_tokens = _dedupe(tokens)
    unique_set = set(unique_tokens)
    target_tokens = [
        token for token in unique_tokens
        if not (token.endswith("s") and len(token) > 4 and token[:-1] in unique_set)
    ]
    verb = "build"
    if {"test", "validate", "verify"} & set(unique_tokens):
        verb = "validate"
    if {"rewrite", "overwrite", "patch", "fix"} & set(unique_tokens):
        verb = "patch"
    target = "_".join(target_tokens[:5])[:64] or "work"
    scale = "major" if {"rewrite", "overwrite", "batch"} & set(unique_tokens) else "patch"
    return f"root:{verb}:{target}:{scale}"


def _line_count(root: Path, rel: str) -> int:
    try:
        return len((root / rel).read_text(encoding="utf-8", errors="ignore").splitlines())
    except Exception:
        return 0


def _estimate_tokens(root: Path, rel: str) -> int:
    try:
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def _exists_bonus(root: Path, rel: str) -> int:
    return 1 if (root / rel).exists() else 0
