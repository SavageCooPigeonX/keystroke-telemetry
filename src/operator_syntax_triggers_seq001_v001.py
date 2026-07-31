"""Learn file wake triggers from operator language and file syntax."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STOP = {"the", "and", "for", "with", "that", "this", "from", "into", "over", "have", "has", "are", "was", "were"}
SCAN_DIRS = ("src", "scripts", "tests", "pigeon_compiler")

def match_operator_syntax_triggers(root: Path, text: str, *, intent_key: str = "", limit: int = 8) -> list[dict[str, Any]]:
    root = Path(root)
    state = _load_state(root)
    records = _records(root, state)
    query = _tokens(" ".join([text, intent_key]))
    if not query:
        return []
    rarity = _rarity(records)
    rows = []
    for rel, record in records.items():
        tokens = set(record.get("tokens") or [])
        overlap = sorted(tokens & set(query))
        if not overlap:
            continue
        learned = set(record.get("learned_operator_tokens") or [])
        syntax = set(record.get("syntax_tokens") or [])
        score = sum(rarity.get(tok, 1.0) for tok in overlap)
        score += len(set(overlap) & learned) * 1.8
        score += len(set(overlap) & syntax) * 0.55
        score += min(int(record.get("observations") or 0), 8) * 0.2
        rows.append({
            "file": rel,
            "score": round(score, 4),
            "matched_tokens": overlap[:12],
            "sources": _sources(overlap, learned, syntax),
            "observations": record.get("observations", 0),
            "numeric": _numeric(overlap),
        })
    rows.sort(key=lambda row: (row["score"], row["observations"]), reverse=True)
    return _select_with_low_touch(rows, max(1, int(limit or 8)))

def learn_operator_syntax_triggers(root: Path, graph: dict[str, Any] | None = None, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    state = _load_state(root)
    records = _records(root, state)
    graph = graph or {}
    touched = []
    for intent in graph.get("intents") or []:
        op_tokens = _tokens(" ".join([
            str(graph.get("prompt") or ""),
            str(intent.get("segment") or ""),
            str(intent.get("intent_key") or ""),
        ]))
        for rel in intent.get("files") or []:
            rel = str(rel or "").replace("\\", "/")
            if not rel or not (root / rel).exists():
                continue
            rec = records.setdefault(rel, _file_record(root, rel))
            rec["observations"] = int(rec.get("observations") or 0) + 1
            rec["learned_operator_tokens"] = sorted(set([*rec.get("learned_operator_tokens", []), *op_tokens]))[:220]
            rec["tokens"] = sorted(set([*rec.get("tokens", []), *op_tokens]))[:420]
            rec["updated_at"] = _now()
            touched.append(rel)
    state = {"schema": "operator_syntax_triggers/v1", "updated_at": _now(), "files": records}
    latest = {
        "schema": "operator_syntax_triggers_update/v1",
        "ts": state["updated_at"],
        "graph_id": graph.get("graph_id", ""),
        "files_touched": sorted(set(touched))[:40],
        "file_count": len(records),
        "low_touch_ready": sum(1 for row in records.values() if int(row.get("observations") or 0) == 0),
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "operator_syntax_triggers.json", state)
        _write_json(logs / "operator_syntax_triggers_latest.json", latest)
        _append_jsonl(logs / "operator_syntax_triggers_history.jsonl", latest)
        (logs / "operator_syntax_triggers.md").write_text(_render(records), encoding="utf-8")
    return latest

def _records(root: Path, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = dict(state.get("files") or {})
    for rel in _repo_files(root):
        records.setdefault(rel, _file_record(root, rel))
    return records

def _select_with_low_touch(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected = rows[: max(1, limit - 2)]
    seen = {row["file"] for row in selected}
    low_touch = [r for r in rows if int(r.get("observations") or 0) == 0 and r["file"] not in seen]
    for row in low_touch[: max(1, min(2, limit // 3))]:
        row["sources"] = [*row.get("sources", []), "low_touch_static_explore"]; selected.append(row); seen.add(row["file"])
    for row in rows:
        if len(selected) >= limit:
            break
        if row["file"] not in seen:
            selected.append(row); seen.add(row["file"])
    return selected[:limit]


def _file_record(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    syntax = _tokens(rel)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:32000]
    except Exception:
        text = ""
    for line in text.splitlines()[:320]:
        stripped = line.strip()
        if stripped.startswith(("def ", "class ", "import ", "from ", "#", '"""', "'''")):
            syntax.extend(_tokens(stripped))
    syntax = sorted(set(syntax))[:260]
    return {
        "file": rel,
        "syntax_tokens": syntax,
        "learned_operator_tokens": [],
        "tokens": syntax,
        "observations": 0,
        "numeric_signature": _numeric(syntax),
        "created_at": _now(),
        "updated_at": _now(),
    }


def _repo_files(root: Path) -> list[str]:
    out = []
    for folder in SCAN_DIRS:
        base = root / folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".js", ".jsx", ".ts", ".tsx", ".ps1"}:
                if "__pycache__" not in path.parts and "node_modules" not in path.parts:
                    out.append(path.relative_to(root).as_posix())
    return sorted(out)[:900]


def _rarity(records: dict[str, dict[str, Any]]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for record in records.values():
        for tok in set(record.get("tokens") or []):
            counts[tok] = counts.get(tok, 0) + 1
    total = max(len(records), 1)
    return {tok: max(0.25, total / (count + 5)) for tok, count in counts.items()}


def _sources(overlap: list[str], learned: set[str], syntax: set[str]) -> list[str]:
    out = []
    if set(overlap) & learned:
        out.append("learned_operator_syntax")
    if set(overlap) & syntax:
        out.append("file_static_syntax")
    return out or ["token_overlap"]


def _numeric(tokens: list[str]) -> dict[str, Any]:
    bins = [0] * 16
    for tok in tokens:
        bins[int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:2], 16) % len(bins)] += 1
    return {"bins": bins, "token_count": len(tokens)}


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z0-9]+", str(text).replace("_", " ").lower())
    return [tok for tok in raw if len(tok) > 2 and tok not in STOP]


def _render(records: dict[str, dict[str, Any]]) -> str:
    ranked = sorted(records.values(), key=lambda row: (int(row.get("observations") or 0), row.get("file", "")), reverse=True)
    lines = ["# Operator Syntax Triggers", "", f"- files: `{len(records)}`", ""]
    for row in ranked[:80]:
        learned = ", ".join((row.get("learned_operator_tokens") or [])[:12])
        syntax = ", ".join((row.get("syntax_tokens") or [])[:12])
        lines.extend([f"## {row.get('file')}", "", f"- observations: `{row.get('observations', 0)}`", f"- learned: `{learned or 'none'}`", f"- syntax: `{syntax}`", ""])
    return "\n".join(lines)


def _load_state(root: Path) -> dict[str, Any]:
    try:
        return json.loads((root / "logs" / "operator_syntax_triggers.json").read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {"schema": "operator_syntax_triggers/v1", "files": {}}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
