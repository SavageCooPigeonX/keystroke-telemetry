"""AI Cognitive Logger — tracks LLM response quality, fix attempts, and AI cognitive state.

Copilot needs therapy too. This module profiles every AI response (Copilot + Gemini)
the same way keystroke telemetry profiles the human operator:
- Fix attempt chains (did the AI keep retrying the same module?)
- Response rework rate (did the human delete it?)
- Temporal patterns (when does the AI hallucinate most?)
- Module-level miss maps (which files does the AI struggle with?)
- AI cognitive state inference (confident / uncertain / looping / hallucinating)

Writes to: logs/ai_cognitive_log_seq001_v001.jsonl (per-response entries)
           logs/ai_cognitive_state.json (live rolling state)
"""

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = "logs/ai_cognitive_log_seq001_v001.jsonl"
STATE_FILE = "logs/ai_cognitive_state.json"
WINDOW_SIZE = 30  # rolling window for state inference


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_load_jsonl(path: Path, tail: int = 0) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text("utf-8", errors="replace").strip().splitlines()
    if tail:
        lines = lines[-tail:]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def log_ai_response(
    root: Path,
    *,
    source: str,           # "copilot" | "gemini"
    prompt: str,
    response: str,
    modules_referenced: list[str] | None = None,
    file_actions: list[dict] | None = None,
    duration_ms: int = 0,
    selected_node: str | None = None,
) -> dict:
    """Log a single AI response and compute its cognitive signature.

    Returns the log entry dict (also appended to LOG_FILE).
    """
    # Detect modules mentioned in prompt + response
    if modules_referenced is None:
        modules_referenced = _extract_module_refs(prompt + " " + response)

    # Score response characteristics
    response_len = len(response)
    code_blocks = response.count("```")
    has_error = any(w in response.lower() for w in ("error:", "traceback", "exception", "failed"))
    has_apology = any(w in response.lower() for w in ("sorry", "apologize", "mistake", "i was wrong"))
    has_uncertainty = any(w in response.lower() for w in ("i think", "might be", "not sure", "possibly", "perhaps"))

    entry = {
        "ts": _now_iso(),
        "source": source,
        "prompt_len": len(prompt),
        "prompt_hint": prompt[:200],
        "response_len": response_len,
        "response_hint": response[:300],
        "modules_referenced": modules_referenced,
        "file_actions": [{"path": a.get("path"), "ok": a.get("ok")} for a in (file_actions or [])],
        "selected_node": selected_node,
        "duration_ms": duration_ms,
        "signals": {
            "code_blocks": code_blocks,
            "has_error": has_error,
            "has_apology": has_apology,
            "has_uncertainty": has_uncertainty,
        },
    }

    # Append to log
    log_path = root / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Update rolling state
    _update_state(root)

    return entry


def backfill_rework_verdict(root: Path, verdict: str, rework_score: float, query_hint: str) -> None:
    """Attach a rework verdict to the most recent matching AI response.

    Called by the rework detector after the 30-second post-response window.
    Updates the last entry in the log that matches query_hint.
    """
    log_path = root / LOG_FILE
    if not log_path.exists():
        return

    lines = log_path.read_text("utf-8").strip().splitlines()
    # Find last entry matching this query
    for i in range(len(lines) - 1, max(len(lines) - 10, -1), -1):
        try:
            entry = json.loads(lines[i])
            if query_hint and entry.get("prompt_hint", "")[:50] == query_hint[:50]:
                entry["rework_verdict"] = verdict
                entry["rework_score"] = rework_score
                lines[i] = json.dumps(entry)
                log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return
        except Exception:
            pass


def _update_state(root: Path) -> dict:
    """Recompute AI cognitive state from recent log entries."""
    entries = _safe_load_jsonl(root / LOG_FILE, tail=WINDOW_SIZE)
    if not entries:
        return {}

    # Module miss map — which files does the AI struggle with?
    module_attempts = defaultdict(lambda: {"total": 0, "errors": 0, "apologies": 0, "rework_misses": 0})
    for e in entries:
        for mod in e.get("modules_referenced", []):
            ma = module_attempts[mod]
            ma["total"] += 1
            if e.get("signals", {}).get("has_error"):
                ma["errors"] += 1
            if e.get("signals", {}).get("has_apology"):
                ma["apologies"] += 1
            if e.get("rework_verdict") == "miss":
                ma["rework_misses"] += 1

    # Fix attempt chains — consecutive responses about same module
    fix_chains = _detect_fix_chains(entries)

    # Temporal patterns
    total = len(entries)
    error_count = sum(1 for e in entries if e.get("signals", {}).get("has_error"))
    apology_count = sum(1 for e in entries if e.get("signals", {}).get("has_apology"))
    uncertainty_count = sum(1 for e in entries if e.get("signals", {}).get("has_uncertainty"))
    rework_misses = sum(1 for e in entries if e.get("rework_verdict") == "miss")

    # Infer AI cognitive state
    error_rate = error_count / max(total, 1)
    apology_rate = apology_count / max(total, 1)
    miss_rate = rework_misses / max(total, 1)
    chain_count = len([c for c in fix_chains if c["attempts"] >= 3])

    if chain_count >= 2 or error_rate > 0.5:
        ai_state = "looping"
    elif miss_rate > 0.4 or apology_rate > 0.3:
        ai_state = "hallucinating"
    elif uncertainty_count / max(total, 1) > 0.4:
        ai_state = "uncertain"
    elif error_rate < 0.1 and miss_rate < 0.1:
        ai_state = "confident"
    else:
        ai_state = "struggling"

    # Struggling modules — sorted by combined badness
    struggling_modules = []
    for mod, stats in module_attempts.items():
        badness = (stats["errors"] + stats["apologies"] + stats["rework_misses"] * 2) / max(stats["total"], 1)
        if badness > 0.2 or stats["total"] >= 3:
            struggling_modules.append({
                "module": mod,
                "attempts": stats["total"],
                "errors": stats["errors"],
                "misses": stats["rework_misses"],
                "badness": round(badness, 3),
            })
    struggling_modules.sort(key=lambda x: -x["badness"])

    state = {
        "ts": _now_iso(),
        "window_size": total,
        "ai_state": ai_state,
        "error_rate": round(error_rate, 3),
        "apology_rate": round(apology_rate, 3),
        "miss_rate": round(miss_rate, 3),
        "uncertainty_rate": round(uncertainty_count / max(total, 1), 3),
        "fix_chains": fix_chains[:5],
        "struggling_modules": struggling_modules[:10],
        "source_breakdown": _source_breakdown(entries),
    }

    state_path = root / STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    return state


def get_ai_state(root: Path) -> dict:
    """Read the latest AI cognitive state."""
    state_path = root / STATE_FILE
    if not state_path.exists():
        return {"ai_state": "unknown", "window_size": 0}
    try:
        return json.loads(state_path.read_text("utf-8"))
    except Exception:
        return {"ai_state": "unknown", "window_size": 0}


def _detect_fix_chains(entries: list[dict]) -> list[dict]:
    """Find consecutive responses targeting the same module(s).

    A fix chain = 3+ responses in a row referencing overlapping modules.
    This is the AI equivalent of human rework — the AI keeps trying and failing.
    """
    chains = []
    current_mods = set()
    chain_start = 0
    chain_entries = []

    for i, e in enumerate(entries):
        mods = set(e.get("modules_referenced", []))
        if not mods:
            if len(chain_entries) >= 2:
                chains.append(_summarize_chain(chain_entries, current_mods))
            current_mods = set()
            chain_entries = []
            continue

        if current_mods and mods & current_mods:  # overlapping modules
            current_mods |= mods
            chain_entries.append(e)
        else:
            if len(chain_entries) >= 2:
                chains.append(_summarize_chain(chain_entries, current_mods))
            current_mods = mods
            chain_entries = [e]

    if len(chain_entries) >= 2:
        chains.append(_summarize_chain(chain_entries, current_mods))

    return chains


def _summarize_chain(entries: list[dict], modules: set) -> dict:
    errors = sum(1 for e in entries if e.get("signals", {}).get("has_error"))
    return {
        "modules": sorted(modules),
        "attempts": len(entries),
        "errors": errors,
        "first_ts": entries[0].get("ts", ""),
        "last_ts": entries[-1].get("ts", ""),
    }


def _source_breakdown(entries: list[dict]) -> dict:
    breakdown = defaultdict(int)
    for e in entries:
        breakdown[e.get("source", "unknown")] += 1
    return dict(breakdown)


def _extract_module_refs(text: str) -> list[str]:
    """Extract pigeon module names from text using seq pattern matching."""
    import re
    # Match patterns like module_name_seq001, module_seq012_v003, etc.
    pattern = r'\b(\w+_seq\d+)\b'
    matches = re.findall(pattern, text.lower())
    # Deduplicate and normalize — strip version suffixes
    seen = set()
    result = []
    for m in matches:
        # Normalize to base name: xxx_seq001
        base = re.match(r'(\w+_seq\d+)', m)
        if base:
            name = base.group(1)
            if name not in seen:
                seen.add(name)
                result.append(name)
    return result[:10]  # Cap at 10
