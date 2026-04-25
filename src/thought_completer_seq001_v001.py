"""thought_completer_seq001_v001 — primary organ (Phase 2).

Takes a fragment, returns 3 ranked candidate completions + file targets +
confidence. Emits an intent to the ledger on acceptance.

Tiered per D1 (local first):
  - Live (<300ms): learned_pairs lookup + intent key match + local synthesis
  - Cycle (≤5s, optional): LLM enrichment (off by default; enable via
    `complete(..., allow_llm=True)`)

Absorbed responsibilities (§6):
  - prompt_enricher       → renders candidates
  - context_select_agent  → uses intent key + file_affinity to route
  - intent_backlog        → open_fragments() surfaces unclosed emissions
  - intent_numeric        → embedding + match via intent_keys module
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Sequence

# ensure sibling modules importable whether loaded as `src.foo` or `foo`
import sys as _sys
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in _sys.path:
    _sys.path.insert(0, str(_HERE))

from operator_profile_shards_seq001_v001 import (
    ShardStore,
    emit_intent,
    mark_condition,
    search_learned_pairs,
    top_file_affinities,
    write_correction,
    write_learned_pair,
    touch_file_affinity,
    closure_rate_7d,
)
from intent_keys_seq001_v001 import match_fragment, embed

# optional: enrich candidates with historical prompt context (Phase 2.5)
try:
    _SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
    if str(_SCRIPTS) not in _sys.path:
        _sys.path.insert(0, str(_SCRIPTS))
    from prompt_search import (  # type: ignore
        search_api as _prompt_search_api,
        is_cache_warm as _history_cache_warm,
        warm_cache_async as _history_warm_async,
    )
    _history_warm_async()  # prime in background; live path skips until ready
except Exception:
    _prompt_search_api = None  # graceful degrade
    _history_cache_warm = lambda: False  # noqa: E731
    _history_warm_async = lambda: None   # noqa: E731


LIVE_BUDGET_MS = 300
REPO_ROOT = Path(__file__).resolve().parent.parent
INTENT_QUEUE_PATH = REPO_ROOT / "logs" / "completer_intent_queue.jsonl"


@dataclass
class Candidate:
    completion: str
    confidence: float
    source: str                       # "learned_pair" | "synthesized" | "llm"
    intent_key: str | None = None
    file_targets: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class CompleterResult:
    fragment: str
    candidates: list[Candidate]
    intent_keys: list[dict[str, Any]]
    latency_ms: float
    tier: str                          # "live" | "cycle"
    history_hits: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment": self.fragment,
            "candidates": [asdict(c) for c in self.candidates],
            "intent_keys": self.intent_keys,
            "latency_ms": self.latency_ms,
            "tier": self.tier,
            "history_hits": self.history_hits,
        }


# ─── SYNTHESIS ────────────────────────────────────────────────────


def _synthesize_from_key(
    fragment: str,
    key_id: str,
    store: ShardStore,
) -> Candidate | None:
    """Build a completion by leaning on the most-recent learned pair
    for this intent key, falling back to file-affinity-based templating.
    """
    pairs = search_learned_pairs(store, intent_key=key_id, limit=5)
    accepted = [p for p in pairs if p.get("accept_kind") == "accept"]
    if accepted:
        p = accepted[0]
        completion = p["completion"]
        file_targets = json.loads(p["file_targets_json"] or "[]")
        return Candidate(
            completion=completion,
            confidence=min(0.9, 0.5 + 0.08 * len(accepted)),
            source="learned_pair",
            intent_key=key_id,
            file_targets=file_targets,
            rationale=f"reusing accepted completion (n={len(accepted)})",
        )
    # fallback: echo fragment + route by affinity
    files = [r["file_path"] for r in top_file_affinities(store, key_id, limit=3)]
    if files:
        return Candidate(
            completion=f"{fragment} [{key_id}]",
            confidence=0.35,
            source="synthesized",
            intent_key=key_id,
            file_targets=files,
            rationale=f"no learned pairs yet; routed via file_affinity ({len(files)} files)",
        )
    return None


def _literal_passthrough(fragment: str) -> Candidate:
    """Safety fallback: operator's raw fragment becomes the completion."""
    return Candidate(
        completion=fragment,
        confidence=0.25,
        source="synthesized",
        rationale="no intent keys matched; passthrough",
    )


def _queue_emit(
    intent_id: str,
    fragment: str,
    chosen: Candidate,
    session_id: str | None,
) -> None:
    """Append accepted intent to queue file for deepseek/copilot consumers (Phase 4)."""
    INTENT_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "intent_id": intent_id,
        "emitted_at": time.time(),
        "fragment": fragment,
        "completion": chosen.completion,
        "intent_key": chosen.intent_key,
        "file_targets": chosen.file_targets,
        "confidence": chosen.confidence,
        "source": chosen.source,
        "session_id": session_id,
    }
    try:
        with INTENT_QUEUE_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # queue is advisory; core flow must not fail on IO


# ─── CORE API ─────────────────────────────────────────────────────


def complete(
    fragment: str,
    store: ShardStore | None = None,
    top_k_keys: int = 3,
    recent_session_keys: Sequence[str] | None = None,
    open_files: Sequence[str] | None = None,
    allow_llm: bool = False,
) -> CompleterResult:
    """Main entry point. Returns ranked candidates for operator to pick.

    allow_llm defaults False (live lane). Set True to enable cycle-lane
    LLM enrichment — NOT implemented in v1 (hook reserved).
    """
    t0 = time.perf_counter()
    close = False
    if store is None:
        store = ShardStore()
        close = True
    try:
        key_hits = match_fragment(
            store,
            fragment,
            top_k=top_k_keys,
            recent_session_keys=recent_session_keys,
            open_files=open_files,
        )
        candidates: list[Candidate] = []
        seen: set[str] = set()
        for hit in key_hits:
            cand = _synthesize_from_key(fragment, hit["key_id"], store)
            if cand is None:
                continue
            if cand.completion in seen:
                continue
            # attenuate confidence by similarity
            cand.confidence = round(cand.confidence * max(0.2, min(1.0, hit["similarity"] * 2)), 3)
            candidates.append(cand)
            seen.add(cand.completion)

        if not candidates:
            candidates.append(_literal_passthrough(fragment))

        # ── Phase 2.5: RAG-enrich with historical prompt hits (depth+recency+liveness)
        # runs ONLY when cache is already warm (prebuilt at import in bg thread).
        # live lane never blocks on cold index build.
        history_hits: list[dict] = []
        if (_prompt_search_api is not None and fragment.strip()
                and _history_cache_warm()):
            try:
                history_hits = _prompt_search_api(
                    fragment, limit=3,
                    depth=0.7, recency=0.5, liveness=0.3,
                    min_liveness=0.0,
                )
            except Exception:
                history_hits = []
        # attach as rationale augmentation on top candidate
        if history_hits and candidates:
            tops = ", ".join(
                f"{h['ts'][:10]}(score={h['score']})"
                for h in history_hits[:2]
            )
            candidates[0].rationale += f" | history: {tops}"

        # pad to 3 with variants (deterministic)
        while len(candidates) < 3 and len(candidates) < top_k_keys + 1:
            base = candidates[0]
            if f"{base.completion} — routed" in seen:
                break
            candidates.append(Candidate(
                completion=f"{base.completion} — routed",
                confidence=round(base.confidence * 0.7, 3),
                source="synthesized",
                intent_key=base.intent_key,
                file_targets=base.file_targets,
                rationale="variant of top candidate",
            ))
            seen.add(f"{base.completion} — routed")

        candidates.sort(key=lambda c: c.confidence, reverse=True)

        if allow_llm:
            # reserved hook; keeps signature stable for Phase 2+
            candidates.append(Candidate(
                completion="[LLM enrichment not enabled in v1]",
                confidence=0.0,
                source="llm",
                rationale="placeholder",
            ))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        tier = "live" if elapsed_ms <= LIVE_BUDGET_MS else "cycle"

        return CompleterResult(
            fragment=fragment,
            candidates=candidates[:3],
            intent_keys=key_hits,
            latency_ms=round(elapsed_ms, 2),
            tier=tier,
            history_hits=history_hits,
        )
    finally:
        if close:
            store.close()


def accept(
    fragment: str,
    chosen: Candidate,
    store: ShardStore | None = None,
    session_id: str | None = None,
) -> str:
    """Record acceptance → write learned_pair, touch file_affinity, emit intent."""
    close = False
    if store is None:
        store = ShardStore()
        close = True
    try:
        with store.transaction():
            write_learned_pair(
                store,
                fragment=fragment,
                completion=chosen.completion,
                intent_key=chosen.intent_key,
                confidence=chosen.confidence,
                accept_kind="accept",
                file_targets=chosen.file_targets,
                session_id=session_id,
            )
            if chosen.intent_key:
                for fp in chosen.file_targets:
                    touch_file_affinity(store, chosen.intent_key, fp)
            intent_id = emit_intent(
                store,
                fragment=fragment,
                completion=chosen.completion,
                intent_key=chosen.intent_key,
                file_targets=chosen.file_targets,
                session_id=session_id,
            )
        _queue_emit(intent_id, fragment, chosen, session_id)
        return intent_id
    finally:
        if close:
            store.close()


def reject(
    fragment: str,
    rejected: Candidate,
    chosen: Candidate | None = None,
    reason: str | None = None,
    store: ShardStore | None = None,
    session_id: str | None = None,
) -> None:
    close = False
    if store is None:
        store = ShardStore()
        close = True
    try:
        write_correction(
            store,
            fragment=fragment,
            rejected_completion=rejected.completion,
            chosen_completion=chosen.completion if chosen else None,
            intent_key=rejected.intent_key,
            reason=reason,
            session_id=session_id,
        )
    finally:
        if close:
            store.close()


# ─── CLOSURE API (for deepseek / copilot feedback) ────────────────


def mark_routed(store: ShardStore, intent_id: str) -> None:
    mark_condition(store, intent_id, "routed")


def mark_acted(store: ShardStore, intent_id: str) -> None:
    mark_condition(store, intent_id, "acted")


def mark_verified(store: ShardStore, intent_id: str) -> None:
    mark_condition(store, intent_id, "verified")


def mark_stable(store: ShardStore, intent_id: str) -> None:
    mark_condition(store, intent_id, "stable")


# ─── CLI ──────────────────────────────────────────────────────────


def _main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="thought completer")
    p.add_argument("fragment", nargs="?", help="fragment to complete")
    p.add_argument("--accept-idx", type=int, help="auto-accept candidate N (0-based)")
    p.add_argument("--closure-rate", action="store_true")
    args = p.parse_args()

    store = ShardStore()

    if args.closure_rate:
        print(f"intent_closure_rate_7d: {closure_rate_7d(store):.2%}")
        store.close()
        return

    if not args.fragment:
        p.print_help()
        store.close()
        return

    result = complete(args.fragment, store=store)
    print(json.dumps(result.to_dict(), indent=2))

    if args.accept_idx is not None and 0 <= args.accept_idx < len(result.candidates):
        chosen = result.candidates[args.accept_idx]
        intent_id = accept(args.fragment, chosen, store=store, session_id="cli")
        print(f"\nACCEPTED → {chosen.completion}")
        print(f"intent_id: {intent_id}")

    store.close()


if __name__ == "__main__":
    _main()
