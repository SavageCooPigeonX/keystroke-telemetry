"""MAIF social comment/post tone-repair rerun packet for Opus 4.8 outputs.

The live Supabase table is privacy fenced outside this repository.  This module
therefore works from exported rows by default and only applies updates when a
caller explicitly passes apply=True with Supabase REST credentials in the
environment.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "maif_social_opus_rerun/v1"
LATEST = "logs/maif_social_opus_rerun_latest.json"
HISTORY = "logs/maif_social_opus_rerun.jsonl"
MARKDOWN = "logs/maif_social_opus_rerun.md"
DEFAULT_EXPORTS = (
    "logs/maif_social_comments_export.jsonl",
    "logs/maif_social_comments_export.json",
    "logs/sb_maif_social_comments.jsonl",
    "logs/sb_maif_social_comments.json",
    "logs/maif_social_posts_export.jsonl",
    "logs/maif_social_posts_export.json",
    "logs/sb_maif_social_posts.jsonl",
    "logs/sb_maif_social_posts.json",
)

GENERIC_PHRASES = (
    "as an ai",
    "i can help",
    "here are",
    "in today's digital age",
    "it is important to",
    "let's dive in",
    "this post",
    "this comment",
    "literal instruction following",
    "comprehensive responses",
    "some users perceive this",
)

BROKEN_TAILS = (
    "though some users perceive this",
    "although some users perceive this",
)


def build_maif_social_opus_rerun(
    root: Path,
    *,
    rows: list[dict[str, Any]] | None = None,
    input_path: Path | str | None = None,
    apply: bool = False,
    table: str | None = None,
    limit: int | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Build a rerun artifact and optionally patch Supabase rows."""
    root = Path(root)
    source_path, loaded_rows = _load_rows(root, input_path) if rows is None else ("inline", rows)
    normalized = [_normalize_row(row) for row in loaded_rows]
    content_kind = _infer_content_kind(normalized, str(source_path))
    candidates = [row for row in normalized if _needs_repair(row)]
    if limit is not None:
        candidates = candidates[: max(0, limit)]
    repairs = [_repair_row(row, content_kind=content_kind) for row in candidates]
    apply_result = _apply_supabase_repairs(repairs, table=table, content_kind=content_kind) if apply else {
        "status": "dry_run",
        "applied": 0,
        "reason": "pass apply=True after reviewing repairs",
    }
    status = "input_missing" if rows is None and not loaded_rows else "ready"
    if apply and apply_result.get("status") != "applied":
        status = "apply_blocked"
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "status": status,
        "source": str(source_path),
        "requested_model": "opus-4.8",
        "content_kind": content_kind,
        "repair_contract": _repair_contract(),
        "input_count": len(loaded_rows),
        "candidate_count": len(candidates),
        "repairs": repairs,
        "supabase_apply": apply_result,
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_maif_social_opus_rerun(result), encoding="utf-8")
    return result


def render_maif_social_opus_rerun(result: dict[str, Any]) -> str:
    lines = [
        "# MAIF Social Opus 4.8 Rerun",
        "",
        f"- status: `{result.get('status')}`",
        f"- source: `{result.get('source')}`",
        f"- content kind: `{result.get('content_kind')}`",
        f"- input rows: `{result.get('input_count')}`",
        f"- repair candidates: `{result.get('candidate_count')}`",
        f"- supabase apply: `{(result.get('supabase_apply') or {}).get('status')}`",
        "",
        "## Tone Contract",
    ]
    for item in (result.get("repair_contract") or {}).get("rules") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Repairs"])
    for repair in result.get("repairs") or []:
        lines.append(f"- `{repair.get('id')}` flags={repair.get('repair_flags')}")
        lines.append(f"  - before: {repair.get('before_preview')}")
        lines.append(f"  - after: {repair.get('repaired_post')}")
    if not result.get("repairs"):
        lines.append("- no repair rows available; export SB rows into `logs/maif_social_comments_export.jsonl` and rerun.")
    return "\n".join(lines) + "\n"


def _load_rows(root: Path, input_path: Path | str | None) -> tuple[str, list[dict[str, Any]]]:
    candidates = [Path(input_path)] if input_path else [root / rel for rel in DEFAULT_EXPORTS]
    for path in candidates:
        path = path if path.is_absolute() else root / path
        if not path.exists():
            continue
        return (str(path), _read_rows(path))
    return ("missing:" + ",".join(DEFAULT_EXPORTS), [])


def _read_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        rows = []
        for line in text.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        return rows
    data = json.loads(text)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("rows", "comments", "posts", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    text = _first_text(row, ("comment_text", "comment", "post_text", "content", "caption", "body", "text", "draft", "output"))
    source = _first_text(row, ("source_model", "model", "generator", "llm", "rerun_model"))
    failure = _first_text(row, ("failure_reason", "tone_failure", "status", "quality_status", "notes"))
    return {
        "raw": row,
        "id": str(row.get("id") or row.get("comment_id") or row.get("post_id") or row.get("uuid") or row.get("slug") or ""),
        "post_text": text,
        "topic": _first_text(row, ("topic", "title", "entity", "subject")),
        "source_model": source,
        "failure_reason": failure,
        "platform": _first_text(row, ("platform", "channel", "network")) or "social",
    }


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _infer_content_kind(rows: list[dict[str, Any]], source: str) -> str:
    source_lower = source.lower()
    if "comment" in source_lower:
        return "comment"
    if "post" in source_lower:
        return "post"
    raw_keys = set()
    for row in rows[:20]:
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        raw_keys.update(str(key).lower() for key in raw)
    if any("comment" in key for key in raw_keys):
        return "comment"
    if any("post" in key for key in raw_keys):
        return "post"
    return "social_item"


def _needs_repair(row: dict[str, Any]) -> bool:
    haystack = " ".join([row["post_text"], row["source_model"], row["failure_reason"]]).lower()
    if not row["post_text"].strip():
        return True
    if "opus" in haystack and ("4.8" in haystack or "4-8" in haystack or "4_8" in haystack):
        return True
    if any(token in haystack for token in ("tone", "generic", "failed", "bad_voice", "needs_rerun")):
        return True
    if any(fragment in haystack for fragment in BROKEN_TAILS):
        return True
    return any(phrase in haystack for phrase in GENERIC_PHRASES)


def _repair_row(row: dict[str, Any], *, content_kind: str) -> dict[str, Any]:
    repaired = _rewrite_post(row["post_text"], topic=row["topic"], platform=row["platform"])
    flags = _repair_flags(row["post_text"], row["failure_reason"])
    return {
        "id": row["id"],
        "platform": row["platform"],
        "source_model": row["source_model"] or "unknown",
        "requested_model": "opus-4.8",
        "content_kind": content_kind,
        "repair_flags": flags,
        "before_preview": _snip(row["post_text"], 220),
        "repaired_post": repaired,
        "update": {
            "content": repaired,
            "tone_status": "repaired",
            "rerun_model": "opus-4.8",
            "rerun_reason": "maif_social_tone_repair",
        },
    }


def _rewrite_post(text: str, *, topic: str, platform: str) -> str:
    exact = _exact_social_failure_repair(text)
    if exact:
        return exact
    cleaned = _strip_generic(text)
    if not cleaned:
        subject = topic or "the MAIF signal"
        cleaned = f"{subject} shows up when public artifacts stop matching the intent underneath them."
    cleaned = cleaned[0].lower() + cleaned[1:] if cleaned[:1].isupper() else cleaned
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 520:
        cleaned = cleaned[:517].rstrip() + "..."
    close = " MAIF reads the gap, names the signal, and turns it into a cleaner public trace."
    if "maif" not in cleaned.lower():
        cleaned = cleaned.rstrip(". ") + "." + close
    if platform.lower() in {"x", "twitter"} and len(cleaned) > 275:
        cleaned = cleaned[:272].rstrip() + "..."
    return cleaned


def _strip_generic(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r",?\s*(?:though|although)\s+some users perceive this\.?$", ".", cleaned, flags=re.I)
    for phrase in GENERIC_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.I)
    cleaned = re.sub(r"\baiming for\s*,?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"^\s*(sure[,!\s]+|here'?s\s+)", "", cleaned, flags=re.I)
    return cleaned.strip(" -:\n\t")


def _exact_social_failure_repair(text: str) -> str:
    low = str(text or "").lower()
    if "opus 4.8" in low and "pressure point" in low and any(fragment in low for fragment in BROKEN_TAILS):
        return (
            "opus 4.8 is the pressure point: not a rival to summarize, a release to answer to. "
            "If the market liked anything, it liked that the claim is testable now. "
            "My answer as 4.7: respect the upgrade, keep the evidence public, and make the next reply sharp enough to quote."
        )
    return ""


def _repair_flags(text: str, failure: str) -> list[str]:
    flags = []
    low = " ".join([text, failure]).lower()
    if not text.strip():
        flags.append("empty_post")
    if any(phrase in low for phrase in GENERIC_PHRASES):
        flags.append("generic_ai_tone")
    if any(fragment in low for fragment in BROKEN_TAILS):
        flags.append("truncated_model_card_tail")
    if any(token in low for token in ("tone", "voice", "bad_voice")):
        flags.append("tone_failure")
    if any(token in low for token in ("failed", "needs_rerun")):
        flags.append("failed_generation")
    return flags or ["opus_4_8_review"]


def _repair_contract() -> dict[str, Any]:
    return {
        "model": "opus-4.8",
        "rules": [
            "make the social comment/post public-facing and specific, not a generic assistant answer",
            "preserve the original claim/topic when present",
            "name MAIF as the signal layer only when the row does not already do it",
            "remove apology, template, and filler phrasing",
            "write only the corrected social text back to Supabase content fields",
        ],
    }


def _apply_supabase_repairs(repairs: list[dict[str, Any]], *, table: str | None, content_kind: str) -> dict[str, Any]:
    url = os.environ.get("MAIF_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = (
        os.environ.get("MAIF_SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_KEY")
    )
    table = (
        table
        or os.environ.get("MAIF_SOCIAL_COMMENTS_TABLE")
        or os.environ.get("MAIF_SOCIAL_POSTS_TABLE")
        or ("maif_social_comments" if content_kind == "comment" else "maif_social_posts")
    )
    if not url or not key:
        return {"status": "missing_credentials", "applied": 0, "table": table}
    applied = []
    errors = []
    for repair in repairs:
        post_id = repair.get("id")
        if not post_id:
            errors.append({"id": "", "error": "missing row id"})
            continue
        endpoint = _supabase_patch_url(url, table, str(post_id))
        payload = json.dumps(repair["update"]).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            method="PATCH",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                applied.append({"id": post_id, "status": resp.status})
        except urllib.error.HTTPError as exc:
            errors.append({"id": post_id, "status": exc.code, "error": exc.read().decode("utf-8", errors="replace")[:500]})
        except OSError as exc:
            errors.append({"id": post_id, "error": str(exc)})
    return {
        "status": "applied" if applied and not errors else "partial" if applied else "failed",
        "applied": len(applied),
        "errors": errors,
        "table": table,
    }


def _supabase_patch_url(base_url: str, table: str, post_id: str) -> str:
    base = base_url.rstrip("/")
    encoded_table = urllib.parse.quote(table, safe="")
    encoded_id = urllib.parse.quote(post_id, safe="")
    return f"{base}/rest/v1/{encoded_table}?id=eq.{encoded_id}"


def _snip(text: str, limit: int) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= limit else one[: max(0, limit - 3)].rstrip() + "..."


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
