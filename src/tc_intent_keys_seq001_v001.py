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
