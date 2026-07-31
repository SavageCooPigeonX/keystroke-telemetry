"""analyze_prompt_behavior_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq001_v001 import _parse_ts
from .analyze_prompt_behavior_compiled_seq001_v001 import _reinforcement
from .analyze_prompt_behavior_compiled_seq001_v001 import _themes
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from .analyze_prompt_behavior_compiled_seq023_v001 import STOPWORDS
from typing import Any
import re

def _cognitive_load(row: dict[str, Any]) -> float:
    signals = row.get("signals") if isinstance(row.get("signals"), dict) else {}
    deletion = float(signals.get("deletion_ratio") or 0.0)
    intent_deletion = float(signals.get("intent_deletion_ratio") or 0.0)
    hesitation = min(float(signals.get("hesitation_count") or 0.0) / 12.0, 1.0)
    rewrites = min(float(signals.get("rewrite_count") or 0.0) / 6.0, 1.0)
    typo = min(float(signals.get("typo_corrections") or 0.0) / 12.0, 1.0)
    length = min(len(str(row.get("msg") or "")) / 900.0, 1.0)
    frustration = 0.25 if row.get("cognitive_state") == "frustrated" else 0.0
    return round(min(1.0, deletion * 0.25 + intent_deletion * 0.2 + hesitation * 0.2 + rewrites * 0.15 + typo * 0.1 + length * 0.1 + frustration), 4)


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _prepare(rows: list[dict[str, Any]], since: str | None) -> list[PromptRow]:
    since_dt = _parse_ts(since) if since else None
    out: list[PromptRow] = []
    for row in rows:
        ts = _parse_ts(str(row.get("ts") or ""))
        if since_dt and ts < since_dt:
            continue
        msg = str(row.get("msg") or "")
        joined = msg + " " + " ".join(str(x) for x in row.get("deleted_words") or [])
        out.append(
            PromptRow(
                raw=row,
                ts=ts,
                session_n=int(row.get("session_n") or 0),
                msg=msg,
                themes=_themes(joined),
                reinforcement=_reinforcement(row, joined),
                cognitive_load=_cognitive_load(row),
                tokens=_tokens(joined),
            )
        )
    return out
