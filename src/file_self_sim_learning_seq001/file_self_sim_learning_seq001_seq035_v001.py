"""file_self_sim_learning_seq001_seq035_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq036_v001 import _file_key_resolver
from .file_self_sim_learning_seq001_seq036_v001 import _resolve_file_key
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq040_v001 import _load_json
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _numeric_predictions(root: Path, intent_model: dict[str, Any], sources: dict[str, Any]) -> list[dict[str, Any]]:
    numeric = sources.get("numeric") or {}
    vocab = numeric.get("vocab") or {}
    matrix = numeric.get("matrix") or {}
    ids = [str(vocab.get(token)) for token in intent_model.get("tokens", []) if vocab.get(token)]
    if not ids:
        return []
    predictions = []
    resolver = _file_key_resolver(root)
    for file_key, weights in matrix.items():
        score = 0.0
        for wid in ids:
            score += float(weights.get(wid) or 0)
        if score <= 0:
            continue
        rel = resolver.get(file_key) or _resolve_file_key(root, file_key)
        if rel:
            predictions.append({"file_key": file_key, "file": rel, "score": round(score, 5)})
    predictions.sort(key=lambda item: item["score"], reverse=True)
    return predictions


def _prompt_numeric_encoding(root: Path, raw: str, sources: dict[str, Any]) -> dict[str, Any]:
    numeric = sources.get("numeric") or {}
    vocab = numeric.get("vocab") or {}
    words = _tokens(raw)
    ids = [int(vocab[word]) for word in words if word in vocab]
    return {
        "method": "intent_vocab_ids_plus_sha256_signature",
        "known_token_ids": ids[:40],
        "unknown_tokens": [word for word in words if word not in vocab][:20],
        "signature": hashlib.sha256("|".join(words).encode("utf-8")).hexdigest()[:16],
    }


def _load_numeric_surface(root: Path) -> dict[str, Any]:
    vocab_data = _load_json(root / "logs" / "intent_vocab.json") or {}
    matrix_data = _load_json(root / "logs" / "intent_matrix.json") or {}
    return {
        "vocab": vocab_data.get("word_to_id") or {},
        "matrix": matrix_data.get("matrix") or {},
    }
