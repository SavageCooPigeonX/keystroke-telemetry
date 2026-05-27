"""Analyze prompt-journal behavior, cognition shifts, and response-style rewards.

The script treats the operator's prompt itself as the reinforcement signal:
positive prompts reward the immediately preceding response style, while
negative/corrective prompts punish it. It also builds theme bridges so repeated
ideas can be connected across time instead of flattened into isolated tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


SCHEMA = "prompt_behavior_analysis/v1"


THEMES: dict[str, str] = {
    "codex_probe": r"\b(codex|copilot|chat gpt|gpt)\b",
    "claude_orchestrator": r"\b(claude|opus)\b",
    "execution": r"\b(push|execute|implement|do that|go ahead|fix it|write fix|run actual|open|reload|build it)\b",
    "prompt_history_reconstruction": r"\b(prompt history|prompt journal|journal|logger|keystroke|research|guessed|reconstruct|reconstruction)\b",
    "thinking_partner": r"\b(thinking partner|brainstorm|challenge my thought|adversarial|cognitive partner|viewpoint|stimulate operator|not being a thinking)\b",
    "intent_key_compiler": r"\b(intent ?key|intent compiler|semantic profile|thought completer|numeric|encoded|profile memory|consensus over keys)\b",
    "entity_intelligence": r"\b(entity|audit|profile|irt|grok|deepseek|artifact|news|press release|drift|consensus|mfs|query profile)\b",
    "ui_rendering": r"\b(layout|render|page|directory|stats|chart|hero|dropdown|search bar|frontend|overlap|format|color|wire)\b",
    "file_sim_orchestration": r"\b(file sim|files|manifest|orchestrator|hush|email|rename|interlinked|memory|agent|subagent)\b",
    "voice_style": r"\b(comedy|los santos|unhinged|radio|text chain|personality|tone|vibe|funny|emotional|golden)\b",
}

POSITIVE_PATTERNS = [
    r"\byes\b",
    r"\byes!\b",
    r"\bperfect\b",
    r"\bexactly\b",
    r"\bcloser\b",
    r"\bthat's it\b",
    r"\bthats it\b",
    r"\bfire\b",
    r"\bkiller task\b",
    r"\blooks like.?its working\b",
    r"\bdo that\b",
    r"\bgo ahead\b",
    r"\bpush\b",
    r"\bworks\b",
    r"\bgood\b",
    r"\bnice\b",
    r"\bliked\b",
]

NEGATIVE_PATTERNS = [
    r"\bwrong\b",
    r"\bnope\b",
    r"\bno no\b",
    r"\bnot quite\b",
    r"\bnot what\b",
    r"\bdont like\b",
    r"\bdoesn.?t work\b",
    r"\bdidnt actually\b",
    r"\byou guessed\b",
    r"\bliterally guessed\b",
    r"\bresearch\b",
    r"\bnot being a thinking partner\b",
    r"\bcannot use you to brainstorm\b",
    r"\bweak\b",
    r"\bridiculous\b",
    r"\brobotic\b",
    r"\bterrible\b",
    r"\blame\b",
    r"\bstupid\b",
    r"\bhate\b",
    r"\bshit\b",
    r"\bwtf\b",
    r"\bmistaking my intent\b",
]

CORRECTION_MODES: dict[str, str] = {
    "guessed_without_trace": r"\b(guessed|research|prompt history|journal|logger|keystroke|reconstruct|reconstruction)\b",
    "premature_task_collapse": r"\b(didnt actually think|not being a thinking partner|brainstorm|challenge|adversarial|surface|not quite)\b",
    "fake_or_wrong_data": r"\b(shit data|not real|wrong data|stats are not accurate|garbage|garbadge|stale data)\b",
    "ui_destroyed_signal": r"\b(ugly|layout|render|overlap|removed|too big|hard on the eyes|format|section|dropdown)\b",
    "generic_chatgpt_voice": r"\b(chat gpt|robotic|template|tone smoothing|no personalization|no comedy|terrible)\b",
    "wrong_role_assignment": r"\b(codex|claude|opus|deepseek|orchestrator|grader|probe layer|coding model)\b",
    "missing_intent_key_layer": r"\b(intent key|intent compiler|semantic profile|thought completer|profile memory|consensus)\b",
    "missing_entity_intelligence": r"\b(entity|audit|profile|irt|grok|artifact|news|press release|drift|network|mfs)\b",
}

REWARD_MODES: dict[str, str] = {
    "execute_verified_work": r"\b(push|do that|go ahead|execute|works|working|test|verify|run actual)\b",
    "caught_hidden_architecture": r"\b(yes!|exactly|thats it|that.?s it|closer|fire|killer task|this is exactly)\b",
    "preserved_style_energy": r"\b(comedy|funny|unhinged|text chain|los santos|vibe|personality)\b",
    "used_real_logs": r"\b(prompt history|journal|logger|keystroke|actual|real)\b",
    "supported_intent_compiler": r"\b(intent key|intent compiler|thought completer|semantic profile|encoded)\b",
}

STOPWORDS = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "what",
    "have",
    "want",
    "like",
    "from",
    "your",
    "youre",
    "about",
    "should",
    "there",
    "still",
    "into",
    "they",
    "them",
    "then",
    "also",
    "because",
    "make",
    "work",
    "works",
    "when",
    "where",
    "which",
    "would",
    "could",
    "need",
    "needs",
    "itself",
    "really",
    "actual",
    "actually",
}


@dataclass
class PromptRow:
    raw: dict[str, Any]
    ts: datetime
    session_n: int
    msg: str
    themes: list[str]
    reinforcement: str
    cognitive_load: float
    tokens: list[str]


def _parse_ts(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"ts": "", "msg": line, "parse_error": True})
    return rows


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _themes(text: str) -> list[str]:
    return [name for name, pattern in THEMES.items() if re.search(pattern, text, re.IGNORECASE)]


def _reinforcement(row: dict[str, Any], text: str) -> str:
    positive = _has_any(text, POSITIVE_PATTERNS)
    negative = _has_any(text, NEGATIVE_PATTERNS)
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    if row.get("cognitive_state") == "frustrated":
        return "negative_soft"
    return "neutral"


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


def _bucket_by_day(rows: list[PromptRow]) -> list[dict[str, Any]]:
    groups: dict[str, list[PromptRow]] = defaultdict(list)
    for row in rows:
        groups[row.ts.date().isoformat()].append(row)
    buckets = []
    for day, group in sorted(groups.items()):
        counts = Counter(r.reinforcement for r in group)
        theme_counts = Counter(t for r in group for t in r.themes)
        buckets.append(
            {
                "day": day,
                "prompts": len(group),
                "avg_cognitive_load": round(mean(r.cognitive_load for r in group), 4),
                "reinforcement": dict(counts),
                "top_themes": theme_counts.most_common(6),
                "high_load_sessions": [
                    {"session_n": r.session_n, "load": r.cognitive_load, "msg": r.msg[:180]}
                    for r in sorted(group, key=lambda item: item.cognitive_load, reverse=True)[:3]
                ],
            }
        )
    return buckets


def _theme_reinforcement(rows: list[PromptRow]) -> dict[str, Any]:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for theme in row.themes or ["unclassified"]:
            stats[theme][row.reinforcement] += 1
            if row.reinforcement != "neutral" and len(examples[theme][row.reinforcement]) < 5:
                examples[theme][row.reinforcement].append(
                    {
                        "session_n": row.session_n,
                        "ts": row.ts.isoformat(),
                        "load": row.cognitive_load,
                        "msg": row.msg[:260],
                    }
                )
    result = {}
    for theme, counter in sorted(stats.items()):
        total = sum(counter.values())
        result[theme] = {
            "total": total,
            "positive": counter.get("positive", 0),
            "negative": counter.get("negative", 0) + counter.get("negative_soft", 0),
            "mixed": counter.get("mixed", 0),
            "neutral": counter.get("neutral", 0),
            "positive_rate": round(counter.get("positive", 0) / total, 4) if total else 0,
            "negative_rate": round((counter.get("negative", 0) + counter.get("negative_soft", 0)) / total, 4) if total else 0,
            "examples": examples.get(theme, {}),
        }
    return result


def _cooccurrence_graph(rows: list[PromptRow]) -> dict[str, Any]:
    edge_counts: Counter[tuple[str, str]] = Counter()
    bridges: list[dict[str, Any]] = []
    for row in rows:
        unique_themes = sorted(set(row.themes))
        for i, left in enumerate(unique_themes):
            for right in unique_themes[i + 1 :]:
                edge_counts[(left, right)] += 1
        if len(unique_themes) >= 3 or (row.cognitive_load >= 0.5 and len(unique_themes) >= 2):
            bridges.append(
                {
                    "session_n": row.session_n,
                    "ts": row.ts.isoformat(),
                    "themes": unique_themes,
                    "reinforcement": row.reinforcement,
                    "cognitive_load": row.cognitive_load,
                    "msg": row.msg[:360],
                }
            )
    return {
        "top_edges": [
            {"themes": list(edge), "count": count}
            for edge, count in edge_counts.most_common(30)
        ],
        "bridge_prompts": sorted(bridges, key=lambda item: (len(item["themes"]), item["cognitive_load"]), reverse=True)[:30],
    }


def _shift_points(rows: list[PromptRow], window: int) -> list[dict[str, Any]]:
    if len(rows) < window * 2:
        return []
    shifts = []
    for idx in range(window, len(rows) - window):
        before = rows[idx - window : idx]
        after = rows[idx : idx + window]
        load_delta = mean(r.cognitive_load for r in after) - mean(r.cognitive_load for r in before)
        before_themes = Counter(t for r in before for t in r.themes)
        after_themes = Counter(t for r in after for t in r.themes)
        theme_delta = {
            theme: after_themes.get(theme, 0) - before_themes.get(theme, 0)
            for theme in sorted(set(before_themes) | set(after_themes))
        }
        top_delta = sorted(theme_delta.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        if abs(load_delta) >= 0.07 or any(abs(v) >= max(4, window // 5) for _, v in top_delta):
            row = rows[idx]
            shifts.append(
                {
                    "at_session": row.session_n,
                    "ts": row.ts.isoformat(),
                    "load_delta": round(load_delta, 4),
                    "top_theme_delta": top_delta,
                    "msg": row.msg[:240],
                }
            )
    # Keep separated shift points so the report is readable.
    filtered = []
    last_session = -999
    for item in sorted(shifts, key=lambda x: abs(x["load_delta"]) + sum(abs(v) for _, v in x["top_theme_delta"]) / 20, reverse=True):
        if abs(item["at_session"] - last_session) < max(8, window // 2):
            continue
        filtered.append(item)
        last_session = item["at_session"]
        if len(filtered) >= 12:
            break
    return sorted(filtered, key=lambda x: x["at_session"])


def _emergent_threads(rows: list[PromptRow]) -> list[dict[str, Any]]:
    seed_terms = [
        "intent",
        "keys",
        "profile",
        "audit",
        "artifact",
        "drift",
        "codex",
        "claude",
        "opus",
        "deepseek",
        "files",
        "manifest",
        "hush",
        "thought",
        "completer",
        "reconstruction",
        "brainstorm",
        "research",
    ]
    term_rows: dict[str, list[PromptRow]] = defaultdict(list)
    for row in rows:
        token_set = set(row.tokens)
        for term in seed_terms:
            if term in token_set or term in row.msg.lower():
                term_rows[term].append(row)
    threads = []
    for term, hits in term_rows.items():
        if len(hits) < 3:
            continue
        themes = Counter(t for row in hits for t in row.themes)
        reinf = Counter(row.reinforcement for row in hits)
        first = hits[0]
        last = hits[-1]
        high = sorted(hits, key=lambda r: r.cognitive_load, reverse=True)[:3]
        threads.append(
            {
                "term": term,
                "count": len(hits),
                "first_session": first.session_n,
                "last_session": last.session_n,
                "dominant_themes": themes.most_common(5),
                "reinforcement": dict(reinf),
                "high_load_examples": [
                    {"session_n": row.session_n, "load": row.cognitive_load, "msg": row.msg[:220]}
                    for row in high
                ],
                "compiled_bridge": _compile_bridge(term, hits, themes),
            }
        )
    return sorted(threads, key=lambda item: item["count"], reverse=True)[:18]


def _compile_bridge(term: str, hits: list[PromptRow], themes: Counter[str]) -> str:
    first_theme = themes.most_common(1)[0][0] if themes else "unclassified"
    last = hits[-1].msg[:120]
    return (
        f"{term} behaves like a bridge through {first_theme}: it starts as repeated surface language, "
        f"then reappears under higher load as a routing demand. Latest trace: {last}"
    )


def _mode_matches(text: str, patterns: dict[str, str]) -> list[str]:
    return [name for name, pattern in patterns.items() if re.search(pattern, text, re.IGNORECASE)]


def _context_window(rows: list[PromptRow], index: int, before: int = 3, after: int = 1) -> dict[str, Any]:
    prev_rows = rows[max(0, index - before) : index]
    next_rows = rows[index + 1 : index + 1 + after]
    return {
        "previous": [
            {
                "session_n": item.session_n,
                "reinforcement": item.reinforcement,
                "themes": item.themes,
                "load": item.cognitive_load,
                "msg": item.msg[:220],
            }
            for item in prev_rows
        ],
        "next": [
            {
                "session_n": item.session_n,
                "reinforcement": item.reinforcement,
                "themes": item.themes,
                "load": item.cognitive_load,
                "msg": item.msg[:180],
            }
            for item in next_rows
        ],
    }


def _infer_failed_response_style(row: PromptRow, previous: list[PromptRow]) -> list[str]:
    text = row.msg + " " + " ".join(str(x) for x in row.raw.get("deleted_words") or [])
    modes = _mode_matches(text, CORRECTION_MODES)
    prev_themes = Counter(t for item in previous for t in item.themes)
    if "prompt_history_reconstruction" in prev_themes and "guessed_without_trace" not in modes:
        modes.append("trace_used_too_late_or_too_shallow")
    if "execution" in prev_themes and "premature_task_collapse" not in modes and re.search(r"\b(no|wrong|not quite|dont like)\b", text, re.I):
        modes.append("execution_before_model_alignment")
    if "ui_rendering" in prev_themes and "ui_destroyed_signal" not in modes:
        modes.append("frontend_change_erased_intelligence_signal")
    if not modes and row.reinforcement in {"negative", "negative_soft"}:
        modes.append("unspecified_misalignment")
    return modes


def _infer_rewarded_response_style(row: PromptRow, previous: list[PromptRow]) -> list[str]:
    text = row.msg + " " + " ".join(str(x) for x in row.raw.get("deleted_words") or [])
    modes = _mode_matches(text, REWARD_MODES)
    prev_themes = Counter(t for item in previous for t in item.themes)
    if "execution" in prev_themes and "execute_verified_work" not in modes:
        modes.append("bounded_execution_momentum")
    if "prompt_history_reconstruction" in prev_themes and "used_real_logs" not in modes:
        modes.append("trace_grounded_reconstruction")
    if "intent_key_compiler" in prev_themes and "supported_intent_compiler" not in modes:
        modes.append("intent_key_architecture_preserved")
    if not modes and row.reinforcement == "positive":
        modes.append("positive_but_underspecified")
    return modes


def _behavioral_events(rows: list[PromptRow]) -> dict[str, Any]:
    punishments: list[dict[str, Any]] = []
    rewards: list[dict[str, Any]] = []
    mixed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[max(0, index - 3) : index]
        base = {
            "session_n": row.session_n,
            "ts": row.ts.isoformat(),
            "reinforcement": row.reinforcement,
            "cognitive_load": row.cognitive_load,
            "themes": row.themes,
            "msg": row.msg[:360],
            "deleted_words": row.raw.get("deleted_words") or [],
            "context": _context_window(rows, index),
        }
        if row.reinforcement in {"negative", "negative_soft"}:
            punishments.append(base | {"inferred_failed_response_style": _infer_failed_response_style(row, previous)})
        elif row.reinforcement == "positive":
            rewards.append(base | {"inferred_rewarded_response_style": _infer_rewarded_response_style(row, previous)})
        elif row.reinforcement == "mixed":
            mixed.append(
                base
                | {
                    "inferred_failed_response_style": _infer_failed_response_style(row, previous),
                    "inferred_rewarded_response_style": _infer_rewarded_response_style(row, previous),
                }
            )
    return {
        "punishment_events": sorted(punishments, key=lambda item: item["cognitive_load"], reverse=True)[:40],
        "reward_events": sorted(rewards, key=lambda item: item["cognitive_load"], reverse=True)[:40],
        "mixed_events": sorted(mixed, key=lambda item: item["cognitive_load"], reverse=True)[:20],
        "punishment_mode_counts": Counter(
            mode
            for item in punishments
            for mode in item.get("inferred_failed_response_style", [])
        ).most_common(),
        "reward_mode_counts": Counter(
            mode
            for item in rewards
            for mode in item.get("inferred_rewarded_response_style", [])
        ).most_common(),
    }


def _internal_event_log(rows: list[PromptRow]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[max(0, index - 5) : index]
        previous_themes = Counter(t for item in previous for t in item.themes)
        correction_modes = _infer_failed_response_style(row, previous)
        reward_modes = _infer_rewarded_response_style(row, previous)
        event_type = _event_type(row)
        events.append(
            {
                "schema": "operator_behavior_event/v1",
                "session_n": row.session_n,
                "ts": row.ts.isoformat(),
                "event_type": event_type,
                "operator_state": _operator_state(row),
                "reinforcement": row.reinforcement,
                "cognitive_load": row.cognitive_load,
                "surface_text": row.msg,
                "deleted_words": row.raw.get("deleted_words") or [],
                "themes": row.themes,
                "preceding_context_themes": previous_themes.most_common(6),
                "inferred_trigger": _infer_trigger(row, previous),
                "punished_response_style": correction_modes if event_type in {"punishment", "mixed", "correction"} else [],
                "rewarded_response_style": reward_modes if event_type in {"reward", "mixed"} else [],
                "latent_need": _latent_need(row, correction_modes, reward_modes),
                "next_response_policy": _next_response_policy(row, correction_modes, reward_modes),
                "evidence": {
                    "signals": row.raw.get("signals") or {},
                    "intent_label": row.raw.get("intent"),
                    "cognitive_state_label": row.raw.get("cognitive_state"),
                    "previous_prompts": [
                        {
                            "session_n": item.session_n,
                            "reinforcement": item.reinforcement,
                            "themes": item.themes,
                            "msg": item.msg[:240],
                        }
                        for item in previous[-3:]
                    ],
                },
            }
        )
    return events


def _event_type(row: PromptRow) -> str:
    if row.reinforcement == "positive":
        return "reward"
    if row.reinforcement == "negative":
        return "punishment"
    if row.reinforcement == "negative_soft":
        return "correction"
    if row.reinforcement == "mixed":
        return "mixed"
    if row.cognitive_load >= 0.55:
        return "high_load_exploration"
    return "observation"


def _operator_state(row: PromptRow) -> str:
    if row.reinforcement in {"negative", "negative_soft"} and row.cognitive_load >= 0.55:
        return "high_load_correction"
    if row.reinforcement in {"negative", "negative_soft"}:
        return "correction_pressure"
    if row.reinforcement == "positive" and row.cognitive_load >= 0.45:
        return "excited_alignment"
    if row.reinforcement == "positive":
        return "approval_or_momentum"
    if row.cognitive_load >= 0.55:
        return "dense_architecture_generation"
    if "thinking_partner" in row.themes or "intent_key_compiler" in row.themes:
        return "open_architecture_probe"
    return "routine_prompt"


def _infer_trigger(row: PromptRow, previous: list[PromptRow]) -> str:
    prev_themes = Counter(t for item in previous for t in item.themes)
    if row.reinforcement in {"negative", "negative_soft", "mixed"}:
        if "prompt_history_reconstruction" in row.themes or re.search(r"guessed|research|prompt history|logger", row.msg, re.I):
            return "response likely inferred from surface prompt instead of reconstructing from telemetry."
        if "ui_rendering" in row.themes and "entity_intelligence" in row.themes:
            return "response likely treated interface as layout instead of intelligence-surface contract."
        if "intent_key_compiler" in row.themes:
            return "response likely missed intent-key compiler layer or collapsed it into generic planning."
        if prev_themes.get("execution", 0) >= 2:
            return "execution momentum likely outran intent alignment."
        return "operator is correcting an unresolved mismatch between response and latent system model."
    if row.reinforcement == "positive":
        if "execution" in row.themes:
            return "operator is rewarding bounded action or verifiable forward motion."
        if "intent_key_compiler" in row.themes:
            return "operator is rewarding preservation of the hidden compiler architecture."
        if "prompt_history_reconstruction" in row.themes:
            return "operator is rewarding telemetry-grounded reconstruction."
        return "operator is approving current direction or continuing momentum."
    if row.cognitive_load >= 0.55:
        return "operator is producing dense architecture; answer should preserve residue before simplifying."
    return "no strong trigger detected."


def _latent_need(row: PromptRow, correction_modes: list[str], reward_modes: list[str]) -> str:
    modes = set(correction_modes + reward_modes)
    if "guessed_without_trace" in modes or "trace_used_too_late_or_too_shallow" in modes:
        return "needs evidence-first reconstruction from prompt journal and nearby deleted-word residue."
    if "missing_entity_intelligence" in modes:
        return "needs entity/profile/audit intelligence model preserved under any UI or narrative change."
    if "missing_intent_key_layer" in modes:
        return "needs intent keys treated as intermediate representation across humans, files, entities, and audits."
    if "wrong_role_assignment" in modes:
        return "needs agent roles preserved: Codex probe/interface, Claude/Opus orchestrator, DeepSeek compiler/hands, Grok retrieval/probe."
    if "execute_verified_work" in modes:
        return "wants bounded verified work after the latent architecture is understood."
    if "caught_hidden_architecture" in modes:
        return "wants the hidden architecture named, challenged, and connected to prior traces."
    if row.cognitive_load >= 0.55:
        return "needs thought-preserving expansion before task reduction."
    return "needs concise alignment without inventing certainty."


def _next_response_policy(row: PromptRow, correction_modes: list[str], reward_modes: list[str]) -> str:
    modes = set(correction_modes + reward_modes)
    if row.reinforcement in {"negative", "negative_soft", "mixed"}:
        if "guessed_without_trace" in modes or "trace_used_too_late_or_too_shallow" in modes:
            return "open logs first; quote exact sessions; compile intent keys; only then answer."
        if "execution_before_model_alignment" in modes:
            return "pause implementation; restate hidden compiler test; ask or inspect before patching."
        if "frontend_change_erased_intelligence_signal" in modes or "ui_destroyed_signal" in modes:
            return "treat UI as intelligence expression; preserve prior signal hierarchy before visual changes."
        if "generic_chatgpt_voice" in modes:
            return "drop polished summary; use internal-log style with evidence and repair action."
        return "respond as correction intake: identify violated expectation, evidence, and repair move."
    if row.reinforcement == "positive":
        if "execute_verified_work" in modes:
            return "continue with bounded implementation plus verification; keep evidence visible."
        if "caught_hidden_architecture" in modes:
            return "expand architecture and pressure-test the insight before execution."
        return "continue momentum, but preserve exact operator wording and latent model."
    if row.cognitive_load >= 0.55:
        return "do not summarize away; extract residue, contradictions, and candidate intent keys."
    return "answer directly and keep context light."


def _correction_chains(rows: list[PromptRow]) -> list[dict[str, Any]]:
    chains: list[list[PromptRow]] = []
    current: list[PromptRow] = []
    for row in rows:
        is_correction = row.reinforcement in {"negative", "negative_soft", "mixed"} or row.cognitive_load >= 0.58
        if is_correction:
            current.append(row)
        else:
            if len(current) >= 2:
                chains.append(current)
            current = []
    if len(current) >= 2:
        chains.append(current)

    out = []
    for chain in chains:
        text = " ".join(item.msg for item in chain)
        out.append(
            {
                "start_session": chain[0].session_n,
                "end_session": chain[-1].session_n,
                "duration_prompts": len(chain),
                "avg_load": round(mean(item.cognitive_load for item in chain), 4),
                "themes": Counter(t for item in chain for t in item.themes).most_common(8),
                "correction_modes": Counter(
                    mode
                    for mode in _mode_matches(text, CORRECTION_MODES)
                ).most_common(),
                "operator_log": _chain_logline(chain),
                "evidence": [
                    {"session_n": item.session_n, "load": item.cognitive_load, "msg": item.msg[:260]}
                    for item in chain[:6]
                ],
            }
        )
    return sorted(out, key=lambda item: (item["avg_load"], item["duration_prompts"]), reverse=True)[:25]


def _chain_logline(chain: list[PromptRow]) -> str:
    themes = Counter(t for item in chain for t in item.themes).most_common(3)
    first = chain[0].msg[:120]
    last = chain[-1].msg[:120]
    return (
        f"Correction chain {chain[0].session_n}->{chain[-1].session_n}: "
        f"operator load stayed elevated around {themes}. Initial signal: {first} Latest correction: {last}"
    )


def _role_models(rows: list[PromptRow]) -> dict[str, Any]:
    roles = {
        "codex": r"\b(codex|copilot|chat gpt|gpt)\b",
        "claude_opus": r"\b(claude|opus)\b",
        "deepseek": r"\bdeepseek\b",
        "grok": r"\bgrok\b",
    }
    out: dict[str, Any] = {}
    for role, pattern in roles.items():
        hits = [row for row in rows if re.search(pattern, row.msg, re.I)]
        if not hits:
            continue
        out[role] = {
            "mentions": len(hits),
            "reinforcement": dict(Counter(row.reinforcement for row in hits)),
            "dominant_themes": Counter(t for row in hits for t in row.themes).most_common(8),
            "positive_contexts": [
                {"session_n": row.session_n, "msg": row.msg[:260]}
                for row in hits
                if row.reinforcement == "positive"
            ][:8],
            "negative_contexts": [
                {"session_n": row.session_n, "msg": row.msg[:260]}
                for row in hits
                if row.reinforcement in {"negative", "negative_soft", "mixed"}
            ][:10],
            "compiled_role": _compile_role(role, hits),
        }
    return out


def _compile_role(role: str, hits: list[PromptRow]) -> str:
    text = " ".join(row.msg.lower() for row in hits)
    if role == "codex":
        if "operator prober" in text or "probe" in text:
            return "Codex is being shaped as operator probe, prompt-capture surface, and execution harness; it is punished when it behaves like a generic answerer."
        return "Codex is primarily evaluated as the live interface between operator intent, code context, and execution."
    if role == "claude_opus":
        return "Claude/Opus is repeatedly pulled toward long-horizon orchestration, grader behavior, subagent runtime, and stateful thought holding; adapter failures get punished."
    if role == "deepseek":
        return "DeepSeek is framed as compiler/hands: run consensus, write bounded artifacts, repair schemas, and execute after the probe/orchestrator has clarified intent."
    if role == "grok":
        return "Grok is framed as retrieval/probe intelligence: void search, artifact extraction, entity expansion, and network discovery."
    return "Role unresolved."


def _internal_logs(report: dict[str, Any]) -> list[str]:
    logs = [
        "INTERNAL OPERATOR MODEL LOG",
        f"source={report['source']}",
        f"prompts={report['prompt_count']} schema={report['schema']}",
        "",
        "REWARD MODEL",
    ]
    for mode, count in report["behavioral_events"]["reward_mode_counts"][:10]:
        logs.append(f"REWARD mode={mode} count={count}")
    logs.append("")
    logs.append("PUNISHMENT MODEL")
    for mode, count in report["behavioral_events"]["punishment_mode_counts"][:12]:
        logs.append(f"PUNISH mode={mode} count={count}")
    logs.append("")
    logs.append("HIGH-SIGNAL CORRECTION EVENTS")
    for item in report["behavioral_events"]["punishment_events"][:10]:
        logs.append(
            "OBS "
            f"session={item['session_n']} load={item['cognitive_load']} "
            f"fail={','.join(item['inferred_failed_response_style'])} "
            f"themes={','.join(item['themes'][:4])} :: {item['msg']}"
        )
    logs.append("")
    logs.append("HIGH-SIGNAL REWARD EVENTS")
    for item in report["behavioral_events"]["reward_events"][:8]:
        logs.append(
            "OBS "
            f"session={item['session_n']} load={item['cognitive_load']} "
            f"reward={','.join(item['inferred_rewarded_response_style'])} "
            f"themes={','.join(item['themes'][:4])} :: {item['msg']}"
        )
    logs.append("")
    logs.append("CORRECTION CHAINS")
    for chain in report["correction_chains"][:8]:
        logs.append(f"CHAIN {chain['operator_log']}")
    logs.append("")
    logs.append("ROLE MODEL")
    for role, model in report["role_models"].items():
        logs.append(f"ROLE {role}: {model['compiled_role']}")
    return logs


def _deepseek_prompt(report: dict[str, Any]) -> str:
    compact = {
        "daily": report["daily"][-10:],
        "theme_reinforcement": {
            k: {kk: vv for kk, vv in v.items() if kk != "examples"}
            for k, v in report["theme_reinforcement"].items()
        },
        "shift_points": report["shift_points"],
        "emergent_threads": report["emergent_threads"][:10],
        "graph_edges": report["cooccurrence_graph"]["top_edges"][:12],
        "behavioral_events": {
            "punishment_mode_counts": report["behavioral_events"]["punishment_mode_counts"][:12],
            "reward_mode_counts": report["behavioral_events"]["reward_mode_counts"][:10],
            "punishment_events": report["behavioral_events"]["punishment_events"][:12],
            "reward_events": report["behavioral_events"]["reward_events"][:8],
        },
        "correction_chains": report["correction_chains"][:10],
        "role_models": report["role_models"],
        "internal_log_excerpt": report.get("internal_logs", [])[:60],
    }
    return (
        "You are DeepSeek acting as a cognitive-behavior research auditor for a local prompt journal.\n"
        "Research and reason about cognitive effects of response styles, especially how responses can either "
        "amplify an operator's exploratory cognition or collapse it into frustration.\n\n"
        "Write this like internal product/behavior logs on an operator, not a public-facing empathy essay. "
        "Do not give generic therapy language. Connect the telemetry to concrete response-style mechanisms: "
        "cognitive load, autonomy support, validation vs over-agreement, premature task closure, curiosity, "
        "repair after misattunement, and long-horizon thought scaffolding.\n\n"
        "Use this behavioral analysis artifact:\n"
        f"{json.dumps(compact, indent=2)}\n\n"
        "Required output:\n"
        "1. Identify the response styles that appear positively reinforced.\n"
        "2. Identify response styles that appear negatively reinforced.\n"
        "3. Explain the most likely cognitive shift points.\n"
        "4. Extract the hidden thing the operator is looking for.\n"
        "5. Propose a response policy for future Codex/Claude/DeepSeek roles.\n"
        "6. Emit 12 internal-log style rules that the assistant should follow when this operator is frustrated.\n"
    )


def analyze(root: Path, since: str | None, window: int) -> dict[str, Any]:
    journal = root / "logs" / "prompt_journal.jsonl"
    rows = _prepare(_load_jsonl(journal), since)
    internal_events = _internal_event_log(rows)
    report = {
        "schema": SCHEMA,
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "source": str(journal),
        "since": since,
        "prompt_count": len(rows),
        "daily": _bucket_by_day(rows),
        "theme_reinforcement": _theme_reinforcement(rows),
        "cooccurrence_graph": _cooccurrence_graph(rows),
        "shift_points": _shift_points(rows, max(5, window)),
        "emergent_threads": _emergent_threads(rows),
        "behavioral_events": _behavioral_events(rows),
        "correction_chains": _correction_chains(rows),
        "role_models": _role_models(rows),
        "internal_event_log_path": str(root / "logs" / "operator_behavior_events.jsonl"),
        "internal_event_count": len(internal_events),
        "internal_event_sample": internal_events[-20:],
    }
    report["_internal_events"] = internal_events
    report["internal_logs"] = _internal_logs(report)
    return report


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Internal Operator Behavioral Log",
        "",
        f"- schema: `{report['schema']}`",
        f"- prompts analyzed: `{report['prompt_count']}`",
        f"- source: `{report['source']}`",
        "",
        "## Internal Logs",
        "",
        "```text",
        *report["internal_logs"],
        "```",
        "",
        "## Behavioral Model",
        "",
        "### Rewarded Response Styles",
        "",
    ]
    for mode, count in report["behavioral_events"]["reward_mode_counts"][:12]:
        lines.append(f"- `{mode}` count={count}")
    lines += [
        "",
        "### Punished Response Styles",
        "",
    ]
    for mode, count in report["behavioral_events"]["punishment_mode_counts"][:14]:
        lines.append(f"- `{mode}` count={count}")
    lines += [
        "",
        "### High-Signal Punishment Events",
        "",
    ]
    for item in report["behavioral_events"]["punishment_events"][:14]:
        lines.append(
            f"- session `{item['session_n']}` load={item['cognitive_load']} "
            f"fail={item['inferred_failed_response_style']} :: {item['msg']}"
        )
    lines += [
        "",
        "### High-Signal Reward Events",
        "",
    ]
    for item in report["behavioral_events"]["reward_events"][:12]:
        lines.append(
            f"- session `{item['session_n']}` load={item['cognitive_load']} "
            f"reward={item['inferred_rewarded_response_style']} :: {item['msg']}"
        )
    lines += [
        "",
        "## Correction Chains",
        "",
    ]
    for chain in report["correction_chains"][:12]:
        lines.append(f"- {chain['operator_log']}")
    lines += [
        "",
        "## Role Model",
        "",
    ]
    for role, model in report["role_models"].items():
        lines.append(f"- `{role}`: {model['compiled_role']}")
    lines += [
        "",
        "## Theme Reinforcement",
        "",
    ]
    for theme, stats in sorted(report["theme_reinforcement"].items(), key=lambda kv: kv[1]["negative"], reverse=True):
        lines.append(
            f"- `{theme}` total={stats['total']} positive={stats['positive']} "
            f"negative={stats['negative']} mixed={stats['mixed']} neutral={stats['neutral']}"
        )
    lines += ["", "## Shift Points", ""]
    for item in report["shift_points"]:
        lines.append(
            f"- session `{item['at_session']}` load_delta={item['load_delta']} "
            f"themes={item['top_theme_delta']} :: {item['msg']}"
        )
    lines += ["", "## Emergent Threads", ""]
    for thread in report["emergent_threads"][:12]:
        lines.append(
            f"- `{thread['term']}` count={thread['count']} sessions={thread['first_session']}..{thread['last_session']} "
            f":: {thread['compiled_bridge']}"
        )
    lines += ["", "## DeepSeek Research Prompt", "", "```text", report["deepseek_prompt"], "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_internal_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def _queue_deepseek(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    prompt = report["deepseek_prompt"]
    job_id = "ds-research-" + hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    job = {
        "schema": "deepseek_prompt_job/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "status": "queued",
        "source": "scripts/analyze_prompt_behavior.py",
        "mode": "cognitive_response_style_research",
        "model": "deepseek-v4-pro",
        "prompt": prompt,
        "priority": 1,
        "context_pack_path": "logs/prompt_behavior_analysis_latest.json",
        "autonomous_write": False,
    }
    log = root / "logs" / "deepseek_prompt_jobs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(job, ensure_ascii=False) + "\n")
    _write_json(root / "logs" / "deepseek_prompt_latest.json", job)
    return job


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze prompt-journal behavior and cognitive shift patterns.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--since", default=None, help="ISO timestamp/date lower bound, e.g. 2026-04-25")
    parser.add_argument("--window", type=int, default=25, help="Prompt window for shift detection.")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--queue-deepseek", action="store_true", help="Append a DeepSeek research job using the generated artifact.")
    args = parser.parse_args()

    root = args.root.resolve()
    report = analyze(root, args.since, args.window)
    report["deepseek_prompt"] = _deepseek_prompt(report)

    out_json = args.out_json or root / "logs" / "prompt_behavior_analysis_latest.json"
    out_md = args.out_md or root / "logs" / "prompt_behavior_analysis.md"
    event_log = root / "logs" / "operator_behavior_events.jsonl"
    internal_events = report.pop("_internal_events", [])
    _write_json(out_json, report)
    _write_md(out_md, report)
    _write_internal_events(event_log, internal_events)
    queued = _queue_deepseek(root, report) if args.queue_deepseek else None

    print(json.dumps({
        "schema": report["schema"],
        "prompt_count": report["prompt_count"],
        "json": str(out_json),
        "markdown": str(out_md),
        "operator_behavior_events": str(event_log),
        "operator_behavior_event_count": len(internal_events),
        "deepseek_job": queued.get("job_id") if queued else None,
        "top_negative_themes": [
            [theme, stats["negative"]]
            for theme, stats in sorted(report["theme_reinforcement"].items(), key=lambda kv: kv[1]["negative"], reverse=True)[:6]
        ],
        "shift_count": len(report["shift_points"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
