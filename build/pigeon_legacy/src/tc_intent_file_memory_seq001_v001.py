"""Natural intent-key to file memory for Thought Completer.

This is the small learning layer between structured intent extraction and file
selection. Intent graphs already know which files were selected, deranked, or
later edited; this module turns that into durable priors so future prompts can
wake files from history instead of starting from heuristics every time.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "tc_intent_file_memory/v1"


def learn_intent_file_memory(
    root: Path,
    graph: dict[str, Any] | None = None,
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Fold one intent graph into the durable intent-file memory."""
    root = Path(root)
    state = _load_state(root)
    graph = graph or {}
    selected = (graph.get("context_clearing_pass") or {}).get("selected_files") or []
    deranked = (graph.get("context_clearing_pass") or {}).get("deranked_files") or []
    selected_by_intent = _files_by_supporting_intent(selected)
    deranked_by_intent = _files_by_supporting_intent(deranked, deranked=True)
    touched: list[dict[str, Any]] = []

    for intent in graph.get("intents") or []:
        intent_key = str(intent.get("intent_key") or "").strip()
        if not intent_key:
            continue
        node = state["intent_keys"].setdefault(intent_key, _new_intent_record(intent))
        files = selected_by_intent.get(intent_key) or _files_from_intent(root, intent)
        negatives = deranked_by_intent.get(intent_key, [])
        _update_record(node, graph, intent, files, negatives)
        touched.append(_summary(node))

    state["updated_at"] = _now()
    summary = {
        "schema": "tc_intent_file_memory_update/v1",
        "ts": state["updated_at"],
        "graph_id": graph.get("graph_id", ""),
        "intent_keys_touched": touched,
        "intent_key_count": len(state["intent_keys"]),
        "top_files": _top_global_files(state),
        "paths": {
            "state": "logs/intent_file_memory.json",
            "latest": "logs/intent_file_memory_latest.json",
            "history": "logs/intent_file_memory_history.jsonl",
            "markdown": "logs/intent_file_memory.md",
        },
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "intent_file_memory.json", state)
        _write_json(logs / "intent_file_memory_latest.json", summary)
        _append_jsonl(logs / "intent_file_memory_history.jsonl", summary)
        (logs / "intent_file_memory.md").write_text(render_intent_file_memory(state), encoding="utf-8")
    return summary


def match_intent_file_memory(
    root: Path,
    text: str = "",
    *,
    intent_key: str = "",
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return learned file priors for an exact or semantically similar intent."""
    state = _load_state(Path(root))
    prompt_tokens = set(_tokens(" ".join([text, intent_key])))
    candidates: dict[str, dict[str, Any]] = {}

    exact = (state.get("intent_keys") or {}).get(intent_key)
    if exact:
        _add_record_matches(candidates, exact, source="exact_intent_key", multiplier=1.35)

    for record in (state.get("intent_keys") or {}).values():
        tokens = set(record.get("tokens") or [])
        overlap = tokens & prompt_tokens
        if not overlap:
            continue
        multiplier = 0.55 + min(len(overlap), 6) * 0.16
        _add_record_matches(
            candidates,
            record,
            source=f"intent_memory_overlap:{','.join(sorted(overlap)[:5])}",
            multiplier=multiplier,
        )

    rows = list(candidates.values())
    rows.sort(key=lambda item: (float(item.get("score") or 0.0), int(item.get("seen") or 0)), reverse=True)
    return rows[: max(1, int(limit or 8))]


def render_intent_file_memory(state: dict[str, Any]) -> str:
    records = sorted(
        (state.get("intent_keys") or {}).values(),
        key=lambda item: (int(item.get("prompt_count") or 0), item.get("updated_at", "")),
        reverse=True,
    )
    lines = [
        "# Intent File Memory",
        "",
        "Thought Completer's learned map of which intent keys naturally wake which files.",
        "",
        f"- intent_keys: `{len(records)}`",
        f"- updated_at: `{state.get('updated_at', '')}`",
        "",
    ]
    for record in records[:50]:
        lines.extend([
            f"## {record.get('intent_key')}",
            "",
            f"- prompts: `{record.get('prompt_count', 0)}`",
            f"- dominant_files: `{', '.join(record.get('dominant_files', [])[:8]) or 'none'}`",
            f"- deranked_recent: `{', '.join(record.get('deranked_recent', [])[:6]) or 'none'}`",
            f"- last_segment: {str(record.get('last_segment') or '')[:220]}",
            "",
        ])
    return "\n".join(lines)


def _add_record_matches(
    candidates: dict[str, dict[str, Any]],
    record: dict[str, Any],
    *,
    source: str,
    multiplier: float,
) -> None:
    for rel in record.get("dominant_files") or []:
        score_data = (record.get("file_scores") or {}).get(rel) or {}
        base = max(float(score_data.get("score") or 0.1), 0.1)
        row = candidates.setdefault(rel, {
            "file": rel,
            "score": 0.0,
            "seen": 0,
            "sources": [],
            "intent_keys": [],
        })
        row["score"] = round(float(row.get("score") or 0.0) + base * multiplier, 4)
        row["seen"] = int(row.get("seen") or 0) + int(score_data.get("selected_count") or 1)
        row["sources"] = _dedupe([*row.get("sources", []), source])[:6]
        row["intent_keys"] = _dedupe([*row.get("intent_keys", []), record.get("intent_key")])[:6]


def _update_record(
    record: dict[str, Any],
    graph: dict[str, Any],
    intent: dict[str, Any],
    selected_files: list[dict[str, Any]],
    deranked_files: list[dict[str, Any]],
) -> None:
    record["prompt_count"] = int(record.get("prompt_count") or 0) + 1
    record["updated_at"] = _now()
    record["last_graph_id"] = graph.get("graph_id", "")
    record["last_segment"] = intent.get("segment", "")
    record["tokens"] = sorted(set([
        *record.get("tokens", []),
        *_tokens(intent.get("segment", "")),
        *_tokens(intent.get("intent_key", "")),
    ]))
    scores = record.setdefault("file_scores", {})
    for item in selected_files:
        rel = _rel(item.get("file") or item.get("path") or item.get("name"))
        if not rel:
            continue
        current = scores.setdefault(rel, {"score": 0.0, "selected_count": 0, "last_reasons": []})
        current["score"] = round(float(current.get("score") or 0.0) + max(float(item.get("final_score") or item.get("score") or 0.25), 0.25), 4)
        current["selected_count"] = int(current.get("selected_count") or 0) + 1
        current["last_reasons"] = _dedupe(list(item.get("reasons") or []) + ["selected by intent graph"])[:6]
    for item in deranked_files:
        rel = _rel(item.get("file") or item.get("path") or item.get("name"))
        if not rel:
            continue
        current = scores.setdefault(rel, {"score": 0.0, "selected_count": 0, "last_reasons": []})
        current["score"] = round(float(current.get("score") or 0.0) - 0.35, 4)
        current["last_derank_reasons"] = _dedupe(list(item.get("derank_reasons") or []) + ["deranked by intent graph"])[:6]
    ranked = sorted(
        scores.items(),
        key=lambda pair: (float(pair[1].get("score") or 0.0), int(pair[1].get("selected_count") or 0)),
        reverse=True,
    )
    record["dominant_files"] = [rel for rel, data in ranked if float(data.get("score") or 0.0) > 0][:12]
    record["deranked_recent"] = [_rel(item.get("file") or item.get("path") or item.get("name")) for item in deranked_files[:8]]
    examples = list(record.get("examples") or [])
    examples.append({
        "ts": graph.get("ts"),
        "graph_id": graph.get("graph_id"),
        "segment": intent.get("segment", ""),
        "prompt": str(graph.get("prompt") or "")[:240],
    })
    record["examples"] = examples[-8:]


def _files_by_supporting_intent(files: list[dict[str, Any]], *, deranked: bool = False) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    keys = ("supporting_intents", "deranked_by") if deranked else ("supporting_intents",)
    for item in files:
        for field in keys:
            for intent_key in item.get(field) or []:
                out.setdefault(str(intent_key), []).append(item)
    return out


def _files_from_intent(root: Path, intent: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for rel in intent.get("files") or []:
        rel = _rel(rel)
        if rel and (root / rel).exists():
            rows.append({"file": rel, "final_score": 0.35, "reasons": ["intent listed file before clearing"]})
    return rows


def _new_intent_record(intent: dict[str, Any]) -> dict[str, Any]:
    intent_key = str(intent.get("intent_key") or "")
    return {
        "intent_id": "ifm-" + hashlib.sha256(intent_key.encode("utf-8")).hexdigest()[:16],
        "intent_key": intent_key,
        "scope": intent.get("scope", ""),
        "verb": intent.get("verb", ""),
        "target": intent.get("target", ""),
        "scale": intent.get("scale", ""),
        "tokens": sorted(set(_tokens(" ".join([
            intent_key,
            str(intent.get("segment") or ""),
            str(intent.get("scope") or ""),
            str(intent.get("target") or ""),
        ])))),
        "prompt_count": 0,
        "file_scores": {},
        "dominant_files": [],
        "deranked_recent": [],
        "examples": [],
        "created_at": _now(),
        "updated_at": _now(),
    }


def _summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "intent_key": record.get("intent_key"),
        "prompt_count": record.get("prompt_count", 0),
        "dominant_files": record.get("dominant_files", [])[:6],
    }


def _top_global_files(state: dict[str, Any]) -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    for record in (state.get("intent_keys") or {}).values():
        for rel, data in (record.get("file_scores") or {}).items():
            totals[rel] = totals.get(rel, 0.0) + float(data.get("score") or 0.0)
    ranked = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    return [{"file": rel, "score": round(score, 4)} for rel, score in ranked[:20] if score > 0]


def _load_state(root: Path) -> dict[str, Any]:
    path = root / "logs" / "intent_file_memory.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(data, dict) and data.get("schema") == SCHEMA:
                data.setdefault("intent_keys", {})
                return data
        except Exception:
            pass
    return {"schema": SCHEMA, "created_at": _now(), "updated_at": _now(), "intent_keys": {}}


def _rel(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _tokens(text: Any) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower())
        if len(token) >= 3 and token not in {"the", "and", "for", "with", "that", "this", "from", "into"}
    ]


def _dedupe(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["learn_intent_file_memory", "match_intent_file_memory", "render_intent_file_memory"]
