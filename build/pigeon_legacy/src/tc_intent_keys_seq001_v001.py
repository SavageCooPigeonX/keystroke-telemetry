"""Manifest-backed intent key generation for thought completer.

Turns a prompt fragment into:
    scope:verb:target:scale

This is intentionally deterministic. It is the core that UI/popup/composer
surfaces can call without depending on Gemini, DeepSeek, or a live window.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tc_intent_file_memory_seq001_v001 import (
    match_intent_file_memory,
    remember_intent_files,
)
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
    ("proper intent key mapping", "intent_key_mapping"),
    ("promper intent key mapping", "intent_key_mapping"),
    ("intent key mapping", "intent_key_mapping"),
    ("intent mapping", "intent_key_mapping"),
    ("operator profile", "operator_profile"),
    ("intent graph", "intent_graph"),
    ("intent graphs", "intent_graph"),
    ("structured intent", "structured_intent"),
    ("file matching", "file_matching"),
    ("match intent keys", "file_matching"),
    ("numeric encoding", "numeric_encoding"),
    ("prompt history", "prompt_history"),
    ("file comments", "file_comments"),
    ("context select", "context_select"),
    ("domain manifest", "domain_manifest"),
    ("intent profile", "intent_profile"),
    ("intent profiles", "intent_profile"),
    ("prompt box", "prompt_box"),
    ("intent manager", "intent_manager"),
    ("intent key", "intent_key"),
    ("manifest", "manifest"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> list[str]:
    lower = str(text or "").lower().replace("_", " ")
    compound_tokens = []
    phrase_tokens = {
        "intent key": "intent_key",
        "intent keys": "intent_key",
        "intent map": "intent_map",
        "intent mapping": "intent_key_mapping",
        "intent key mapping": "intent_key_mapping",
        "proper intent key mapping": "intent_key_mapping",
        "promper intent key mapping": "intent_key_mapping",
        "context select": "context_select",
        "domain manifest": "domain_manifest",
        "file pairing": "file_pairing",
        "file pairings": "file_pairing",
        "file comments": "file_comments",
        "prompt history": "prompt_history",
    }
    for phrase, token in phrase_tokens.items():
        if phrase in lower:
            compound_tokens.append(token)
    base_tokens = [t for t in re.findall(r"[a-zA-Z0-9]+", lower) if len(t) > 2 and t not in STOP]
    return [*base_tokens, *compound_tokens]


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
        tokens = sorted(set(_tokens(haystack)))
        out.append({
            "path": rel,
            "scope": scope,
            "title": first_heading[:120],
            "tokens": tokens,
            "domain_id": _file_domain(rel, set(tokens)),
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
    matches: list[tuple[int, int, str]] = []
    for phrase, target in PHRASE_TARGETS:
        if phrase in lower:
            matches.append((lower.rfind(phrase), len(phrase), target))
    if matches:
        specific = [
            row for row in matches
            if row[2] not in {"thought_completer", "intent_key", "manifest"}
        ]
        pool = specific or matches
        pool.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return pool[0][2]
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


DOMAIN_HINTS = {
    "project.keystroke_telemetry": {
        "terms": {
            "keystroke", "typing", "deleted", "deletion", "context", "select",
            "telemetry", "thought", "completer", "prompt", "intent", "numeric",
            "profile", "manifest", "file", "files", "pairing", "learning",
        },
        "privacy": "local-first",
    },
    "project.hush": {
        "terms": {"hush", "shard", "shards", "memory", "writeback", "recall"},
        "privacy": "mixed",
    },
    "project.irt": {
        "terms": {"irt", "artifact", "probe", "field", "pulse", "entity"},
        "privacy": "project-with-personal-signals",
    },
    "project.pigeon_code_compiler": {
        "terms": {"pigeon", "compiler", "compile", "rename", "registry", "import"},
        "privacy": "project",
    },
    "personal.operator_profile": {
        "terms": {"personal", "operator", "profile", "routine", "name", "style"},
        "privacy": "private",
    },
    "cross_domain.audit": {
        "terms": {"audit", "security", "origin", "push", "pr", "github", "test"},
        "privacy": "project-with-sensitive-logs",
    },
}
DOMAIN_ANCHORS = {
    "project.hush": {"hush", "shard", "shards", "writeback", "recall"},
    "project.irt": {"irt", "artifact", "probe", "field", "pulse", "entity"},
    "project.pigeon_code_compiler": {"pigeon", "compiler", "compile"},
    "personal.operator_profile": {"operator", "personal", "profile"},
    "cross_domain.audit": {"audit", "origin", "push", "pr", "github", "security"},
}
DOMAIN_PATH_PREFIXES = {
    "project.keystroke_telemetry": (
        "src/tc_",
        "src/intent_",
        "src/context_",
        "client/",
        "vscode-extension/",
    ),
    "project.hush": (
        "hush/",
        "hush_runtime/",
        "hush_memory/",
    ),
    "project.irt": (
        "src/irt_",
        "irt/",
        "artifacts/",
    ),
    "project.pigeon_code_compiler": (
        "pigeon_compiler/",
        "pigeon_brain/",
    ),
    "cross_domain.audit": (
        ".github/",
        "documentation/manifests/",
        "docs/push_narratives/",
    ),
}
DOMAIN_EXTERNAL_PREFIXES = {
    "project.hush": (
        "hush/",
        "hush_runtime/",
        "hush_memory/",
        "listen/",
    ),
    "project.irt": (
        "api/",
        "directory/",
        "production_auditor/",
        "artifact_storage/",
    ),
    "project.pigeon_code_compiler": (
        "pigeon_compiler/",
    ),
}
STALE_CONTEXT_PARTS = {
    "docs/push_narratives",
    "pigeon_compiler/bones",
    "documentation/manifests",
}
DOC_SUPPORT_TOKENS = {
    "audit", "architecture", "architerchture", "doc", "docs",
    "document", "manifest", "policy", "plan", "read", "review", "spec", "system",
    "systems",
}
EXTERNAL_PROJECT_DOMAINS = {
    "project.hush",
    "project.irt",
    "project.pigeon_code_compiler",
}

GRAPH_SPLIT_RE = re.compile(
    r"\s*(?:[,;]|\bthen\b|\bplus\b|\band\s+(?="
    r"build|complete|get|match|use|route|update|write|run|seed|make|audit|fix|"
    r"implement|create|add|select|compile|learn|pair"
    r"\b))\s*",
    re.I,
)

SOURCE_SUFFIXES = {".py", ".md", ".js", ".jsx", ".ts", ".tsx", ".json"}
SOURCE_SKIP_PARTS = {
    ".git", ".pytest_cache", "__pycache__", "node_modules", "logs",
    "build", "dist", ".venv", "venv",
}


def _safe_key(text: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(text or "").strip())
    key = re.sub(r"_+", "_", key).strip("_")
    return key[:180] or "unknown"


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(str(prompt or "").encode("utf-8", errors="replace")).hexdigest()[:16]


def _as_posix(path: Path) -> str:
    return path.resolve().as_posix()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _resolve_context_path(root: Path, rel: str) -> Path:
    path = Path(str(rel or ""))
    if path.is_absolute():
        return path
    return Path(root) / path


def _split_prompt(prompt: str, max_intents: int = 8) -> list[str]:
    text = re.sub(r"\s+", " ", str(prompt or "").strip())
    if not text:
        return []
    parts = [part.strip(" .:-") for part in GRAPH_SPLIT_RE.split(text)]
    out = []
    seen = set()
    for part in parts:
        if len(_tokens(part)) < 2:
            continue
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(part)
        if len(out) >= max_intents:
            break
    return out or [text]


def _select_domain(text: str, fallback_domain: str = "project.keystroke_telemetry") -> dict[str, Any]:
    toks = set(_tokens(text))
    rows = []
    for domain_id, spec in DOMAIN_HINTS.items():
        terms = set(spec["terms"])
        hits = sorted(toks & terms)
        anchors = DOMAIN_ANCHORS.get(domain_id, set())
        anchor_hits = sorted(toks & anchors)
        score = round(len(hits) / max(1, len(toks)) + (0.08 if hits else 0), 4)
        if anchors and not anchor_hits:
            score = 0.0
        rows.append({
            "domain_id": domain_id,
            "score": score,
            "matched_terms": hits,
            "anchor_terms": anchor_hits,
            "privacy": spec["privacy"],
        })
    rows.sort(key=lambda row: (-float(row["score"]), row["domain_id"]))
    primary = rows[0] if rows and rows[0]["score"] > 0 else {
        "domain_id": fallback_domain,
        "score": 0.0,
        "matched_terms": [],
        "privacy": DOMAIN_HINTS.get(fallback_domain, DOMAIN_HINTS["project.keystroke_telemetry"])["privacy"],
        "fallback": True,
    }
    return {
        "schema": "domain_selection/v1",
        "primary_domain": primary["domain_id"],
        "primary": primary,
        "secondary_domains": [row for row in rows[1:5] if row["score"] > 0],
        "scores": rows,
    }


def _default_domain_manifest(root: Path) -> dict[str, Any]:
    root = Path(root)
    root_abs = _as_posix(root)
    domains = []
    for domain_id, spec in DOMAIN_HINTS.items():
        roots = [{
            "root": root_abs,
            "source": "local_repo",
            "path_prefixes": list(DOMAIN_PATH_PREFIXES.get(domain_id, ())),
        }]
        external_root = os.environ.get("KEYSTROKE_EXTERNAL_PROJECT_ROOT", "").strip()
        if external_root and root.name.lower() == "keystroke-telemetry" and domain_id in DOMAIN_EXTERNAL_PREFIXES:
            roots.append({
                "root": _as_posix(Path(external_root)),
                "source": "external_project",
                "path_prefixes": list(DOMAIN_EXTERNAL_PREFIXES[domain_id]),
            })
        domains.append({
            "domain_id": domain_id,
            "terms": sorted(spec["terms"]),
            "anchors": sorted(DOMAIN_ANCHORS.get(domain_id, set())),
            "privacy": spec["privacy"],
            "roots": roots,
            "intent_profile_dir": "logs/intent_profiles",
        })
    return {
        "schema": "domain_manifest/v1",
        "root": root_abs,
        "domains": domains,
        "split_policy": "split when prompt segment domain differs, selected files exceed intent scope, or domain files are unavailable",
    }


def _merge_domain_manifest(default: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(override, dict) or override.get("schema") != "domain_manifest/v1":
        return default
    default_by_id = {row.get("domain_id"): row for row in default.get("domains") or []}
    merged = {**default, **{k: v for k, v in override.items() if k != "domains"}}
    domains = []
    for row in override.get("domains") or []:
        domain_id = row.get("domain_id")
        if not domain_id:
            continue
        base = default_by_id.get(domain_id, {})
        merged_row = {**base, **row}
        roots_by_key = {}
        for spec in [*(base.get("roots") or []), *(row.get("roots") or [])]:
            if not isinstance(spec, dict) or not spec.get("root"):
                continue
            key = (str(spec.get("root")), str(spec.get("source", "")))
            roots_by_key[key] = {**roots_by_key.get(key, {}), **spec}
        merged_row["roots"] = list(roots_by_key.values())
        domains.append(merged_row)
        default_by_id.pop(domain_id, None)
    domains.extend(default_by_id.values())
    merged["domains"] = domains
    return merged


def _load_domain_manifest(root: Path) -> dict[str, Any]:
    root = Path(root)
    default = _default_domain_manifest(root)
    path = root / "logs" / "domain_manifest.json"
    if not path.exists():
        return default
    try:
        existing = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return default
    return _merge_domain_manifest(default, existing)


def _domain_rows(domain_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = domain_manifest.get("domains") if isinstance(domain_manifest, dict) else []
    return [row for row in rows or [] if isinstance(row, dict) and row.get("domain_id")]


def _write_domain_manifest(root: Path, domain_manifest: dict[str, Any]) -> dict[str, str]:
    root = Path(root)
    now = _utc_now()
    state = {**domain_manifest, "updated_at": now}
    domains = []
    for domain in _domain_rows(domain_manifest):
        row = {**domain}
        roots = []
        for spec in domain.get("roots") or []:
            if not isinstance(spec, dict) or not spec.get("root"):
                continue
            root_path = Path(str(spec["root"]))
            roots.append({
                **spec,
                "root": root_path.as_posix(),
                "exists": root_path.exists(),
            })
        row["roots"] = roots
        domains.append(row)
    state["domains"] = domains
    path = root / "logs" / "domain_manifest.json"
    _write_json(path, state)
    lines = [
        "# Domain Manifest",
        "",
        f"- updated_at: `{now}`",
        f"- root: `{state.get('root', _as_posix(root))}`",
        f"- split_policy: {state.get('split_policy', '')}",
        "",
    ]
    for domain in domains:
        lines.extend([
            f"## {domain.get('domain_id', '')}",
            "",
            f"- privacy: `{domain.get('privacy', '')}`",
            f"- intent_profile_dir: `{domain.get('intent_profile_dir', '')}`",
            f"- anchors: {', '.join(f'`{term}`' for term in domain.get('anchors') or [])}",
            "",
            "### Roots",
            "",
        ])
        for spec in domain.get("roots") or []:
            prefixes = ", ".join(f"`{prefix}`" for prefix in spec.get("path_prefixes") or [])
            lines.append(
                f"- `{spec.get('root', '')}` source=`{spec.get('source', '')}` "
                f"exists=`{bool(spec.get('exists'))}` prefixes={prefixes}"
            )
        lines.append("")
    md = root / "logs" / "domain_manifest.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("\n".join(lines), encoding="utf-8")
    return {"json": path.relative_to(root).as_posix(), "markdown": md.relative_to(root).as_posix()}


def _canonical_file_key(path: str) -> str:
    stem = Path(str(path or "")).stem.lower()
    stem = stem.split("__", 1)[0]
    stem = re.sub(r"[^a-z0-9_]+", "_", stem)
    stem = re.sub(r"_seq\d+(?=_|$)", "", stem)
    stem = re.sub(r"_v\d+(?=_|$)", "", stem)
    stem = re.sub(r"_d\d{4}(?=_|$)", "", stem)
    stem = re.sub(r"_s\d{3}(?=_|$)", "", stem)
    return re.sub(r"_+", "_", stem).strip("_")


def _file_domain(rel: str, tokens: set[str]) -> str:
    path = str(rel or "").lower().replace("\\", "/")
    for domain_id, prefixes in DOMAIN_PATH_PREFIXES.items():
        if any(path.startswith(prefix) for prefix in prefixes):
            return domain_id
    if path.startswith("docs/") or path.startswith("documentation/") or path.endswith("manifest.md"):
        return "cross_domain.audit"
    if "hush" in path or {"hush", "shard"} <= tokens:
        return "project.hush"
    if "irt" in path or {"irt", "artifact"} <= tokens:
        return "project.irt"
    if "pigeon" in path or {"pigeon", "compiler"} <= tokens:
        return "project.pigeon_code_compiler"
    return "project.keystroke_telemetry"


def _is_stale_context_path(rel: str) -> bool:
    path = str(rel or "").lower().replace("\\", "/")
    return any(part in path for part in STALE_CONTEXT_PARTS)


def _source_preference(rel: str, domain_id: str, segment_tokens: set[str]) -> tuple[float, list[str]]:
    path = str(rel or "").lower().replace("\\", "/")
    suffix = Path(path).suffix
    reasons: list[str] = []
    score = 0.0
    if suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
        score += 0.42
        reasons.append("source_file_preference")
    if suffix == ".md":
        doc_penalty = 0.28
        if "manifest" in segment_tokens or "docs" in segment_tokens or "document" in segment_tokens:
            doc_penalty = 0.04
        score -= doc_penalty
        reasons.append("markdown_context_penalty")
    if _is_stale_context_path(path):
        stale_penalty = 0.95
        if "audit" in segment_tokens or "history" in segment_tokens:
            stale_penalty = 0.35
        score -= stale_penalty
        reasons.append("stale_generated_context_penalty")
    if domain_id == "project.pigeon_code_compiler" and path.startswith("pigeon_compiler/") and suffix == ".py":
        score += 0.36
        reasons.append("domain_source_bonus")
    if domain_id == "project.hush" and "hush" in path and suffix == ".py":
        score += 0.36
        reasons.append("domain_source_bonus")
    if domain_id == "project.irt" and ("irt" in path or "artifact" in path) and suffix == ".py":
        score += 0.36
        reasons.append("domain_source_bonus")
    if segment_tokens & {"intent_key", "intent_key_mapping", "intent_map"}:
        if any(part in path for part in ("tc_intent_keys", "test_tc_intent_keys", "intent_map", "intent_file_memory")):
            score += 0.76
            reasons.append("intent_key_mapping_file_bonus")
        elif (path.startswith("test_") or path.startswith("tests/")) and "intent" not in path:
            score -= 0.28
            reasons.append("generic_test_penalty")
    return score, reasons


def _row_for_path(root: Path, path: Path, rel: str, domain_id: str | None = None,
                  *, external: bool = False, scan_root: Path | None = None) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:5000]
    except Exception:
        text = ""
    haystack = f"{rel} {Path(rel).stem} {text[:1600]}"
    toks = set(_tokens(haystack))
    return {
        "path": _as_posix(path) if external else rel,
        "repo_path": rel,
        "root": _as_posix(scan_root or root),
        "key": _canonical_file_key(rel),
        "domain_id": domain_id or _file_domain(rel, toks),
        "tokens": toks,
        "excerpt": text[:700],
        "external": external,
    }


def _file_rows(root: Path, limit: int = 5000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if len(rows) >= limit:
            break
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in SOURCE_SKIP_PARTS for part in Path(rel).parts):
            continue
        rows.append(_row_for_path(root, path, rel))
    return rows


def _external_file_rows(root: Path, domain_manifest: dict[str, Any], limit: int = 1800) -> list[dict[str, Any]]:
    root = Path(root)
    rows: list[dict[str, Any]] = []
    local_root = root.resolve()
    for domain in _domain_rows(domain_manifest):
        domain_id = str(domain.get("domain_id") or "")
        for spec in domain.get("roots") or []:
            if len(rows) >= limit:
                break
            if not isinstance(spec, dict) or spec.get("source") != "external_project":
                continue
            scan_root = Path(str(spec.get("root") or ""))
            if not scan_root.exists() or _is_relative_to(scan_root, local_root):
                continue
            prefixes = [str(prefix).replace("\\", "/").strip("/") for prefix in spec.get("path_prefixes") or []]
            if not prefixes:
                continue
            for prefix in prefixes:
                if len(rows) >= limit:
                    break
                base = scan_root / Path(prefix)
                if not base.exists():
                    continue
                for path in sorted(base.rglob("*")):
                    if len(rows) >= limit:
                        break
                    if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                        continue
                    rel = path.relative_to(scan_root).as_posix()
                    if any(part in SOURCE_SKIP_PARTS for part in Path(rel).parts):
                        continue
                    rows.append(_row_for_path(root, path, rel, domain_id, external=True, scan_root=scan_root))
    return rows


def _numeric_rows(numeric_files: list[Any] | None) -> tuple[dict[str, float], list[str]]:
    scores: dict[str, float] = {}
    raw_files: list[str] = []
    for row in numeric_files or []:
        if isinstance(row, dict):
            name = str(row.get("path") or row.get("file") or row.get("name") or "")
            score = float(row.get("score") or 0.0)
        else:
            name = str(row)
            score = 0.1
        if not name:
            continue
        raw_files.append(name.replace("\\", "/"))
        key = _canonical_file_key(name)
        scores[key] = max(scores.get(key, 0.0), score)
    return scores, raw_files


def _score_file(domain_id: str, segment_tokens: set[str], prompt_tokens: set[str], file_row: dict[str, Any],
                numeric_scores: dict[str, float]) -> tuple[float, list[str]]:
    ftoks = set(file_row.get("tokens") or [])
    reasons = []
    score = 0.0
    file_domain = str(file_row.get("domain_id") or "project.keystroke_telemetry")
    if file_domain == domain_id:
        score += 0.75
        reasons.append("domain_match")
    elif file_domain == "cross_domain.audit" and domain_id != "personal.operator_profile":
        score -= 0.12
        reasons.append("cross_domain_context")
    else:
        score -= 0.7
        reasons.append("domain_mismatch")
    segment_overlap = segment_tokens & ftoks
    prompt_overlap = prompt_tokens & ftoks
    if segment_overlap:
        score += len(segment_overlap) * 0.45
        reasons.append("segment_overlap")
    if prompt_overlap:
        score += min(1.0, len(prompt_overlap) * 0.08)
        reasons.append("prompt_overlap")
    numeric = numeric_scores.get(str(file_row.get("key") or ""), 0.0)
    if numeric:
        score += min(2.0, numeric * 2.0)
        reasons.append("numeric_prediction")
    path = str(file_row.get("path") or "").lower()
    for tok in segment_tokens:
        if tok in path:
            score += 0.18
            reasons.append("path_token")
            break
    source_score, source_reasons = _source_preference(path, domain_id, segment_tokens)
    score += source_score
    reasons.extend(source_reasons)
    return round(score, 4), sorted(set(reasons))


def _is_source_file(rel: str) -> bool:
    return Path(str(rel or "")).suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx"}


def _compatible_file_domains(domain_id: str) -> set[str]:
    domains = {domain_id}
    if domain_id == "personal.operator_profile":
        domains.add("project.keystroke_telemetry")
    return domains


def _domain_source_available(candidates: list[dict[str, Any]], domain_id: str) -> bool:
    compatible = _compatible_file_domains(domain_id)
    return any(
        str(row.get("domain_id") or "") in compatible and _is_source_file(str(row.get("path") or ""))
        for row in candidates
    )


def _doc_support_allowed(segment_tokens: set[str], domain_id: str) -> bool:
    return domain_id == "cross_domain.audit" or bool(segment_tokens & DOC_SUPPORT_TOKENS)


def _file_allowed_for_domain(row: dict[str, Any], domain_id: str, segment_tokens: set[str]) -> bool:
    file_domain = str(row.get("domain_id") or "")
    if file_domain in _compatible_file_domains(domain_id):
        return True
    if file_domain == "cross_domain.audit" and _doc_support_allowed(segment_tokens, domain_id):
        return True
    return False


def _score_manifest_for_domain(
    segment_tokens: set[str],
    prompt_tokens: set[str],
    manifest: dict[str, Any],
    domain_id: str,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = _score_manifest(segment_tokens | prompt_tokens, manifest)
    manifest_domain = str(manifest.get("domain_id") or "")
    path = str(manifest.get("path") or "")
    if manifest_domain == domain_id:
        score += 0.32
        reasons.append("domain_manifest_match")
    elif manifest_domain == "cross_domain.audit" and _doc_support_allowed(segment_tokens, domain_id):
        score += 0.02
        reasons.append("cross_domain_manifest_support")
    else:
        return -1.0, ["manifest_domain_mismatch"]
    if _is_stale_context_path(path):
        score -= 0.7
        reasons.append("stale_manifest_penalty")
    return round(score, 4), sorted(set(reasons))


def _select_manifest_for_intent(
    manifests: list[dict[str, Any]],
    segment_tokens: set[str],
    prompt_tokens: set[str],
    domain_id: str,
) -> dict[str, Any]:
    scored = []
    for manifest in manifests:
        score, reasons = _score_manifest_for_domain(segment_tokens, prompt_tokens, manifest, domain_id)
        if score > 0:
            scored.append({**manifest, "score": score, "score_reasons": reasons})
    scored.sort(key=lambda row: (-float(row["score"]), row["path"]))
    if scored:
        return scored[0]
    return {
        "path": f"domain:{domain_id}",
        "scope": domain_id,
        "title": domain_id,
        "domain_id": domain_id,
        "score": 0.0,
        "score_reasons": ["domain_scope_fallback"],
        "excerpt": "",
    }


def _manifest_for_file(root: Path, rel: str) -> str:
    full_path = _resolve_context_path(root, rel)
    if full_path.is_absolute() and not _is_relative_to(full_path, Path(root)):
        for parent in [full_path.parent, *full_path.parents]:
            candidate = parent / "MANIFEST.md"
            if candidate.exists():
                return candidate.as_posix()
        return "external:MANIFEST.md"
    path = Path(str(rel or ""))
    parts = path.parts
    for index in range(len(parts), 0, -1):
        candidate = Path(*parts[:index]) / "MANIFEST.md"
        if (Path(root) / candidate).exists():
            return candidate.as_posix()
    return "MANIFEST.md"


def _file_comment(root: Path, rel: str) -> str:
    path = _resolve_context_path(root, rel)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return rel
    for line in text.splitlines()[:40]:
        clean = line.strip().strip("#").strip().strip('"')
        if clean and not clean.startswith("-*-") and "telemetry:pulse" not in clean:
            return clean[:220]
    return rel


def _select_files_for_intent(
    root: Path,
    segment: str,
    prompt: str,
    intent_key: str,
    domain_id: str,
    candidates: list[dict[str, Any]],
    numeric_scores: dict[str, float],
    max_files: int,
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    segment_tokens = set(_tokens(segment))
    prompt_tokens = set(_tokens(prompt))
    scored = []
    for row in candidates:
        score, reasons = _score_file(domain_id, segment_tokens, prompt_tokens, row, numeric_scores)
        if score > 0:
            scored.append({
                "file": row["path"],
                "repo_path": row.get("repo_path", row["path"]),
                "root": row.get("root", ""),
                "domain_id": row.get("domain_id", ""),
                "external": bool(row.get("external")),
                "score": score,
                "reasons": reasons,
            })
    scored.sort(key=lambda row: (-float(row["score"]), row["file"]))

    learned = match_intent_file_memory(root, segment, intent_key=intent_key, limit=max_files)
    learned_files = [row["file"] for row in learned if _resolve_context_path(root, row["file"]).exists()]
    rows_by_file = {row["file"]: row for row in scored}
    for row in learned:
        file = row["file"]
        if not _resolve_context_path(root, file).exists():
            continue
        existing = rows_by_file.get(file)
        if existing:
            existing["score"] = round(float(existing["score"]) + float(row["score"]), 4)
            existing.setdefault("reasons", []).append("learned_file_memory")
        else:
            file_domain = _file_domain(file, set(_tokens(file)))
            if file_domain not in {domain_id, "cross_domain.audit"}:
                continue
            rows_by_file[file] = {
                "file": file,
                "repo_path": file,
                "root": _as_posix(Path(root)),
                "domain_id": file_domain,
                "external": Path(file).is_absolute(),
                "score": row["score"],
                "reasons": ["learned_file_memory"],
            }
    domain_source_available = _domain_source_available(candidates, domain_id)
    scoped_rows = [
        row for row in rows_by_file.values()
        if _file_allowed_for_domain(row, domain_id, segment_tokens)
    ]
    if domain_source_available:
        scored = scoped_rows
    elif domain_id in EXTERNAL_PROJECT_DOMAINS:
        scored = [
            row for row in scoped_rows
            if str(row.get("domain_id") or "") == "cross_domain.audit"
            and _doc_support_allowed(segment_tokens, domain_id)
        ]
    else:
        scored = scoped_rows or list(rows_by_file.values())
    scored = sorted(scored, key=lambda row: (-float(row["score"]), row["file"]))

    files = [row["file"] for row in scored[:max_files]]
    if not files and domain_id not in EXTERNAL_PROJECT_DOMAINS:
        fallback = _manifest_for_file(root, "MANIFEST.md")
        if (Path(root) / fallback).exists():
            files = [fallback]
            scored = [{"file": fallback, "score": 0.01, "reasons": ["manifest_fallback"]}]
        elif candidates:
            files = [candidates[0]["path"]]
            scored = [{"file": candidates[0]["path"], "score": 0.01, "reasons": ["repo_fallback"]}]
    return files, scored[:max_files], learned_files


def _context_clearing(root: Path, selected_files: list[str], numeric_raw: list[str]) -> dict[str, Any]:
    selected = list(dict.fromkeys(selected_files))
    selected_keys = {_canonical_file_key(file) for file in selected}
    deranked = []
    for raw in numeric_raw:
        key = _canonical_file_key(raw)
        exists = (Path(root) / raw).exists()
        if key not in selected_keys or not exists:
            deranked.append({
                "file": raw,
                "reason": "missing_or_outside_selected_context" if not exists else "weaker_than_intent_files",
                "canonical_key": key,
            })
    return {
        "schema": "self_clearing_context/v1",
        "context_window_files": selected,
        "deranked_files": deranked,
        "selected_count": len(selected),
    }


def _load_existing_nodes(root: Path) -> dict[str, Any]:
    path = Path(root) / "logs" / "intent_nodes.json"
    if not path.exists():
        return {"schema": "intent_nodes/v1", "nodes": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        data = {"schema": "intent_nodes/v1", "nodes": {}}
    if not isinstance(data, dict):
        data = {"schema": "intent_nodes/v1", "nodes": {}}
    data.setdefault("schema", "intent_nodes/v1")
    data.setdefault("nodes", {})
    return data


def _match_existing_nodes(root: Path, intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state = _load_existing_nodes(root)
    rows = []
    for intent in intents:
        toks = set(_tokens(" ".join([intent.get("intent_key", ""), intent.get("segment", "")])))
        for key, node in (state.get("nodes") or {}).items():
            ntoks = set(node.get("tokens") or [])
            overlap = toks & ntoks
            if not overlap:
                continue
            file_counts = node.get("files") if isinstance(node.get("files"), dict) else {}
            dominant = [
                file for file, _count in sorted(
                    file_counts.items(),
                    key=lambda item: (-int(item[1]), item[0]),
                )[:5]
            ]
            rows.append({
                "intent_key": key,
                "current_intent_key": intent.get("intent_key", ""),
                "score": round(len(overlap) / max(1, len(toks)), 4),
                "matched_tokens": sorted(overlap)[:12],
                "dominant_files": dominant,
            })
    rows.sort(key=lambda row: (-float(row["score"]), row["intent_key"]))
    return rows[:8]


def _update_intent_nodes(root: Path, intents: list[dict[str, Any]]) -> dict[str, Any]:
    state = _load_existing_nodes(root)
    now = _utc_now()
    nodes = state.setdefault("nodes", {})
    for intent in intents:
        key = intent["intent_key"]
        node = nodes.setdefault(key, {
            "intent_key": key,
            "created_at": now,
            "support": 0,
            "tokens": [],
            "files": {},
            "last_seen": now,
        })
        node["support"] = int(node.get("support") or 0) + 1
        node["last_seen"] = now
        node["tokens"] = sorted(set([*node.get("tokens", []), *_tokens(" ".join([key, intent.get("segment", "")]))]))[:120]
        files = node.setdefault("files", {})
        for file in intent.get("files") or []:
            files[file] = int(files.get(file) or 0) + 1
    state["updated_at"] = now
    state["node_count"] = len(nodes)
    _write_json(Path(root) / "logs" / "intent_nodes.json", state)
    return {"schema": "intent_nodes/v1", "node_count": len(nodes)}


def _write_intent_profile_event(root: Path, event: dict[str, Any]) -> None:
    _append_jsonl(Path(root) / "logs" / "intent_profile_events.jsonl", event)


def _write_intent_profiles(root: Path, graph: dict[str, Any]) -> list[str]:
    root = Path(root)
    updated = []
    now = graph["ts"]
    for intent in graph.get("intents") or []:
        key = intent["intent_key"]
        safe = _safe_key(key).replace(":", "__")
        path = root / "logs" / "intent_profiles" / f"{safe}.json"
        profile = {}
        if path.exists():
            try:
                profile = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                profile = {}
        if not isinstance(profile, dict) or profile.get("schema") != "intent_key_profile/v1":
            profile = {
                "schema": "intent_key_profile/v1",
                "intent_key": key,
                "domain_id": intent.get("domain_id", ""),
                "created_at": now,
                "status": "active",
                "files": {},
                "file_comments": [],
                "prompt_count": 0,
                "triggers": {},
            }
        profile["updated_at"] = now
        profile["domain_id"] = intent.get("domain_id", profile.get("domain_id", ""))
        profile["prompt_count"] = int(profile.get("prompt_count") or 0) + 1
        profile["last_prompt_hash"] = graph.get("prompt_hash")
        profile["last_segment"] = intent.get("segment", "")
        profile["manifest_path"] = intent.get("manifest_path", "")
        triggers = profile.setdefault("triggers", {})
        for tok in _tokens(" ".join([intent.get("segment", ""), key])):
            triggers[tok] = int(triggers.get(tok) or 0) + 1
        files = profile.setdefault("files", {})
        comments = profile.setdefault("file_comments", [])
        for file in intent.get("files") or []:
            row = files.setdefault(file, {
                "path": file,
                "support": 0,
                "role": "context_file",
                "first_seen": now,
            })
            row["support"] = int(row.get("support") or 0) + 1
            row["last_seen"] = now
            row["manifest"] = _manifest_for_file(root, file)
            comment = {
                "ts": now,
                "run_id": graph.get("run_id"),
                "file": file,
                "file_says": _file_comment(root, file),
                "opinion": f"Serves {key} as selected context for segment: {intent.get('segment', '')[:160]}",
                "missing": intent.get("missing", []),
                "confidence": intent.get("confidence", 0.0),
            }
            comments.append(comment)
            _write_intent_profile_event(root, {
                "schema": "intent_profile_event/v1",
                "ts": now,
                "run_id": graph.get("run_id"),
                "event": "file_comment_added",
                "intent_key": key,
                "file": file,
                "prompt_hash": graph.get("prompt_hash"),
            })
        profile["file_comments"] = comments[-40:]
        _write_json(path, profile)
        updated.append(path.relative_to(root).as_posix())
    return updated


def _intent_file_pairings(root: Path, graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for intent in graph.get("intents") or []:
        scores_by_file = {row.get("file"): row for row in intent.get("file_scores") or []}
        for file in intent.get("files") or []:
            score = scores_by_file.get(file, {})
            rows.append({
                "pairing_id": "intent-file:" + _prompt_hash(f"{intent.get('intent_key', '')}|{file}"),
                "intent_key": intent.get("intent_key", ""),
                "domain_id": intent.get("domain_id", ""),
                "segment": intent.get("segment", ""),
                "file": file,
                "repo_path": score.get("repo_path", file),
                "root": score.get("root", _as_posix(Path(root))),
                "external": bool(score.get("external")),
                "score": score.get("score", 0.0),
                "reasons": score.get("reasons", []),
                "file_comment": _file_comment(root, file),
                "missing": intent.get("missing", []),
                "manifest_path": intent.get("manifest_path", ""),
            })
    rows.sort(key=lambda row: (row["domain_id"], row["intent_key"], row["file"]))
    return rows


def _domain_gaps(graph: dict[str, Any]) -> list[dict[str, Any]]:
    gaps = []
    for intent in graph.get("intents") or []:
        missing = intent.get("missing") or []
        if not missing:
            continue
        gaps.append({
            "intent_key": intent.get("intent_key", ""),
            "domain_id": intent.get("domain_id", ""),
            "segment": intent.get("segment", ""),
            "missing": missing,
        })
    return gaps


def _write_intent_map_manifest(root: Path, graph: dict[str, Any]) -> dict[str, str]:
    root = Path(root)
    logs = root / "logs"
    manifest_json = logs / "intent_map_manifest.json"
    pairings = _intent_file_pairings(root, graph)
    files_by_domain: dict[str, list[str]] = {}
    for pairing in pairings:
        files_by_domain.setdefault(pairing["domain_id"], [])
        if pairing["file"] not in files_by_domain[pairing["domain_id"]]:
            files_by_domain[pairing["domain_id"]].append(pairing["file"])
    state = {
        "schema": "intent_map_manifest/v1",
        "updated_at": graph["ts"],
        "last_run_id": graph["run_id"],
        "last_prompt_hash": graph["prompt_hash"],
        "domain_manifest": graph.get("domain_manifest", {}),
        "domain_selection": graph["domain_selection"],
        "intent_count": graph["intent_count"],
        "intents": [
            {
                "intent_key": row["intent_key"],
                "domain_id": row["domain_id"],
                "files": row["files"],
                "external_files": [file for file in row["files"] if Path(str(file)).is_absolute()],
                "manifest_path": row["manifest_path"],
            }
            for row in graph.get("intents") or []
        ],
        "file_pairings": pairings,
        "files_by_domain": files_by_domain,
        "domain_gaps": _domain_gaps(graph),
        "profiles_updated": graph.get("intent_profiles_updated", []),
    }
    _write_json(manifest_json, state)
    lines = [
        "# Intent Map Manifest",
        "",
        f"- updated_at: `{graph['ts']}`",
        f"- run_id: `{graph['run_id']}`",
        f"- prompt_hash: `{graph['prompt_hash']}`",
        f"- primary_domain: `{graph['domain_selection']['primary_domain']}`",
        f"- domain_manifest: `{(graph.get('domain_manifest') or {}).get('path', 'logs/domain_manifest.json')}`",
        "",
        "## Domains",
        "",
    ]
    for domain_id, files in sorted(files_by_domain.items()):
        lines.append(f"- `{domain_id}` files={len(files)}")
    if state["domain_gaps"]:
        lines.extend(["", "## Domain Gaps", ""])
        for gap in state["domain_gaps"]:
            lines.append(f"- `{gap['intent_key']}` missing={', '.join(gap['missing'])}")
    lines.extend([
        "",
        "## File Pairings",
        "",
    ])
    for row in pairings:
        external = " external" if row["external"] else ""
        lines.append(f"- `{row['intent_key']}` -> `{row['file']}` score=`{row['score']}`{external}")
        if row.get("file_comment"):
            lines.append(f"  - says: {row['file_comment'][:160]}")
    lines.extend([
        "",
        "## Intent Profiles",
        "",
    ])
    for intent in graph.get("intents") or []:
        lines.append(f"- `{intent['intent_key']}` domain=`{intent['domain_id']}` manifest=`{intent['manifest_path']}`")
        for file in intent.get("files") or []:
            lines.append(f"  - `{file}`")
    md = logs / "intent_map_manifest.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": manifest_json.relative_to(root).as_posix(), "markdown": md.relative_to(root).as_posix()}


def _write_graph_context(root: Path, graph: dict[str, Any]) -> None:
    lines = [
        "# Intent Graph Context",
        "",
        f"- run_id: `{graph['run_id']}`",
        f"- prompt_hash: `{graph['prompt_hash']}`",
        f"- primary_domain: `{graph['domain_selection']['primary_domain']}`",
        f"- intent_count: `{graph['intent_count']}`",
        "",
    ]
    for intent in graph.get("intents") or []:
        lines.extend([
            f"## {intent['intent_key']}",
            "",
            f"- segment: {intent['segment']}",
            f"- manifest: `{intent['manifest_path']}`",
            f"- files: {', '.join(f'`{file}`' for file in intent.get('files') or [])}",
            "",
        ])
    path = Path(root) / "logs" / "intent_graph_context.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_intent_graph(
    root: Path,
    prompt: str,
    *,
    deleted_words: list[str] | None = None,
    numeric_files: list[Any] | None = None,
    file_rows: list[dict[str, Any]] | None = None,
    domain_manifest: dict[str, Any] | None = None,
    write: bool = True,
    max_intents: int = 8,
    max_files_per_intent: int = 3,
    limit: int | None = None,
    context_selection: dict[str, Any] | None = None,
    **_compat_options: Any,
) -> dict[str, Any]:
    """Compile a prompt into routed intent nodes and update profile memory."""
    root = Path(root)
    prompt = str(prompt or "").strip()
    deleted_words = deleted_words or []
    if limit is not None:
        try:
            max_intents = int(limit)
        except (TypeError, ValueError):
            pass
    if numeric_files is None and isinstance(context_selection, dict):
        numeric_files = context_selection.get("files") or []
    combined_prompt = " ".join([prompt, *map(str, deleted_words)])
    domain_manifest = domain_manifest or _load_domain_manifest(root)
    global_domain = _select_domain(combined_prompt)
    manifests = discover_manifests(root)
    candidates = file_rows if file_rows is not None else [
        *_file_rows(root),
        *_external_file_rows(root, domain_manifest),
    ]
    numeric_scores, numeric_raw = _numeric_rows(numeric_files)
    segments = _split_prompt(prompt, max_intents=max_intents)
    prompt_tokens = set(_tokens(combined_prompt))
    intents = []
    for index, segment in enumerate(segments, 1):
        segment_tokens = set(_tokens(segment))
        segment_domain = _select_domain(segment, fallback_domain=global_domain["primary_domain"])
        domain_id = segment_domain["primary_domain"]
        manifest = _select_manifest_for_intent(manifests, segment_tokens, prompt_tokens, domain_id)
        scope = str(manifest.get("scope") or "root")
        verb = _choose_verb(segment_tokens)
        scale = _choose_scale(segment_tokens | prompt_tokens)
        target = _choose_target(segment, scope)
        intent_key = f"{scope}:{verb}:{target}:{scale}"
        files, file_scores, learned_files = _select_files_for_intent(
            root,
            segment,
            combined_prompt,
            intent_key,
            domain_id,
            candidates,
            numeric_scores,
            max_files_per_intent,
        )
        confidence = round(
            min(1.0, float(manifest.get("score") or 0.0) + (0.08 * len(files)) + (0.08 if learned_files else 0)),
            4,
        )
        missing = []
        if not files:
            missing.append("no_file_pairing")
            if domain_id in EXTERNAL_PROJECT_DOMAINS:
                missing.append(f"domain_files_unavailable:{domain_id}")
        intents.append({
            "schema": "intent_node/v1",
            "intent_id": "intent-node:" + _prompt_hash(f"{prompt}|{index}|{intent_key}"),
            "intent_key": intent_key,
            "domain_id": domain_id,
            "domain_selection": segment_domain,
            "segment": segment,
            "scope": scope,
            "verb": verb,
            "target": target,
            "scale": scale,
            "confidence": confidence,
            "manifest_path": str(manifest.get("path") or "MANIFEST.md"),
            "files": files,
            "file_scores": file_scores,
            "learned_files": learned_files,
            "missing": missing,
        })

    selected_files = [file for intent in intents for file in intent.get("files") or []]
    node_matches = _match_existing_nodes(root, intents)
    nodes = _update_intent_nodes(root, intents) if write else {"schema": "intent_nodes/v1", "node_count": 0}
    domain_split = {
        "schema": "domain_split/v1",
        "primary_domain": global_domain["primary_domain"],
        "global": global_domain,
        "intent_domains": [
            {
                "intent_key": intent["intent_key"],
                "segment": intent["segment"],
                "domain_id": intent["domain_id"],
                "score": (intent.get("domain_selection") or {}).get("primary", {}).get("score", 0.0),
            }
            for intent in intents
        ],
        "split_count": len({intent["domain_id"] for intent in intents}),
    }
    graph = {
        "schema": "intent_graph/v1",
        "ts": _utc_now(),
        "run_id": "intent-run-" + _prompt_hash(prompt + _utc_now()),
        "prompt_hash": _prompt_hash(prompt),
        "prompt": prompt,
        "deleted_words": deleted_words,
        "domain_manifest": {
            "schema": domain_manifest.get("schema", "domain_manifest/v1"),
            "domain_count": len(_domain_rows(domain_manifest)),
            "path": "logs/domain_manifest.json",
        },
        "domain_selection": domain_split,
        "intent_count": len(intents),
        "intents": intents,
        "context_clearing_pass": _context_clearing(root, selected_files, numeric_raw),
        "intent_nodes": nodes,
        "intent_node_matches": node_matches,
    }
    if write:
        for intent in intents:
            memory_files = list(intent.get("files") or [])
            if memory_files:
                memory_files = [memory_files[0], *memory_files]
            remember_intent_files(
                root,
                " ".join([intent.get("segment", ""), prompt, *deleted_words]),
                intent["intent_key"],
                memory_files,
            )
        graph["intent_profiles_updated"] = _write_intent_profiles(root, graph)
        graph["domain_manifest_written"] = _write_domain_manifest(root, domain_manifest)
        graph["intent_map_manifest"] = _write_intent_map_manifest(root, graph)
        logs = root / "logs"
        _write_json(logs / "intent_graph_latest.json", graph)
        _append_jsonl(logs / "intent_graphs.jsonl", graph)
        _write_graph_context(root, graph)
    return graph


def _history_prompt(row: dict[str, Any]) -> str:
    for key in ("msg", "prompt", "text", "message", "final_text", "content"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _load_prompt_history(path: Path, limit_scan: int = 800) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit_scan:]:
        try:
            row = json.loads(line)
        except Exception:
            continue
        prompt = _history_prompt(row)
        if len(prompt) >= 25:
            rows.append({**row, "_prompt": prompt})
    return rows


def _complexity_score(prompt: str) -> float:
    toks = _tokens(prompt)
    domain_hits = 0
    for spec in DOMAIN_HINTS.values():
        domain_hits += len(set(toks) & set(spec["terms"]))
    punctuation = len(re.findall(r"[,;:/-]", prompt))
    return len(set(toks)) + domain_hits * 3 + punctuation * 0.5


def seed_intent_graphs_from_history(
    root: Path,
    *,
    history_path: Path | str | None = None,
    prompts: list[str] | None = None,
    limit: int = 12,
    write: bool = True,
) -> dict[str, Any]:
    """Run complex historical prompts through the intent graph as seed data."""
    root = Path(root)
    selected_prompts: list[str] = []
    source = "explicit_prompts"
    if prompts:
        selected_prompts = [str(prompt).strip() for prompt in prompts if str(prompt).strip()]
    else:
        path = Path(history_path) if history_path else root / "logs" / "prompt_journal.jsonl"
        source = path.as_posix()
        rows = _load_prompt_history(path)
        rows.sort(key=lambda row: _complexity_score(row["_prompt"]), reverse=True)
        chosen = []
        seen_hashes = set()
        for row in rows:
            digest = _prompt_hash(row["_prompt"])
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            chosen.append(row)
            if len(chosen) >= limit:
                break
        selected_prompts = [row["_prompt"] for row in chosen]

    graphs = []
    file_reactions: dict[str, int] = {}
    profiles = set()
    domain_manifest = _load_domain_manifest(root)
    candidates = [*_file_rows(root), *_external_file_rows(root, domain_manifest)]
    for prompt in selected_prompts[:limit]:
        graph = generate_intent_graph(root, prompt, file_rows=candidates, domain_manifest=domain_manifest, write=write)
        graphs.append({
            "prompt_preview": prompt[:180],
            "prompt_hash": graph["prompt_hash"],
            "intent_count": graph["intent_count"],
            "primary_domain": graph["domain_selection"]["primary_domain"],
            "intent_keys": [intent["intent_key"] for intent in graph.get("intents") or []],
            "files_reacted": list(dict.fromkeys(
                file for intent in graph.get("intents") or [] for file in intent.get("files") or []
            )),
        })
        for intent in graph.get("intents") or []:
            profiles.add(intent["intent_key"])
            for file in intent.get("files") or []:
                file_reactions[file] = file_reactions.get(file, 0) + 1

    summary = {
        "schema": "intent_graph_seed_run/v1",
        "ts": _utc_now(),
        "source": source,
        "processed": len(graphs),
        "graphs": graphs,
        "file_reactions": [
            {"file": file, "count": count}
            for file, count in sorted(file_reactions.items(), key=lambda item: (-item[1], item[0]))
        ],
        "intent_profiles_updated": sorted(profiles),
        "manifest": "logs/intent_map_manifest.md",
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "intent_graph_seed_latest.json", summary)
        lines = ["# Intent Graph Seed Run", "", f"- processed: `{len(graphs)}`", f"- source: `{source}`", "", "## File Reactions", ""]
        for row in summary["file_reactions"][:30]:
            lines.append(f"- `{row['file']}` count={row['count']}")
        lines.extend(["", "## Prompt Graphs", ""])
        for row in graphs:
            lines.append(f"- `{row['prompt_hash']}` domain=`{row['primary_domain']}` intents={row['intent_count']}")
            for file in row["files_reacted"][:8]:
                lines.append(f"  - `{file}`")
        (logs / "intent_graph_seed_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
