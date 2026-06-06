"""file_self_sim_learning_seq001_seq038_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq041_v001 import ALIASES
from .file_self_sim_learning_seq001_seq041_v001 import STOP
from pathlib import Path
from typing import Any
import hashlib
import re

def _hash_encoding(text: str) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [int.from_bytes(digest[i:i + 2], "big") for i in range(0, 16, 2)]
    return {
        "method": "sha256_u16_file_intent_profile",
        "signature": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "vector_u16": vector,
    }


def _profile_hint(packet: dict[str, Any]) -> str:
    veins = [item.get("file") for item in packet.get("context_veins", [])[:3]]
    validation = (packet.get("verification_packet") or {}).get("validation_plan", [])
    return " ".join([
        f"For {packet.get('intent_key', '')}, load {', '.join(veins) or 'manifest/test context'} first.",
        f"Validate with {validation[0] if validation else 'git diff --check'}.",
        "Do not self-overwrite until approval and outcome reward are recorded.",
    ])[:360]


def _clean_rel(value: Any) -> str:
    text = str(value or "").strip().strip("'\"").replace("\\", "/")
    if not text or text.startswith("/") or (len(text) > 1 and text[1] == ":"):
        return ""
    if ".." in Path(text).parts:
        return ""
    return text


def _tokens(text: str) -> list[str]:
    out = []
    for raw in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower()):
        expanded = [raw]
        if "_" in raw:
            expanded.extend(part for part in raw.split("_") if part)
        for token in expanded:
            token = token.strip("_")
            if len(token) >= 3 and token not in STOP:
                normalized = ALIASES.get(token, token)
                out.append(normalized)
                if normalized.endswith("s") and len(normalized) > 4:
                    out.append(normalized[:-1])
    return out
