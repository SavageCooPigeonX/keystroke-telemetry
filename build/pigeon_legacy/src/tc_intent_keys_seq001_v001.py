"""Manifest-backed intent key generation for thought completer.

Turns a prompt fragment into:
    scope:verb:target:scale

This is intentionally deterministic. It is the core that UI/popup/composer
surfaces can call without depending on Gemini, DeepSeek, or a live window.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tc_intent_key_io_seq001_v001 import write_outputs
from src.tc_semantic_profile_seq001_v001 import log_semantic_profile_event

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "about", "because",
    "intent", "key", "keys", "generation", "generate", "agent", "part",
}
VERBS = {
    "patch": {"fix", "patch", "repair", "bug", "broken", "working"},
    "build": {"build", "create", "add", "ship", "implement", "wire"},
    "test": {"test", "audit", "verify", "check", "validate"},
    "refactor": {"refactor", "split", "isolate", "extract", "rewrite"},
    "route": {"route", "match", "select", "dispatch", "encode", "manage"},
    "document": {"doc", "docs", "document", "manifest", "spec"},
}
PHRASE_TARGETS = [
    ("operator profile", "operator_profile"),
    ("operator model", "operator_profile"),
    ("pause analysis", "pause_analysis"),
    ("intent graph", "intent_graph"),
    ("file matching", "file_matching"),
    ("numerically matched", "semantic_numeric_file_matching"),
    ("semantically", "semantic_numeric_file_matching"),
    ("semantic numeric", "semantic_numeric_file_matching"),
    ("numeric file", "numeric_file_encoding"),
    ("neumeric file", "numeric_file_encoding"),
    ("numeric encoding", "numeric_encoding"),
    ("structured intent", "structured_intent_extraction"),
    ("intent extraction", "structured_intent_extraction"),
    ("thought completer", "thought_completer"),
    ("prompt box", "prompt_box"),
    ("intent manager", "intent_manager"),
    ("intent key", "intent_key"),
    ("manifest", "manifest"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> list[str]:
    text = text.replace("_", " ")
    return [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2 and t not in STOP]


def _slug(text: str, fallback: str = "work") -> str:
    words = _tokens(text)
    if not words:
        return fallback
    return "_".join(words[:4])[:48]


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def discover_manifests(root: Path, limit: int = 500) -> list[dict[str, Any]]:
    root = Path(root)
    out: list[dict[str, Any]] = []
    for path in sorted(root.rglob("MANIFEST.md"))[:limit]:
        try:
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        parent = path.parent.relative_to(root).as_posix()
        scope = "root" if parent == "." else parent
        first_heading = next((ln.strip("# ").strip() for ln in text.splitlines() if ln.startswith("#")), scope)
        haystack = f"{rel} {scope} {first_heading} {text[:4000]}"
        out.append({
            "path": rel,
            "scope": scope,
            "title": first_heading[:120],
            "tokens": sorted(set(_tokens(haystack))),
            "excerpt": "\n".join(text.splitlines()[:18])[:1200],
        })
    return out


def _score_manifest(prompt_tokens: set[str], manifest: dict[str, Any]) -> float:
    mtoks = set(manifest.get("tokens") or [])
    if not prompt_tokens or not mtoks:
        return 0.0
    overlap = prompt_tokens & mtoks
    path_tokens = set(_tokens(str(manifest.get("scope", ""))))
    path_boost = 0.08 * len(prompt_tokens & path_tokens)
    return round((len(overlap) / max(len(prompt_tokens), 1)) + path_boost, 4)


def _choose_verb(prompt_tokens: set[str]) -> str:
    best = ("route", 0)
    for verb, words in VERBS.items():
        hits = len(prompt_tokens & words)
        if hits > best[1]:
            best = (verb, hits)
    return best[0]


def _choose_scale(prompt_tokens: set[str]) -> str:
    if prompt_tokens & {"audit", "read", "inspect", "review"}:
        return "read"
    if prompt_tokens & {"rewrite", "refactor", "split", "major", "migration"}:
        return "major"
    if prompt_tokens & {"fix", "patch", "wire", "add", "implement", "encode", "encoding", "log", "save", "persist"}:
        return "patch"
    return "minor"


def _choose_target(prompt: str, scope: str) -> str:
    lower = prompt.lower().replace("-", " ")
    for phrase, target in PHRASE_TARGETS:
        if phrase in lower:
            return target
    explicit = re.findall(r"(?:src|client|pigeon_compiler|pigeon_brain)/[a-zA-Z0-9_./-]+", prompt)
    if explicit:
        return _slug(Path(explicit[0]).stem)
    return _slug(prompt.replace(scope, ""))


def _scope_warnings(top: list[dict[str, Any]], confidence: float) -> list[str]:
    if confidence < 0.12:
        return ["low_manifest_confidence"]
    scopes = [m["scope"] for m in top[:3] if m.get("score", 0) >= max(confidence - 0.05, 0)]
    roots = {s.split("/", 1)[0] for s in scopes if s and s != "root"}
    if len(roots) > 1:
        return ["multiple_scope_candidates"]
    return []


def generate_intent_key(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    emit_prompt_box: bool = True,
    inject: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    prompt = str(prompt or "").strip()
    p_tokens = set(_tokens(" ".join([prompt, *(deleted_words or [])])))
    manifests = discover_manifests(root)
    scored = [{**m, "score": _score_manifest(p_tokens, m)} for m in manifests]
    scored.sort(key=lambda m: (-m["score"], m["path"]))
    best = scored[0] if scored else {"scope": "root", "path": "MANIFEST.md", "score": 0.0, "excerpt": ""}
    confidence = float(best.get("score", 0.0))
    warnings = _scope_warnings(scored, confidence)
    void = confidence < 0.06 or "low_manifest_confidence" in warnings
    verb = _choose_verb(p_tokens)
    scale = _choose_scale(p_tokens)
    target = _choose_target(prompt, str(best.get("scope", "root")))
    scope = str(best.get("scope") or "root")
    intent_key = f"{scope}:{verb}:{target}:{scale}"
    digest = hashlib.sha256(f"{intent_key}|{prompt}".encode("utf-8")).hexdigest()[:16]
    semantic_profile = log_semantic_profile_event(
        root,
        prompt,
        source="intent_key_generator",
        intent_key=intent_key,
        deleted_words=deleted_words or [],
    )
    record = {
        "ts": _utc_now(),
        "intent_id": f"intent-key:{digest}",
        "prompt": prompt,
        "deleted_words": deleted_words or [],
        "intent_key": intent_key,
        "scope": scope,
        "verb": verb,
        "target": target,
        "scale": scale,
        "confidence": confidence,
        "void": void,
        "void_reason": ";".join(warnings) if void else "",
        "scope_warnings": warnings,
        "manifest_path": str(best.get("path", "MANIFEST.md")),
        "manifest_excerpt": str(best.get("excerpt", "")),
        "semantic_profile": semantic_profile,
        "candidates": [{"scope": m["scope"], "path": m["path"], "score": m["score"]} for m in scored[:6]],
        "prompt_box": {"status": "skipped", "reason": "void"} if void else {},
    }
    logs = root / "logs"
    _append_jsonl(logs / "intent_keys.jsonl", record)
    _write_json(logs / "manifest_index.json", {"ts": record["ts"], "manifests": scored[:80]})
    return write_outputs(root, record, emit_prompt_box=emit_prompt_box, inject=inject)


def generate_intent_graph(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    limit: int = 5,
    numeric_files: list[dict[str, Any]] | None = None,
    context_selection: dict[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Generate multiple structured intent keys from one messy operator prompt.

    This is the thought-completer shape: a pause should not collapse the whole
    buffer into one key. It should expose the handful of moves the operator is
    circling, with each move bound to manifests and candidate files.
    """
    root = Path(root)
    prompt = str(prompt or "").strip()
    deleted = deleted_words or []
    manifests = discover_manifests(root)
    numeric = list(numeric_files or [])
    context_files = list((context_selection or {}).get("files") or [])
    node_matches = _match_nodes(root, prompt)
    segments = _split_intent_segments(prompt, limit=limit)
    if prompt and not segments:
        segments = [prompt]
    p_tokens = set(_tokens(" ".join([prompt, *deleted])))
    graph_id = hashlib.sha256(f"{prompt}|{' '.join(deleted)}".encode("utf-8")).hexdigest()[:16]
    intents = []
    for index, segment in enumerate(segments[: max(1, int(limit or 5))], 1):
        seg_tokens = set(_tokens(" ".join([segment, *deleted])))
        scored = [{**m, "score": _score_manifest(seg_tokens or p_tokens, m)} for m in manifests]
        scored.sort(key=lambda m: (-m["score"], m["path"]))
        best = scored[0] if scored else {"scope": "root", "path": "MANIFEST.md", "score": 0.0, "excerpt": ""}
        confidence = float(best.get("score", 0.0))
        verb = _choose_verb(seg_tokens or p_tokens)
        scale = _choose_scale(seg_tokens or p_tokens)
        target = _choose_target(segment, str(best.get("scope", "root")))
        scope = str(best.get("scope") or "root")
        intent_key = f"{scope}:{verb}:{target}:{scale}"
        learned_files = _match_intent_file_memory(root, segment, intent_key)
        files = _intent_files(root, segment, scored[:6], numeric, context_files, node_matches, learned_files)
        intents.append({
            "index": index,
            "segment": segment,
            "intent_key": intent_key,
            "scope": scope,
            "verb": verb,
            "target": target,
            "scale": scale,
            "confidence": confidence,
            "void": confidence < 0.06,
            "manifest_path": str(best.get("path", "MANIFEST.md")),
            "files": files,
            "learned_files": learned_files[:6],
            "numeric_files": _compact_numeric_files(numeric),
            "why": _intent_why(segment, files, confidence),
            "candidates": [{"scope": m["scope"], "path": m["path"], "score": m["score"]} for m in scored[:4]],
        })
    clearing = _context_clearing_pass(root, prompt, intents, numeric, context_files)
    graph = {
        "schema": "intent_graph/v1",
        "ts": _utc_now(),
        "graph_id": f"intent-graph:{graph_id}",
        "prompt": prompt,
        "deleted_words": deleted,
        "intent_count": len(intents),
        "intents": intents,
        "context_clearing_pass": clearing,
        "intent_node_matches": node_matches,
        "operator_model_use": "pause-time thought completion should model repeated operator intent, not merely complete text",
        "paths": {
            "latest": "logs/intent_graph_latest.json",
            "history": "logs/intent_graph_history.jsonl",
            "context": "logs/intent_graph_context.md",
        },
    }
    graph["intent_file_memory"] = _learn_intent_file_memory(root, graph, write=write)
    graph["intent_nodes"] = _accumulate_nodes(root, graph, write=write)
    if write:
        logs = root / "logs"
        _write_json(logs / "intent_graph_latest.json", graph)
        _append_jsonl(logs / "intent_graph_history.jsonl", graph)
        (logs / "intent_graph_context.md").write_text(render_intent_graph(graph) + "\n", encoding="utf-8")
    return graph


def render_intent_graph(graph: dict[str, Any]) -> str:
    lines = [
        "## Intent Graph",
        "",
        f"**GRAPH:** `{graph.get('graph_id', 'none')}`",
        f"**PROMPT:** `{_ascii(str(graph.get('prompt') or '')[:240])}`",
        f"**INTENTS:** `{graph.get('intent_count', 0)}`",
        "",
    ]
    for item in graph.get("intents") or []:
        files = ", ".join(item.get("files") or []) or "none"
        lines.extend([
            f"{item.get('index')}. `{_ascii(item.get('intent_key'))}`",
            f"   - segment: {_ascii(item.get('segment'))}",
            f"   - files: `{_ascii(files)}`",
            f"   - why: {_ascii(item.get('why'))}",
        ])
        learned = item.get("learned_files") or []
        if learned:
            lines.append(
                f"   - learned: `{_ascii(', '.join(row.get('file', '') for row in learned[:5]))}`"
            )
    clearing = graph.get("context_clearing_pass") or {}
    if clearing:
        lines.extend([
            "",
            "## Self-Clearing Context Window",
            "",
            f"**BUDGET:** `{clearing.get('token_budget', 0)}` tokens",
            f"**SELECTED:** `{len(clearing.get('selected_files') or [])}`",
            f"**DERANKED:** `{len(clearing.get('deranked_files') or [])}`",
            "",
        ])
        for item in (clearing.get("selected_files") or [])[:12]:
            lines.append(
                f"- keep `{_ascii(item.get('file'))}` score `{item.get('final_score')}` - "
                f"{_ascii('; '.join(item.get('reasons') or [])[:180])}"
            )
        if clearing.get("deranked_files"):
            lines.extend(["", "### Deranked", ""])
            for item in (clearing.get("deranked_files") or [])[:12]:
                lines.append(
                    f"- drop `{_ascii(item.get('file'))}` score `{item.get('final_score')}` - "
                    f"{_ascii('; '.join(item.get('derank_reasons') or [])[:180])}"
                )
    node_matches = graph.get("intent_node_matches") or []
    if node_matches:
        lines.extend(["", "## Intent Node Memory", ""])
        for node in node_matches[:8]:
            lines.append(
                f"- `{_ascii(node.get('node_key'))}` score `{node.get('score')}` "
                f"files `{_ascii(', '.join(node.get('dominant_files') or [])[:180])}`"
            )
    return "\n".join(lines)


def _split_intent_segments(prompt: str, limit: int = 5) -> list[str]:
    text = re.sub(r"\s+", " ", str(prompt or "")).strip()
    if not text:
        return []
    split_pattern = (
        r"\s*(?:[.;?]|(?:\s+-\s+)|(?:\s+/\s+)|"
        r"\b(?:but|also|then|so|because|which|maybe|basically|baisically|right now|"
        r"part two|what i want|there should|this means|that means)\b)\s*"
    )
    raw = [part.strip(" ,:-") for part in re.split(split_pattern, text, flags=re.I) if part.strip(" ,:-")]
    segments: list[str] = []
    for part in raw:
        if len(_tokens(part)) < 3:
            continue
        segments.append(_clean_segment(part))
    if len(segments) < limit:
        topics = _topic_segments(text)
        segments.extend(topics)
    deduped = _dedupe_text(segments)
    ranked = sorted(enumerate(deduped), key=lambda pair: (-_segment_score(pair[1]), pair[0]))
    return [segment for _idx, segment in ranked[: max(1, int(limit or 5))]]


def _segment_score(segment: str) -> float:
    toks = set(_tokens(segment))
    score = min(len(toks), 12) * 0.1
    weighted = [
        ({"operator", "profile", "fingerprint", "model"}, 2.6),
        ({"pause", "pauses", "paused", "analysis", "complete", "completion"}, 2.3),
        ({"intent", "graph", "graphs"}, 2.4),
        ({"file", "files", "matching", "matched"}, 2.2),
        ({"numeric", "neumeric", "numerically", "semantically", "encoding"}, 2.5),
        ({"structured", "extraction", "extractions"}, 2.3),
        ({"thought", "completer"}, 1.2),
    ]
    for words, weight in weighted:
        hits = len(toks & words)
        if hits:
            score += weight * min(hits, 2)
    if toks <= {"knows", "your", "prompt", "intent"}:
        score -= 2.0
    return score


def _topic_segments(text: str) -> list[str]:
    lower = text.lower()
    topics = [
        ("operator profile", "build a durable operator profile from prompt history and profile facts"),
        ("pause", "complete paused thoughts with actual analysis before model handoff"),
        ("intent graph", "derive an intent graph from structured intent key extraction"),
        ("file matching", "match extracted intent keys to files using manifest and numeric file identity"),
        ("numeric", "use semantic numeric file encoding so prompt intent wakes the right files"),
        ("structured intent", "emit several structured intent extractions for one prompt instead of one collapsed key"),
    ]
    return [value for needle, value in topics if needle in lower]


def _clean_segment(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:260]


def _dedupe_text(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        key = " ".join(_tokens(value)[:10])
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _intent_files(
    root: Path,
    segment: str,
    manifest_candidates: list[dict[str, Any]],
    numeric_files: list[dict[str, Any]],
    context_files: list[dict[str, Any]],
    node_matches: list[dict[str, Any]] | None = None,
    learned_files: list[dict[str, Any]] | None = None,
) -> list[str]:
    out = []
    out.extend(_learned_file_paths(learned_files or []))
    out.extend(_node_match_files(node_matches or []))
    out.extend(_heuristic_files(root, segment))
    out.extend(_numeric_file_paths(root, context_files))
    out.extend(_numeric_file_paths(root, numeric_files))
    for manifest in manifest_candidates[:3]:
        path = str(manifest.get("path") or "")
        if path:
            out.append(path)
    return _dedupe_text(out)[:8]


def _match_nodes(root: Path, prompt: str) -> list[dict[str, Any]]:
    try:
        from src.intent_nodes_seq001_v001 import match_intent_nodes
        return match_intent_nodes(root, prompt, limit=5)
    except Exception:
        return []


def _accumulate_nodes(root: Path, graph: dict[str, Any], write: bool) -> dict[str, Any]:
    try:
        from src.intent_nodes_seq001_v001 import accumulate_intent_nodes
        return accumulate_intent_nodes(root, graph, write=write)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _match_intent_file_memory(root: Path, segment: str, intent_key: str) -> list[dict[str, Any]]:
    try:
        from src.tc_intent_file_memory_seq001_v001 import match_intent_file_memory
        return match_intent_file_memory(root, segment, intent_key=intent_key, limit=6)
    except Exception:
        return []


def _learn_intent_file_memory(root: Path, graph: dict[str, Any], write: bool) -> dict[str, Any]:
    try:
        from src.tc_intent_file_memory_seq001_v001 import learn_intent_file_memory
        return learn_intent_file_memory(root, graph, write=write)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _learned_file_paths(learned_files: list[dict[str, Any]]) -> list[str]:
    out = []
    for item in learned_files[:8]:
        rel = str(item.get("file") or item.get("path") or item.get("name") or "").strip()
        if rel:
            out.append(rel.replace("\\", "/"))
    return out


def _node_match_files(node_matches: list[dict[str, Any]]) -> list[str]:
    out = []
    for node in node_matches[:4]:
        out.extend(str(item) for item in (node.get("dominant_files") or [])[:5])
    return out


def _heuristic_files(root: Path, text: str) -> list[str]:
    haystack = text.lower()
    hints = [
        (
            {"thought", "completer", "pause", "paused", "completion", "popup"},
            [
                "src/thought_completer.py",
                "src/tc_prompt_composer_seq001_v001.py",
                "src/tc_buffer_watcher_seq001_v001.py",
                "src/tc_popup_seq001_v004*.py",
            ],
        ),
        (
            {"operator", "profile", "semantic", "fingerprint", "model"},
            [
                "src/tc_semantic_profile_seq001_v001.py",
                "src/ai_fingerprint_operator_seq001_v001.py",
            ],
        ),
        (
            {"intent", "key", "keys", "extraction", "structured", "graph"},
            [
                "src/tc_intent_keys_seq001_v001.py",
                "src/intent_loop_closer_seq001_v001.py",
            ],
        ),
        (
            {"file", "files", "matching", "matched", "numeric", "neumeric", "encoding"},
            [
                "src/intent_numeric_seq001*.py",
                "src/tc_context_agent_seq001_v004*.py",
                "codex_compat.py",
            ],
        ),
        (
            {"analysis", "sim", "sims", "simulation"},
            [
                "src/tc_sim_engine_seq001_v004*.py",
                "src/file_self_sim_learning_seq001_v001.py",
            ],
        ),
    ]
    out = []
    for terms, candidates in hints:
        if any(term in haystack for term in terms):
            out.extend(_existing_candidates(root, candidates))
    return out


def _existing_candidates(root: Path, candidates: list[str]) -> list[str]:
    out = []
    for candidate in candidates:
        if "*" in candidate:
            out.extend(path.relative_to(root).as_posix() for path in sorted(root.glob(candidate)) if path.is_file())
            continue
        if (root / candidate).exists():
            out.append(candidate)
    return out


def _numeric_file_paths(root: Path, files: list[dict[str, Any]]) -> list[str]:
    out = []
    for item in files[:8]:
        name = str(item.get("path") or item.get("name") or "").strip()
        if not name:
            continue
        if (root / name).exists():
            out.append(name.replace("\\", "/"))
            continue
        if "/" in name or "\\" in name:
            out.append(name.replace("\\", "/"))
            continue
        stem = Path(name).stem
        matches = sorted((root / "src").glob(f"**/{stem}.py")) if (root / "src").exists() else []
        if matches:
            out.append(matches[0].relative_to(root).as_posix())
            continue
        doc_matches = sorted(
            path for path in (root / "docs").glob("**/*")
            if path.is_file() and path.stem.lower() == stem.lower()
        ) if (root / "docs").exists() else []
        if doc_matches:
            out.append(doc_matches[0].relative_to(root).as_posix())
            continue
        out.append(name)
    return out


def _compact_numeric_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": item.get("path") or item.get("name"), "score": item.get("score", 0)}
        for item in files[:6]
        if item.get("path") or item.get("name")
    ]


def _intent_why(segment: str, files: list[str], confidence: float) -> str:
    if files:
        return f"segment matched {len(files)} file signal(s); manifest confidence {confidence:.3f}"
    return f"segment produced an intent key but needs better file history; manifest confidence {confidence:.3f}"


def _context_clearing_pass(
    root: Path,
    prompt: str,
    intents: list[dict[str, Any]],
    numeric_files: list[dict[str, Any]],
    context_files: list[dict[str, Any]],
    token_budget: int = 18000,
) -> dict[str, Any]:
    prompt_tokens = set(_tokens(prompt))
    numeric_names = {_file_ref_name(item) for item in numeric_files}
    context_names = {_file_ref_name(item) for item in context_files}
    records: dict[str, dict[str, Any]] = {}
    for intent in intents:
        segment_tokens = set(_tokens(intent.get("segment", "")))
        for rank, file_name in enumerate(intent.get("files") or []):
            rel = str(file_name or "").replace("\\", "/")
            if not rel:
                continue
            rec = records.setdefault(rel, {
                "file": rel,
                "score": 0.0,
                "supporting_intents": [],
                "deranked_by": [],
                "reasons": [],
                "derank_reasons": [],
            })
            path_tokens = set(_tokens(rel))
            overlap = segment_tokens & path_tokens
            points = max(0.15, 1.4 - rank * 0.12)
            if overlap:
                points += min(len(overlap), 4) * 0.55
                rec["reasons"].append(f"{intent.get('target')} promoted path tokens {', '.join(sorted(overlap)[:4])}")
            else:
                points -= 0.35
                rec["deranked_by"].append(intent.get("intent_key"))
                rec["derank_reasons"].append(f"{intent.get('target')} saw no path-token overlap")
            if (root / rel).exists():
                points += 0.45
            elif rel in numeric_names or Path(rel).stem in numeric_names:
                points -= 1.6
                rec["unresolved"] = True
                rec["derank_reasons"].append("numeric prediction did not resolve to an existing repo file")
            else:
                points -= 1.0
                rec["unresolved"] = True
                rec["derank_reasons"].append("candidate did not resolve to an existing repo file")
            if rel in context_names:
                points += 0.45
                rec["reasons"].append("context selector independently selected it")
            if rel in numeric_names or Path(rel).stem in numeric_names:
                points += 0.25
                rec["reasons"].append("numeric surface nominated it")
            if not (path_tokens & prompt_tokens) and not rel.lower().endswith("manifest.md"):
                points -= 0.25
                rec["derank_reasons"].append("file identity is weak against the full prompt")
            rec["score"] += points
            rec["supporting_intents"].append(intent.get("intent_key"))
    rows = []
    for rec in records.values():
        rec["supporting_intents"] = _dedupe_text([str(x) for x in rec.get("supporting_intents") or []])
        rec["deranked_by"] = _dedupe_text([str(x) for x in rec.get("deranked_by") or []])
        rec["reasons"] = _dedupe_text([str(x) for x in rec.get("reasons") or []])[:6]
        rec["derank_reasons"] = _dedupe_text([str(x) for x in rec.get("derank_reasons") or []])[:6]
        rec["estimated_tokens"] = _estimate_tokens(root, rec["file"])
        rec["final_score"] = round(float(rec.get("score") or 0.0), 4)
        rows.append(rec)
    rows.sort(key=lambda item: (item["final_score"], len(item["supporting_intents"])), reverse=True)
    selected = []
    deranked = []
    total = 0
    for item in rows:
        if item.get("unresolved"):
            deranked.append({**item, "decision": "deranked"})
            continue
        if item["final_score"] < 0.65:
            deranked.append({**item, "decision": "deranked"})
            continue
        tokens = int(item.get("estimated_tokens") or 0)
        if selected and total + tokens > token_budget:
            deranked.append({**item, "decision": "deranked", "derank_reasons": [*item.get("derank_reasons", []), "forward context token budget"]})
            continue
        selected.append({**item, "decision": "selected"})
        total += tokens
    return {
        "schema": "self_clearing_context/v1",
        "mode": "sim_votes_promote_and_derank_files_before_prompt_handoff",
        "token_budget": token_budget,
        "total_estimated_tokens": total,
        "selected_files": selected[:12],
        "deranked_files": deranked[:40],
        "context_window_files": [item["file"] for item in selected[:12]],
    }


def _file_ref_name(item: dict[str, Any]) -> str:
    return str(item.get("path") or item.get("name") or "").replace("\\", "/")


def _estimate_tokens(root: Path, rel: str) -> int:
    path = root / str(rel)
    if not path.exists() or not path.is_file():
        return 0
    try:
        return max(1, len(path.read_text(encoding="utf-8", errors="ignore")) // 4)
    except Exception:
        return 0


def _ascii(value: Any) -> str:
    return str(value).encode("ascii", errors="replace").decode("ascii")


__all__ = ["generate_intent_key", "generate_intent_graph", "render_intent_graph"]
