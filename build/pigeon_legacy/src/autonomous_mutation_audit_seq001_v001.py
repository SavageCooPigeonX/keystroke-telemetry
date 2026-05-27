"""Audit autonomous mutation history and file reaction signals.

This is the bridge between "models proposed work" and "files learned from
mutation." It reads local logs, git/self-fix history, DeepSeek queues, file
self-knowledge packets, and last-prompt intent traces, then emits a compact
audit plus context-clearing rules.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "autonomous_mutation_audit/v1"

INTENT_RE = re.compile(r"^[A-Za-z0-9_./-]+:[A-Za-z0-9_./-]+:[A-Za-z0-9_./-]+:[A-Za-z0-9_./-]+$")


def audit_autonomous_mutations(root: Path, prompt: str = "", write: bool = True) -> dict[str, Any]:
    root = Path(root)
    logs = root / "logs"
    latest_prompt = _latest_prompt(root)
    prompt_text = str(prompt or latest_prompt.get("msg") or "")
    sources = _load_sources(root)
    last_prompt = _last_prompt_forensics(root, prompt_text, latest_prompt, sources)
    deepseek = _deepseek_audit(root, sources)
    self_fix = _self_fix_audit(root)
    file_reactions = _file_reactions(root, last_prompt, sources)
    report = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "prompt": prompt_text[:1000],
        "last_prompt_forensics": last_prompt,
        "email_delivery": _email_delivery_audit(root, sources),
        "deepseek_actuals": deepseek,
        "self_fix_history": self_fix,
        "file_reactions": file_reactions,
        "operator_read": _operator_read(last_prompt, deepseek, self_fix, file_reactions),
        "paths": {
            "latest": "logs/autonomous_mutation_audit_latest.json",
            "history": "logs/autonomous_mutation_audit.jsonl",
            "markdown": "logs/autonomous_mutation_audit.md",
            "context_clearing_rules": "logs/file_context_clearing_rules.json",
        },
    }
    if write:
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "autonomous_mutation_audit_latest.json", report)
        _append_jsonl(logs / "autonomous_mutation_audit.jsonl", report)
        (logs / "autonomous_mutation_audit.md").write_text(render_autonomous_mutation_audit(report), encoding="utf-8")
        _write_json(logs / "file_context_clearing_rules.json", file_reactions.get("context_clearing_rules", {}))
    return report


def render_autonomous_mutation_audit(report: dict[str, Any]) -> str:
    last = report.get("last_prompt_forensics") or {}
    deepseek = report.get("deepseek_actuals") or {}
    email = report.get("email_delivery") or {}
    self_fix = report.get("self_fix_history") or {}
    reactions = report.get("file_reactions") or {}
    lines = [
        "# Autonomous Mutation Audit",
        "",
        report.get("operator_read", ""),
        "",
        "## Last Prompt Intent Keys",
        "",
        f"- prompt_session: `{last.get('session_n')}`",
        f"- distinct_structured_intent_keys: `{last.get('distinct_intent_key_count', 0)}`",
    ]
    for item in last.get("intent_key_sources", []):
        lines.append(f"- `{item.get('intent_key')}` via `{item.get('source')}`")
    if last.get("unstructured_intent_fragments"):
        lines.extend(["", "### Unstructured Fragments"])
        for item in last.get("unstructured_intent_fragments", [])[:4]:
            lines.append(f"- `{item.get('source')}`: {item.get('value', '')[:180]}")
    lines.extend([
        "",
        "## Files Logged To",
        "",
    ])
    for source, files in (last.get("files_logged_by_source") or {}).items():
        lines.append(f"- `{source}`: `{', '.join(files[:12]) or 'none'}`")
    lines.extend([
        "",
        "## Email",
        "",
        f"- mode: `{email.get('mode')}`",
        f"- can_send: `{email.get('can_send')}`",
        f"- latest_sent: `{email.get('latest_sent_id') or 'none'}`",
        f"- latest_error: `{email.get('latest_error') or 'none'}`",
        "",
        "## DeepSeek Actuals",
        "",
        f"- code_completion_jobs: `{deepseek.get('code_completion_jobs', 0)}`",
        f"- prompt_jobs: `{deepseek.get('prompt_jobs', 0)}`",
        f"- prompt_results: `{deepseek.get('prompt_results', 0)}`",
        f"- dry_run_results: `{deepseek.get('dry_run_results', 0)}`",
        f"- applied_result_evidence: `{deepseek.get('applied_result_evidence', 0)}`",
        f"- current_read: {deepseek.get('read')}",
        "",
        "## Self-Fix History",
        "",
        f"- docs: `{self_fix.get('self_fix_docs', 0)}`",
        f"- git_matches: `{self_fix.get('git_match_count', 0)}`",
        f"- improvement_subjects: `{len(self_fix.get('improvement_subjects') or [])}`",
        f"- breakage_subjects: `{len(self_fix.get('breakage_subjects') or [])}`",
    ])
    for item in (self_fix.get("notable_subjects") or [])[:8]:
        lines.append(f"- `{item.get('short')}` {item.get('date')}: {item.get('subject')}")
    lines.extend([
        "",
        "## File Reaction / Context Clearing",
        "",
        f"- files_audited: `{reactions.get('files_audited', 0)}`",
        f"- outcome_rows: `{reactions.get('outcome_rows', 0)}`",
        f"- read: {reactions.get('read')}",
        "",
    ])
    for item in reactions.get("files", [])[:12]:
        lines.extend([
            f"### {item.get('file')}",
            f"- action: `{item.get('context_action')}`",
            f"- mutation_events: `{item.get('mutation_events')}`",
            f"- tests_found: `{item.get('tests_found')}`",
            f"- dead_tokens: `{', '.join(item.get('dead_tokens') or []) or 'none'}`",
            f"- memory_condensation: {item.get('memory_condensation')}",
            "",
        ])
    return "\n".join(lines)


def _load_sources(root: Path) -> dict[str, Any]:
    logs = root / "logs"
    return {
        "intent_key_latest": _load_json(logs / "intent_key_latest.json") or {},
        "intent_keys": _load_jsonl(logs / "intent_keys.jsonl", 300),
        "intent_loop": _load_json(logs / "intent_loop_latest.json") or {},
        "context_selection": _load_json(logs / "context_selection.json") or {},
        "dynamic_context": _load_json(logs / "dynamic_context_pack.json") or {},
        "batch_sim": _load_json(logs / "batch_rewrite_sim_latest.json") or {},
        "file_self_knowledge": _load_json(logs / "file_self_knowledge_latest.json") or {},
        "file_email_delivery": _load_json(logs / "file_email_delivery_status.json") or {},
        "file_email_outbox": _load_jsonl(logs / "file_email_outbox.jsonl", 300),
        "resend_payloads": _load_jsonl(logs / "resend_payloads.jsonl", 300),
        "deepseek_code_jobs": _load_jsonl(logs / "deepseek_code_completion_jobs.jsonl", 1000),
        "deepseek_prompt_jobs": _load_jsonl(logs / "deepseek_prompt_jobs.jsonl", 1000),
        "deepseek_prompt_results": _load_jsonl(logs / "deepseek_prompt_results.jsonl", 1000),
        "deepseek_daemon": _load_jsonl(logs / "deepseek_daemon.jsonl", 300),
        "learning_outcomes": _load_jsonl(logs / "file_self_sim_learning_outcomes.jsonl", 1000),
        "dead_pairs": _load_jsonl(logs / "dead_token_collective_pairs.jsonl", 5000),
        "identity_growth": _load_jsonl(logs / "file_identity_growth.jsonl", 5000),
        "edit_pairs": _load_jsonl(logs / "edit_pairs.jsonl", 1000),
        "training_pairs": _load_jsonl(logs / "training_pairs.jsonl", 1000),
    }


def _latest_prompt(root: Path) -> dict[str, Any]:
    rows = _load_jsonl(root / "logs" / "prompt_journal.jsonl", 5)
    return rows[-1] if rows else {}


def _last_prompt_forensics(
    root: Path,
    prompt: str,
    latest_prompt: dict[str, Any],
    sources: dict[str, Any],
) -> dict[str, Any]:
    prompt_norm = _norm(prompt)
    intent_sources: list[dict[str, str]] = []
    fragments: list[dict[str, str]] = []

    def add_key(source: str, value: Any) -> None:
        value_s = str(value or "").strip()
        if not value_s:
            return
        if INTENT_RE.match(value_s):
            intent_sources.append({"source": source, "intent_key": value_s})
        else:
            fragments.append({"source": source, "value": value_s[:400]})

    latest = sources.get("intent_key_latest") or {}
    if not prompt_norm or _same_prompt(prompt_norm, latest.get("prompt")):
        add_key("logs/intent_key_latest.json", latest.get("intent_key"))
    for row in sources.get("intent_keys") or []:
        if _same_prompt(prompt_norm, row.get("prompt")):
            add_key("logs/intent_keys.jsonl", row.get("intent_key"))
    loop = sources.get("intent_loop") or {}
    if _same_prompt(prompt_norm, loop.get("prompt")):
        add_key("logs/intent_loop_latest.json", loop.get("intent_key"))
    sim = sources.get("batch_sim") or {}
    sim_intent = sim.get("intent") if isinstance(sim.get("intent"), dict) else {}
    if _same_prompt(prompt_norm, sim_intent.get("raw")):
        add_key("logs/batch_rewrite_sim_latest.json", sim_intent.get("intent_key"))
    dyn = sources.get("dynamic_context") or {}
    if _same_prompt(prompt_norm, dyn.get("prompt")):
        policy = dyn.get("operator_response_policy") if isinstance(dyn.get("operator_response_policy"), dict) else {}
        for move in policy.get("intent_moves") or []:
            if isinstance(move, dict):
                add_key("logs/dynamic_context_pack.json:operator_response_policy", move.get("intent_key"))
        add_key("logs/dynamic_context_pack.json:context_selection", ((dyn.get("context_selection") or {}).get("intent_keys")))
    ctx = sources.get("context_selection") or {}
    add_key("logs/context_selection.json", ctx.get("intent_keys"))
    for row in (sources.get("file_email_outbox") or [])[-10:]:
        if prompt_norm and prompt_norm[:120] in _norm(row.get("reason")):
            add_key("logs/file_email_outbox.jsonl", row.get("intent_key"))

    distinct = []
    seen = set()
    for item in intent_sources:
        key = item["intent_key"]
        if key in seen:
            continue
        seen.add(key)
        distinct.append(item)

    files_by_source = _files_logged_by_source(sources, prompt_norm)
    return {
        "session_n": latest_prompt.get("session_n"),
        "prompt_ts": latest_prompt.get("ts"),
        "prompt_source": latest_prompt.get("source"),
        "distinct_intent_key_count": len({item["intent_key"] for item in intent_sources}),
        "intent_key_sources": distinct,
        "unstructured_intent_fragments": fragments[:8],
        "files_logged_by_source": files_by_source,
        "all_files": sorted({file for files in files_by_source.values() for file in files}),
    }


def _files_logged_by_source(sources: dict[str, Any], prompt_norm: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    ctx = sources.get("context_selection") or {}
    out["context_selection"] = _dedupe(str(item.get("name") or item.get("file") or item) for item in ctx.get("files") or [])
    dyn = sources.get("dynamic_context") or {}
    out["dynamic_focus_files"] = _dedupe(str(item.get("name") or item.get("file") or item) for item in dyn.get("focus_files") or [])
    loop = sources.get("intent_loop") or {}
    out["intent_loop_focus"] = _dedupe(loop.get("focus_files") or [])
    out["intent_loop_proposals"] = _dedupe(item.get("file") for item in loop.get("proposals") or [] if isinstance(item, dict))
    sim = sources.get("batch_sim") or {}
    out["batch_rewrite_proposals"] = _dedupe(item.get("path") for item in sim.get("proposals") or [] if isinstance(item, dict))
    self_knowledge = sources.get("file_self_knowledge") or {}
    out["file_self_knowledge_packets"] = _dedupe(item.get("file") for item in self_knowledge.get("packets") or [] if isinstance(item, dict))
    email_files = []
    for row in (sources.get("file_email_outbox") or [])[-12:]:
        if prompt_norm and prompt_norm[:120] not in _norm(row.get("reason")):
            continue
        email_files.append(row.get("file"))
        email_files.extend(row.get("context_injection") or [])
    out["file_email_receipt"] = _dedupe(email_files)
    return {key: [item for item in value if item] for key, value in out.items()}


def _email_delivery_audit(root: Path, sources: dict[str, Any]) -> dict[str, Any]:
    status = sources.get("file_email_delivery") or {}
    outbox = sources.get("file_email_outbox") or []
    sent = [row for row in outbox if (row.get("resend") or {}).get("status") == "sent"]
    errors = [row for row in outbox if (row.get("resend") or {}).get("status") == "error"]
    latest_sent = sent[-1] if sent else {}
    latest_error = errors[-1] if errors else {}
    return {
        "mode": status.get("mode"),
        "can_send": bool(status.get("can_send")),
        "api_key_present": bool(status.get("api_key_present")),
        "blockers": status.get("blockers") or [],
        "outbox_rows": len(outbox),
        "sent_rows": len(sent),
        "error_rows": len(errors),
        "latest_sent_id": ((latest_sent.get("resend") or {}).get("response") or {}).get("id"),
        "latest_sent_subject": latest_sent.get("subject"),
        "latest_error": (latest_error.get("resend") or {}).get("error") or (latest_error.get("resend") or {}).get("http_status"),
    }


def _deepseek_audit(root: Path, sources: dict[str, Any]) -> dict[str, Any]:
    code_jobs = sources.get("deepseek_code_jobs") or []
    prompt_jobs = sources.get("deepseek_prompt_jobs") or []
    prompt_results = sources.get("deepseek_prompt_results") or []
    daemon = sources.get("deepseek_daemon") or []
    edits = sources.get("edit_pairs") or []
    statuses = Counter(str(row.get("status") or "unknown") for row in code_jobs)
    prompt_statuses = Counter(str(row.get("status") or "unknown") for row in prompt_jobs)
    dry_run_results = sum(1 for row in prompt_results if row.get("dry_run"))
    applied_results = [
        row for row in [*prompt_results, *daemon]
        if not row.get("dry_run") and str(row.get("success", "")).lower() == "true"
    ]
    deepseek_edits = [
        row for row in edits
        if "deepseek" in _norm(row.get("edit_why")) or "deepseek" in _norm(row.get("prompt_msg"))
    ]
    historical = _git_log(root, ["deepseek", "self-heal", "autonomous", "auto"], limit=80)
    read = (
        "Current DeepSeek path is mostly queue/proposal memory: code jobs are approval-gated, "
        "prompt jobs are queued, and recorded prompt results are dry-run. Historical commits show "
        "DeepSeek/self-heal influenced source evolution, but current logs do not prove autonomous "
        "DeepSeek source overwrites completed."
    )
    if applied_results or deepseek_edits:
        read = (
            "DeepSeek has some applied evidence in local logs/edit pairs, but most current work is still "
            "queued behind approval. Treat it as planner/grader evidence unless a validation-bound edit pair exists."
        )
    return {
        "code_completion_jobs": len(code_jobs),
        "code_job_statuses": dict(statuses),
        "prompt_jobs": len(prompt_jobs),
        "prompt_job_statuses": dict(prompt_statuses),
        "prompt_results": len(prompt_results),
        "dry_run_results": dry_run_results,
        "applied_result_evidence": len(applied_results) + len(deepseek_edits),
        "deepseek_edit_pairs": len(deepseek_edits),
        "daemon_events": len(daemon),
        "historical_git_mentions": len(historical),
        "recent_job_files": _dedupe(row.get("file") for row in code_jobs[-20:])[:12],
        "read": read,
    }


def _self_fix_audit(root: Path) -> dict[str, Any]:
    docs = sorted((root / "docs" / "self_fix").glob("*.md")) if (root / "docs" / "self_fix").exists() else []
    matches = _git_log(root, ["deepseek", "self-heal", "self fix", "autonomous", "auto"], limit=120)
    improve_words = ("fix", "heal", "healed", "restore", "compile", "health", "hardening", "rollback")
    break_words = ("lost", "timeout", "winerror", "crash", "revert", "broken", "missing")
    improvements = [row for row in matches if any(word in row["subject"].lower() for word in improve_words)]
    breakages = [row for row in matches if any(word in row["subject"].lower() for word in break_words)]
    return {
        "self_fix_docs": len(docs),
        "latest_docs": [path.name for path in docs[-8:]],
        "git_match_count": len(matches),
        "notable_subjects": matches[:14],
        "improvement_subjects": improvements[:20],
        "breakage_subjects": breakages[:20],
        "read": (
            "Self-fix history is real and large, but the evidence is mostly commit/doc-level. "
            "The missing bridge is per-file outcome condensation: pass/fail/rewrite result should "
            "feed file self-knowledge and context clearing."
        ),
    }


def _file_reactions(root: Path, last_prompt: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    files = last_prompt.get("all_files") or []
    packets = {
        item.get("file"): item
        for item in (sources.get("file_self_knowledge") or {}).get("packets") or []
        if isinstance(item, dict)
    }
    rows = []
    for rel in files[:80]:
        if not _looks_like_repo_file(rel):
            continue
        rows.append(_file_reaction(root, rel, packets.get(rel) or {}, sources))
    rows.sort(key=lambda item: (item.get("mutation_events", 0), item.get("tests_found", 0)), reverse=True)
    rules = {
        "schema": "file_context_clearing_rules/v1",
        "ts": _now(),
        "source": "autonomous_mutation_audit",
        "rules": [
            {
                "file": item.get("file"),
                "action": item.get("context_action"),
                "reason": item.get("memory_condensation"),
                "dead_tokens": item.get("dead_tokens", []),
                "requires_tests": item.get("tests_found", 0) == 0,
            }
            for item in rows
        ],
    }
    outcomes = sources.get("learning_outcomes") or []
    read = (
        "Files react today by accumulating identity growth, self-knowledge packets, and mail. "
        "They do not yet react enough to successful/failed rewrites because file_self_sim_learning_outcomes is empty."
    )
    if outcomes:
        read = "File learning outcomes exist; these should now drive derank/clear/rewrite eligibility."
    return {
        "files_audited": len(rows),
        "outcome_rows": len(outcomes),
        "files": rows,
        "context_clearing_rules": rules,
        "read": read,
    }


def _file_reaction(root: Path, rel: str, packet: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    rel = str(rel).replace("\\", "/")
    dead_rows = [
        row for row in sources.get("dead_pairs") or []
        if rel in {_clean(row.get("old_path")), _clean(row.get("new_path"))}
    ]
    growth = [row for row in sources.get("identity_growth") or [] if _clean(row.get("file")) == rel]
    edits = [row for row in sources.get("edit_pairs") or [] if _clean(row.get("file")) == rel]
    outcomes = [row for row in sources.get("learning_outcomes") or [] if _clean(row.get("file")) == rel]
    tests = packet.get("validates_with") or []
    dead_tokens = []
    for row in dead_rows:
        dead_tokens.extend(row.get("dead_tokens") or [])
    mutation_events = len(dead_rows) + len(growth) + len(edits) + len(outcomes)
    tests_found = len([cmd for cmd in tests if "pytest" in str(cmd) or "py_compile" in str(cmd)])
    if tests_found == 0:
        action = "hold_rewrite_map_validation"
    elif outcomes:
        action = "clear_or_rewrite_based_on_outcome_reward"
    elif mutation_events >= 5:
        action = "clear_context_unless_intent_matches_then_allow_bounded_draft"
    elif dead_tokens:
        action = "derank_dead_tokens_before_context"
    else:
        action = "learn_more_before_autonomy"
    return {
        "file": rel,
        "mutation_events": mutation_events,
        "dead_history_events": len(dead_rows),
        "identity_growth_events": len(growth),
        "edit_events": len(edits),
        "outcome_events": len(outcomes),
        "tests_found": tests_found,
        "dead_tokens": _dedupe(dead_tokens)[:12],
        "self_knowledge_packet": packet.get("packet_id", ""),
        "context_action": action,
        "memory_condensation": _memory_condensation(action, mutation_events, tests_found, dead_tokens),
    }


def _memory_condensation(action: str, mutation_events: int, tests_found: int, dead_tokens: list[str]) -> str:
    if action == "hold_rewrite_map_validation":
        return "file must not self-rewrite yet; validation proof is missing"
    if action == "clear_or_rewrite_based_on_outcome_reward":
        return "file has outcome evidence; condense pass/fail into future rewrite eligibility"
    if action == "clear_context_unless_intent_matches_then_allow_bounded_draft":
        return f"file has {mutation_events} mutation signals; keep it out of context unless intent strongly matches"
    if action == "derank_dead_tokens_before_context":
        return f"dead tokens {', '.join(dead_tokens[:5])} should subtract from future wake score"
    return "file needs more edit/outcome/test history before autonomous mutation"


def _operator_read(
    last: dict[str, Any],
    deepseek: dict[str, Any],
    self_fix: dict[str, Any],
    reactions: dict[str, Any],
) -> str:
    return (
        f"Last prompt produced {last.get('distinct_intent_key_count', 0)} distinct structured intent key(s) "
        f"and logged files through {len(last.get('files_logged_by_source') or {})} surfaces. Email is live if "
        f"delivery status says can_send. DeepSeek is mostly queued/dry-run in current logs, while historical "
        f"self-fix is real ({self_fix.get('self_fix_docs', 0)} docs). The missing intelligence is outcome "
        f"condensation: {reactions.get('outcome_rows', 0)} file learning outcome rows means files are not yet "
        f"learning enough from pass/fail mutation results."
    )


def _git_log(root: Path, terms: list[str], limit: int = 80) -> list[dict[str, str]]:
    grep_args = []
    for term in terms:
        grep_args.extend(["--grep", term])
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--extended-regexp",
                "--regexp-ignore-case",
                "--date=short",
                f"-n{limit}",
                "--pretty=format:%h%x09%ad%x09%s",
                *grep_args,
            ],
            cwd=root,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return []
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            rows.append({"short": parts[0], "date": parts[1], "subject": parts[2]})
    return rows


def _same_prompt(a: str, b: Any) -> bool:
    a_norm = _norm(a)
    b_norm = _norm(b)
    if not a_norm or not b_norm:
        return False
    return a_norm == b_norm or a_norm[:160] == b_norm[:160] or b_norm[:160] in a_norm


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _clean(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip()


def _looks_like_repo_file(value: Any) -> bool:
    text = _clean(value)
    return bool(text and (text.endswith((".py", ".md", ".json")) or text.startswith(("src/", "client/", ".github/"))))


def _dedupe(values: Any) -> list[str]:
    seen = set()
    out = []
    for value in values or []:
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
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
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except Exception:
        return []
    rows = []
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit autonomous mutation and file reaction history.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    result = audit_autonomous_mutations(Path(args.root), prompt=args.prompt, write=not args.no_write)
    print(json.dumps({
        "schema": result.get("schema"),
        "last_prompt_intent_keys": (result.get("last_prompt_forensics") or {}).get("distinct_intent_key_count"),
        "deepseek": result.get("deepseek_actuals", {}).get("read"),
        "email_can_send": result.get("email_delivery", {}).get("can_send"),
        "paths": result.get("paths"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["audit_autonomous_mutations", "render_autonomous_mutation_audit"]
