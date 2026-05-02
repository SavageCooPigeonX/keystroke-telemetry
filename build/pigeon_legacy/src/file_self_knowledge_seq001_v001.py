"""File self-knowledge packets.

These packets are the repo-owned answer to "how does this file work?"
They are deterministic, local, and intended to be read by Codex/Copilot before
any coding model receives a rewrite task.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "file_self_knowledge/v1"
PACKET_SCHEMA = "file_self_knowledge_packet/v1"

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "actual", "using",
    "based", "time", "over", "all", "about", "then", "than", "their",
    "there", "what", "when", "where", "which", "want", "need", "needs",
    "file", "files", "src", "test", "tests", "seq", "v001",
}

ALIASES = {
    "neumeric": "numeric",
    "neumaric": "numeric",
    "sims": "sim",
    "simulation": "sim",
    "simulations": "sim",
    "rewrites": "rewrite",
    "fixes": "fix",
    "emails": "email",
    "manifests": "manifest",
}


def build_file_self_knowledge(
    root: Path,
    files: list[Any] | None = None,
    prompt: str = "",
    limit: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    """Build durable file self-knowledge packets for the current focus set."""
    root = Path(root)
    sources = _load_sources(root)
    selected = _select_files(root, files, prompt, sources, limit)
    packets = [_packet_for_file(root, rel, prompt, sources) for rel in selected]
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "prompt": str(prompt or "")[:500],
        "packet_count": len(packets),
        "packets": packets,
        "operator_read": _operator_read(packets),
        "paths": {
            "latest": "logs/file_self_knowledge_latest.json",
            "history": "logs/file_self_knowledge.jsonl",
            "markdown": "logs/file_self_knowledge.md",
            "packet_dir": "logs/file_self_knowledge",
            "profiles": "file_profiles.json",
        },
    }
    if write:
        _write_outputs(root, result)
    return result


def load_file_self_knowledge(root: Path, file: str | None = None) -> dict[str, Any]:
    """Load the latest packet set or one file-specific packet."""
    root = Path(root)
    if file:
        path = root / "logs" / "file_self_knowledge" / f"{_safe_name(file)}.json"
        return _load_json(path) or {}
    return _load_json(root / "logs" / "file_self_knowledge_latest.json") or {}


def render_file_self_knowledge(result: dict[str, Any]) -> str:
    lines = [
        "# File Self-Knowledge Packets",
        "",
        "Files should know how they work before a coding model touches them.",
        "",
        f"- generated_at: `{result.get('ts', '')}`",
        f"- packets: `{result.get('packet_count', 0)}`",
        "",
        "## Operator Read",
        "",
        result.get("operator_read") or "No file packet woke.",
        "",
    ]
    for packet in result.get("packets") or []:
        lines.extend([
            f"## {packet.get('file')}",
            "",
            f"- packet: `{packet.get('packet_id')}`",
            f"- readiness: `{packet.get('mutation_scope', {}).get('readiness')}`",
            f"- owns: `{', '.join(packet.get('owns') or []) or 'unknown'}`",
            f"- wakes_on: `{', '.join(packet.get('wakes_on') or []) or 'unknown'}`",
            f"- required_context: `{', '.join(packet.get('required_context') or []) or 'none'}`",
            f"- validates_with: `{', '.join(packet.get('validates_with') or []) or 'none'}`",
            f"- known_failures: `{', '.join(packet.get('known_failures') or []) or 'none'}`",
            f"- dead_token_negatives: `{', '.join(packet.get('dead_token_negatives') or []) or 'none'}`",
            f"- guide: {packet.get('model_guide')}",
            f"- quote: {packet.get('file_quote')}",
            "",
        ])
    return "\n".join(lines)


def _load_sources(root: Path) -> dict[str, Any]:
    logs = root / "logs"
    return {
        "dynamic_context": _load_json(logs / "dynamic_context_pack.json") or {},
        "context_selection": _load_json(logs / "context_selection.json") or {},
        "file_sim": _load_json(logs / "batch_rewrite_sim_latest.json") or {},
        "file_self_learning": _load_json(logs / "file_self_sim_learning_latest.json") or {},
        "file_job_council": _load_json(logs / "file_job_council_latest.json") or {},
        "intent_nodes": _load_json(logs / "intent_nodes.json") or {},
        "file_memory_index": _load_json(logs / "file_memory_index.json") or {},
        "file_profiles": _load_json(root / "file_profiles.json") or {},
        "dead_pairs": _load_jsonl(logs / "dead_token_collective_pairs.jsonl", 1200),
        "identity_growth": _load_jsonl(logs / "file_identity_growth.jsonl", 800),
        "learning_outcomes": _load_jsonl(logs / "file_self_sim_learning_outcomes.jsonl", 500),
        "dead_stale": _load_jsonl(logs / "dead_stale_code_findings.jsonl", 800),
        "edit_pairs": _load_jsonl(logs / "edit_pairs.jsonl", 500),
        "response_rewards": _load_jsonl(logs / "response_reward_events.jsonl", 200),
    }


def _select_files(
    root: Path,
    files: list[Any] | None,
    prompt: str,
    sources: dict[str, Any],
    limit: int,
) -> list[str]:
    scores: dict[str, dict[str, Any]] = defaultdict(lambda: {"score": 0.0, "reasons": []})
    for item in files or []:
        rel = _file_from_any(item)
        if rel:
            _score(scores, rel, 12.0, "explicit_focus")
    for item in (sources.get("context_selection") or {}).get("files") or []:
        rel = _file_from_any(item)
        if rel:
            _score(scores, rel, 7.0 + float(item.get("score") or 0), "context_selection")
    for item in (sources.get("dynamic_context") or {}).get("focus_files") or []:
        rel = _file_from_any(item)
        if rel:
            _score(scores, rel, 5.0, f"dynamic_focus:{item.get('reason', 'context')}")
    for proposal in (sources.get("file_sim") or {}).get("proposals") or []:
        rel = _clean_rel(proposal.get("path"))
        if rel:
            _score(scores, rel, 4.0 + float(proposal.get("interlink_score") or 0), "file_sim_proposal")
    for node in (sources.get("file_self_learning") or {}).get("wake_order") or []:
        rel = _clean_rel(node.get("file"))
        if rel:
            _score(scores, rel, 3.5 + float(node.get("wake_score") or 0) / 10.0, "self_learning_wake")
    prompt_tokens = set(_tokens(prompt))
    if prompt_tokens:
        for rel in _repo_files(root):
            overlap = prompt_tokens & set(_tokens(rel))
            if len(overlap) >= 2:
                _score(scores, rel, 2.0 + len(overlap), "path_prompt_overlap")
    rows = []
    for rel, data in scores.items():
        rel = _clean_rel(rel)
        if not rel or not _candidate_allowed(root, rel):
            continue
        rows.append((rel, float(data["score"]), data["reasons"]))
    rows.sort(key=lambda item: (item[1], _source_bonus(item[0])), reverse=True)
    return [rel for rel, _score_value, _reasons in rows[: max(1, int(limit or 8))]]


def _packet_for_file(root: Path, rel: str, prompt: str, sources: dict[str, Any]) -> dict[str, Any]:
    rel = _clean_rel(rel)
    path = root / rel
    profile = _profile_for_file(rel, sources)
    memory = _memory_for_file(root, rel, sources)
    manifest = _nearest_manifest(root, rel)
    tests = _tests_for_file(root, rel)
    relationships = _relationships_for_file(root, rel, sources)
    growth = _growth_for_file(rel, sources)
    dead = _dead_tokens_for_file(rel, sources)
    failures = _known_failures(rel, tests, sources)
    owns = _owns_for_file(root, rel, profile, memory, manifest, growth, prompt)
    wakes_on = _wakes_on_for_file(rel, owns, growth, dead, prompt)
    required_context = _required_context(rel, manifest, tests, relationships, memory)
    safe, unsafe, readiness = _mutation_scope(rel, tests, relationships, failures)
    packet_id = _packet_id(rel, owns, wakes_on, tests, dead)
    return {
        "schema": PACKET_SCHEMA,
        "packet_id": packet_id,
        "file": rel,
        "exists": path.exists(),
        "language": _language(path),
        "approx_tokens": _estimate_tokens(path),
        "owns": owns,
        "wakes_on": wakes_on,
        "safe_mutations": safe,
        "unsafe_mutations": unsafe,
        "required_context": required_context,
        "validates_with": _validation_commands(rel, tests),
        "known_failures": failures,
        "relationships": relationships,
        "dead_token_negatives": dead,
        "operator_memory": memory,
        "mutation_scope": {
            "readiness": readiness,
            "allowed_without_operator": False,
            "boundary": "single_file_patch" if readiness != "blocked" else "hold_until_context",
            "coding_model_role": "draft_within_packet; do not rediscover repo furniture",
        },
        "task_warrant_template": _task_warrant(rel, owns, required_context, tests),
        "model_guide": _model_guide(rel, owns, required_context, tests, dead, failures),
        "file_quote": _file_quote(rel, failures, tests, relationships, dead),
        "source_evidence": {
            "manifest": manifest,
            "memory_messages": memory.get("messages", 0),
            "identity_growth_events": len(growth),
            "dead_token_events": len(dead),
            "tests_found": len(tests),
            "relationship_count": len(relationships),
        },
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> None:
    logs = root / "logs"
    packet_dir = logs / "file_self_knowledge"
    packet_dir.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "file_self_knowledge_latest.json", result)
    _append_jsonl(logs / "file_self_knowledge.jsonl", result)
    (logs / "file_self_knowledge.md").write_text(render_file_self_knowledge(result), encoding="utf-8")
    for packet in result.get("packets") or []:
        _write_json(packet_dir / f"{_safe_name(packet.get('file', 'unknown'))}.json", packet)
    _update_file_profiles(root, result)


def _update_file_profiles(root: Path, result: dict[str, Any]) -> None:
    profiles = _load_json(root / "file_profiles.json") or {}
    ts = result.get("ts") or _now()
    for packet in result.get("packets") or []:
        rel = packet.get("file", "")
        key = _stem_key(rel)
        profile = profiles.setdefault(key, {})
        history = profile.setdefault("self_knowledge_history", [])
        history.append({
            "ts": ts,
            "packet_id": packet.get("packet_id"),
            "owns": packet.get("owns", [])[:6],
            "wakes_on": packet.get("wakes_on", [])[:8],
            "readiness": (packet.get("mutation_scope") or {}).get("readiness"),
            "validates_with": packet.get("validates_with", [])[:4],
            "dead_token_negatives": packet.get("dead_token_negatives", [])[:8],
        })
        profile["self_knowledge_packet"] = {
            "file": rel,
            "packet_id": packet.get("packet_id"),
            "owns": packet.get("owns", [])[:6],
            "required_context": packet.get("required_context", [])[:8],
            "model_guide": packet.get("model_guide"),
            "updated_at": ts,
        }
        profile["self_knowledge_history"] = history[-20:]
        profiles[key] = profile
    _write_json(root / "file_profiles.json", profiles)


def _operator_read(packets: list[dict[str, Any]]) -> str:
    if not packets:
        return "No self-knowledge packets woke; Codex would still be rediscovering the repo from scratch."
    blocked = [p for p in packets if (p.get("mutation_scope") or {}).get("readiness") == "blocked"]
    ready = [p for p in packets if p not in blocked]
    top = packets[0]
    return (
        f"{len(packets)} file packet(s) woke. Top file `{top.get('file')}` now carries owns/wakes/context/"
        f"validation/refusal data for Codex to probe with before any rewrite model drafts. "
        f"{len(ready)} are draft-ready inside rails; {len(blocked)} are blocked until real validation/context exists."
    )


def _owns_for_file(
    root: Path,
    rel: str,
    profile: dict[str, Any],
    memory: dict[str, Any],
    manifest: str,
    growth: list[dict[str, Any]],
    prompt: str,
) -> list[str]:
    tokens = Counter(_tokens(rel))
    for row in growth[-12:]:
        tokens.update(_tokens(" ".join(str(tag) for tag in row.get("growth_tags") or [])))
        tokens.update(_tokens(row.get("intent_key", "")))
    for text in _profile_text(profile):
        tokens.update(_tokens(text))
    for values in (memory.get("commands") or {}).values():
        for value in values:
            tokens.update(_tokens(value))
    if manifest:
        try:
            tokens.update(_tokens((root / manifest).read_text(encoding="utf-8", errors="ignore")[:1800]))
        except Exception:
            pass
    prompt_tokens = set(_tokens(prompt))
    for token in prompt_tokens & set(tokens):
        tokens[token] += 2
    role = _role_from_tokens(set(tokens))
    owns = [role]
    owns.extend(token for token, _count in tokens.most_common(10) if token not in set(_tokens(role)))
    return _dedupe(owns)[:8]


def _wakes_on_for_file(
    rel: str,
    owns: list[str],
    growth: list[dict[str, Any]],
    dead: list[str],
    prompt: str,
) -> list[str]:
    tokens = Counter(_tokens(rel))
    tokens.update(_tokens(" ".join(owns)))
    tokens.update(_tokens(prompt))
    for row in growth[-10:]:
        tokens.update(_tokens(" ".join(str(tag) for tag in row.get("growth_tags") or [])))
        tokens.update(_tokens(row.get("intent_key", "")))
    for token in dead:
        if token in tokens:
            tokens[token] = max(0, tokens[token] - 3)
    return [token for token, count in tokens.most_common(12) if count > 0][:10]


def _required_context(
    rel: str,
    manifest: str,
    tests: list[str],
    relationships: list[dict[str, Any]],
    memory: dict[str, Any],
) -> list[str]:
    files = [rel]
    if manifest:
        files.append(manifest)
    files.extend(tests[:4])
    files.extend(item.get("file", "") for item in relationships[:8])
    thread = memory.get("thread")
    if thread:
        files.append(str(thread))
    return [item for item in _dedupe(_clean_rel(item) for item in files) if item][:12]


def _mutation_scope(
    rel: str,
    tests: list[str],
    relationships: list[dict[str, Any]],
    failures: list[str],
) -> tuple[list[str], list[str], str]:
    suffix = Path(rel).suffix.lower()
    safe = ["bounded edits that preserve current public contract"]
    unsafe = [
        "full rewrite without operator approval",
        "cross-file mutation without a context pack",
        "inventing validation commands that do not exist",
    ]
    readiness = "draft_ready"
    if suffix == ".py":
        safe.append("small function/class patch after py_compile")
    elif suffix == ".md":
        safe.append("documentation/manifest update with diff check")
    else:
        safe.append("metadata patch after parser validation")
    if tests:
        safe.append("test-bound patch using existing validation")
    else:
        unsafe.append("claiming test coverage before a real test is mapped")
        readiness = "needs_validation"
    if relationships:
        unsafe.append("ignoring peer files that already co-change or validate this file")
    if any("missing_validation" in item for item in failures):
        readiness = "blocked"
    return _dedupe(safe), _dedupe(unsafe), readiness


def _validation_commands(rel: str, tests: list[str]) -> list[str]:
    commands = []
    if rel.endswith(".py"):
        commands.append(f"py -m py_compile {rel}")
    elif rel.endswith(".json"):
        commands.append(f"py -m json.tool {rel}")
    commands.extend(f"py -m pytest {test} -q" for test in tests[:4])
    commands.append("git diff --check")
    return _dedupe(commands)


def _relationships_for_file(root: Path, rel: str, sources: dict[str, Any]) -> list[dict[str, Any]]:
    rel = _clean_rel(rel)
    relationships: list[dict[str, Any]] = []
    council = sources.get("file_job_council") or {}
    for edge in council.get("relationships") or []:
        left = _clean_rel(edge.get("from"))
        right = _clean_rel(edge.get("to"))
        if left == rel and right:
            relationships.append({"file": right, "type": edge.get("type", "peer"), "reason": edge.get("reason", "")})
        elif right == rel and left:
            relationships.append({"file": left, "type": edge.get("type", "peer"), "reason": edge.get("reason", "")})
    for job in council.get("jobs") or []:
        files = [_clean_rel(item) for item in job.get("files") or []]
        if rel in files:
            for item in files:
                if item and item != rel:
                    relationships.append({"file": item, "type": "job_peer", "reason": job.get("why", "same job")})
            for item in job.get("context_files") or []:
                clean = _clean_rel(item)
                if clean and clean != rel:
                    relationships.append({"file": clean, "type": "context", "reason": "job context file"})
    relationships.extend(_local_import_relationships(root, rel))
    return _dedupe_relationships(relationships)[:12]


def _local_import_relationships(root: Path, rel: str) -> list[dict[str, str]]:
    path = root / rel
    if not path.exists() or path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    relationships = []
    for line in text.splitlines()[:300]:
        match = re.match(r"\s*from\s+src\.([a-zA-Z0-9_.]+)\s+import", line)
        if match:
            candidate = "src/" + match.group(1).replace(".", "/") + ".py"
            if (root / candidate).exists():
                relationships.append({"file": candidate, "type": "import", "reason": "direct source import"})
        match = re.match(r"\s*import\s+src\.([a-zA-Z0-9_.]+)", line)
        if match:
            candidate = "src/" + match.group(1).replace(".", "/") + ".py"
            if (root / candidate).exists():
                relationships.append({"file": candidate, "type": "import", "reason": "direct source import"})
    return relationships


def _tests_for_file(root: Path, rel: str) -> list[str]:
    stem = _stem_key(rel)
    direct = [
        root / f"test_{stem}.py",
        root / "tests" / f"test_{stem}.py",
    ]
    tests = []
    for path in direct:
        if path.exists():
            tests.append(path.relative_to(root).as_posix())
    if len(tests) < 4:
        for path in sorted(root.glob("test*.py"))[:300]:
            if path.relative_to(root).as_posix() in tests:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:5000]
            except Exception:
                continue
            if Path(rel).stem in text or stem in _tokens(path.name):
                tests.append(path.relative_to(root).as_posix())
            if len(tests) >= 4:
                break
    return _dedupe(tests)[:4]


def _nearest_manifest(root: Path, rel: str) -> str:
    current = (root / rel).parent
    while True:
        manifest = current / "MANIFEST.md"
        if manifest.exists():
            return manifest.relative_to(root).as_posix()
        if current == root or root not in current.parents:
            break
        current = current.parent
    manifest = root / "src" / "MANIFEST.md"
    if manifest.exists():
        return manifest.relative_to(root).as_posix()
    manifest = root / "MANIFEST.md"
    if manifest.exists():
        return manifest.relative_to(root).as_posix()
    return ""


def _memory_for_file(root: Path, rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    rel = _clean_rel(rel)
    for item in (sources.get("file_memory_index") or {}).get("files") or []:
        if _clean_rel(item.get("file")) != rel:
            continue
        data = {}
        memory_path = Path(str(item.get("path") or ""))
        if memory_path and not memory_path.is_absolute():
            memory_path = root / memory_path
        if memory_path.exists():
            data = _load_json(memory_path) or {}
        commands: dict[str, list[str]] = defaultdict(list)
        notes = []
        for message in data.get("messages", [])[-12:]:
            for key, values in (message.get("commands") or {}).items():
                for value in values or []:
                    commands[str(key)].append(str(value))
            preview = str(message.get("body_preview") or "").strip()
            if preview:
                notes.append(preview[:180])
        return {
            "messages": int(item.get("messages") or len(data.get("messages") or [])),
            "thread": item.get("markdown") or item.get("path") or "",
            "commands": {key: _dedupe(values)[-6:] for key, values in commands.items()},
            "notes": notes[-4:],
        }
    return {"messages": 0, "thread": "", "commands": {}, "notes": []}


def _profile_for_file(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    return (sources.get("file_profiles") or {}).get(_stem_key(rel), {})


def _profile_text(profile: dict[str, Any]) -> list[str]:
    chunks = []
    for key in ("self_knowledge_packet", "self_sim_profile", "learning_history", "learning_outcomes"):
        value = profile.get(key)
        if value:
            chunks.append(json.dumps(value, ensure_ascii=False, sort_keys=True)[:2400])
    return chunks


def _growth_for_file(rel: str, sources: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in sources.get("identity_growth") or [] if _clean_rel(row.get("file")) == rel][-30:]


def _dead_tokens_for_file(rel: str, sources: dict[str, Any]) -> list[str]:
    tokens: Counter[str] = Counter()
    for row in sources.get("dead_pairs") or []:
        old_path = _clean_rel(row.get("old_path"))
        new_path = _clean_rel(row.get("new_path"))
        if rel not in {old_path, new_path}:
            continue
        tokens.update(_tokens(" ".join(str(item) for item in row.get("dead_tokens") or [])))
        if row.get("event_type") in {"rename", "delete"}:
            tokens.update(_tokens(row.get("old_identity", "")))
    return [token for token, _count in tokens.most_common(16)]


def _known_failures(rel: str, tests: list[str], sources: dict[str, Any]) -> list[str]:
    failures = []
    passing_outcomes = {"compile_pass", "passed", "verified", "actual_job_pass"}
    if not tests and rel.endswith(".py"):
        failures.append("missing_validation:test_file_not_mapped")
    for row in sources.get("learning_outcomes") or []:
        if _clean_rel(row.get("file")) == rel and str(row.get("outcome", "")).lower() not in passing_outcomes:
            failures.append(f"prior_learning_outcome:{row.get('outcome', 'unknown')}")
    for row in sources.get("dead_stale") or []:
        if _clean_rel(row.get("file") or row.get("path")) == rel:
            label = row.get("reason") or row.get("kind") or row.get("category") or "dead_stale_suspect"
            failures.append(f"dead_stale:{label}")
    return _dedupe(failures)[:8]


def _task_warrant(rel: str, owns: list[str], context: list[str], tests: list[str]) -> dict[str, Any]:
    return {
        "to": rel,
        "mission": owns[0] if owns else "preserve file responsibility",
        "load_before_touching": context[:8],
        "allowed_action": "draft bounded patch or refusal with missing context",
        "proof_required": _validation_commands(rel, tests)[:5],
        "operator_approval_required": True,
    }


def _model_guide(
    rel: str,
    owns: list[str],
    context: list[str],
    tests: list[str],
    dead: list[str],
    failures: list[str],
) -> str:
    clauses = [
        f"Patch {rel} only inside its stated responsibility: {owns[0] if owns else 'unknown'}.",
        f"Load {', '.join(context[:4]) or rel} before drafting.",
    ]
    if tests:
        clauses.append(f"Validate with {tests[0]} plus diff check.")
    else:
        clauses.append("Do not claim test coverage; map validation first.")
    if dead:
        clauses.append(f"Do not revive stale identity tokens: {', '.join(dead[:5])}.")
    if failures:
        clauses.append(f"Address known failure first: {failures[0]}.")
    clauses.append("Return a small warrant-bound patch; no full rewrite without approval.")
    return " ".join(clauses)[:720]


def _file_quote(
    rel: str,
    failures: list[str],
    tests: list[str],
    relationships: list[dict[str, Any]],
    dead: list[str],
) -> str:
    name = Path(rel).name
    if failures:
        return f"{name}: I can help, but first stop asking me to pass imaginary validation."
    if dead:
        return f"{name}: I buried {dead[0]} for a reason; do not invite it back with snacks."
    if relationships:
        peer = Path(str(relationships[0].get("file") or "")).name
        return f"{name}: load {peer} before you let a rewrite model touch my furniture."
    if tests:
        return f"{name}: I have a test receipt; give me a bounded warrant and nobody gets theatrical."
    return f"{name}: I know my lane now; the model can stop wandering around with a flashlight."


def _role_from_tokens(tokens: set[str]) -> str:
    if {"response", "policy", "reward", "style"} & tokens:
        return "operator response policy and reward routing"
    if {"intent", "key", "node", "orchestrator", "compile"} & tokens:
        return "intent compilation and mutation routing"
    if {"context", "select", "selection", "pack"} & tokens:
        return "context selection and self-clearing file packs"
    if {"email", "mail", "memory"} & tokens:
        return "file mail memory and operator correspondence"
    if {"sim", "learning", "rewrite"} & tokens:
        return "file simulation and rewrite learning"
    if {"dead", "stale", "token", "rename"} & tokens:
        return "dead/stale identity evidence and deranking"
    if {"test", "validation", "validate"} & tokens:
        return "validation and survival proof"
    return "source responsibility inferred from history and path"


def _packet_id(rel: str, owns: list[str], wakes_on: list[str], tests: list[str], dead: list[str]) -> str:
    seed = json.dumps({
        "file": rel,
        "owns": owns,
        "wakes_on": wakes_on,
        "tests": tests,
        "dead": dead,
    }, sort_keys=True, ensure_ascii=False)
    return "fsk-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _language(path: Path) -> str:
    return {
        ".py": "python",
        ".md": "markdown",
        ".json": "json",
        ".jsonl": "jsonl",
        ".ps1": "powershell",
    }.get(path.suffix.lower(), path.suffix.lower().lstrip(".") or "unknown")


def _estimate_tokens(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def _file_from_any(item: Any) -> str:
    if isinstance(item, dict):
        return _clean_rel(item.get("path") or item.get("file") or item.get("name"))
    return _clean_rel(item)


def _repo_files(root: Path) -> list[str]:
    files = []
    for pattern in ("src/**/*.py", "client/**/*.py", "test*.py", "tests/**/*.py", ".github/copilot-instructions.md", "src/**/MANIFEST.md"):
        for path in root.glob(pattern):
            rel = path.relative_to(root).as_posix()
            if "__pycache__" not in rel:
                files.append(rel)
    return _dedupe(files)


def _candidate_allowed(root: Path, rel: str) -> bool:
    if rel.startswith("logs/") or "__pycache__" in rel:
        return False
    return (root / rel).exists() and Path(rel).suffix.lower() in {".py", ".md", ".json"}


def _source_bonus(rel: str) -> float:
    if rel.startswith("src/"):
        return 2.0
    if rel.startswith("client/"):
        return 1.5
    if Path(rel).name.startswith("test_"):
        return -0.5
    return 0.0


def _score(scores: dict[str, dict[str, Any]], rel: str, points: float, reason: str) -> None:
    clean = _clean_rel(rel)
    if not clean:
        return
    scores[clean]["score"] += points
    scores[clean]["reasons"].append(reason)


def _clean_rel(value: Any) -> str:
    text = str(value or "").strip().strip("'\"").replace("\\", "/")
    if not text:
        return ""
    if text.startswith("/") or (len(text) > 1 and text[1] == ":"):
        return ""
    if ".." in Path(text).parts:
        return ""
    return text


def _safe_name(rel: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "__", str(rel).replace("\\", "/")).strip("_") or "unknown"


def _stem_key(value: str) -> str:
    stem = Path(str(value)).stem.lower()
    stem = re.sub(r"_seq\d+(?=_|$)", "", stem)
    stem = re.sub(r"_s\d{3,4}(?=_|$)", "", stem)
    stem = re.sub(r"_v\d+(?=_|$)", "", stem)
    stem = re.sub(r"_d\d{4}(?=_|$)", "", stem)
    stem = stem.split("__", 1)[0]
    stem = re.sub(r"[^a-z0-9_]+", "_", stem)
    return re.sub(r"_+", "_", stem).strip("_") or Path(str(value)).stem.lower()


def _tokens(text: Any) -> list[str]:
    out = []
    for raw in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower()):
        parts = [raw]
        if "_" in raw:
            parts.extend(part for part in raw.split("_") if part)
        for token in parts:
            token = token.strip("_")
            if len(token) < 3 or token in STOP:
                continue
            token = ALIASES.get(token, token)
            out.append(token)
            if token.endswith("s") and len(token) > 4:
                out.append(token[:-1])
    return out


def _dedupe(values: Any) -> list[Any]:
    seen = set()
    out = []
    for value in values or []:
        key = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str) if isinstance(value, dict) else str(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _dedupe_relationships(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for item in items:
        rel = _clean_rel(item.get("file"))
        if not rel or rel in seen:
            continue
        seen.add(rel)
        out.append({"file": rel, "type": str(item.get("type") or "peer"), "reason": str(item.get("reason") or "")[:180]})
    return out


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except Exception:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "PACKET_SCHEMA",
    "SCHEMA",
    "build_file_self_knowledge",
    "load_file_self_knowledge",
    "render_file_self_knowledge",
]
