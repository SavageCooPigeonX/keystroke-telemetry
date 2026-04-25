"""prompt_search — google-for-prompts over logs/prompt_journal.jsonl

usage:
    python scripts/prompt_search.py "manifest chain"
    python scripts/prompt_search.py "deepseek" --depth 0.7 --recency 0.3
    python scripts/prompt_search.py "chain" --min-liveness 0.5
    python scripts/prompt_search.py --regex "file.?sim" --show-dead
    python scripts/prompt_search.py --module file_sim --limit 5
    python scripts/prompt_search.py --stats
    python scripts/prompt_search.py --dead-report

scoring (weighted mix, tunable):
    score = depth*BM25 + recency*half_life + liveness*ref_alive + phrase_bonus

liveness (answers "can prompts go dead?"):
    module_refs resolved against disk (src/, scripts/, etc).
    dead file -> liveness 0.0 for that ref, 1.0 if alive.
    prompt with all refs missing = zombie (encoding still in intent_keys,
    but file surface evaporated). use --show-dead to surface them,
    --min-liveness to filter out.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JOURNAL = REPO / "logs" / "prompt_journal.jsonl"

# directories scanned to resolve module_refs -> liveness
_MODULE_ROOTS = [REPO / "src", REPO / "scripts", REPO / "client",
                 REPO / "pigeon_compiler", REPO / "pigeon_brain",
                 REPO / "streaming_layer", REPO / "tests"]

_TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")


# ─── liveness (file existence) ────────────────────────────────────

_ALIVE_CACHE: set[str] = set()
_ALIVE_INDEX_BUILT: bool = False


def _build_alive_index() -> None:
    global _ALIVE_INDEX_BUILT
    if _ALIVE_INDEX_BUILT:
        return
    for root in _MODULE_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            _ALIVE_CACHE.add(p.stem)
    _ALIVE_INDEX_BUILT = True


def _ref_is_alive(ref: str) -> bool:
    _build_alive_index()
    if not ref:
        return False
    stem = Path(ref).stem
    # fast O(1) exact stem check; substring fallback only for short refs
    if stem in _ALIVE_CACHE:
        return True
    if len(stem) >= 8:
        # try prefix match (pigeon files carry long suffixes)
        for name in _ALIVE_CACHE:
            if name.startswith(stem[:8]):
                return True
    return False


_LIVENESS_CACHE: dict[tuple, float] = {}


def _liveness_score(module_refs: list) -> float:
    if not module_refs:
        return 1.0
    key = tuple(sorted(str(r) for r in module_refs))
    cached = _LIVENESS_CACHE.get(key)
    if cached is not None:
        return cached
    alive = sum(1 for r in module_refs if _ref_is_alive(str(r)))
    score = alive / len(module_refs)
    _LIVENESS_CACHE[key] = score
    return score


def _tok(s: str) -> list[str]:
    return _TOKEN_RE.findall((s or "").lower())


def _load(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


# cached journal + index, invalidated on mtime change (for live-lane RAG)
_JOURNAL_CACHE: dict = {"mtime": 0.0, "records": [], "docs_true": None,
                        "df_true": None, "N_true": 0, "avgdl_true": 0.0,
                        "docs_false": None, "df_false": None,
                        "N_false": 0, "avgdl_false": 0.0}


def _cached_records() -> list[dict]:
    try:
        mt = JOURNAL.stat().st_mtime
    except OSError:
        return []
    if mt != _JOURNAL_CACHE["mtime"]:
        _JOURNAL_CACHE["mtime"] = mt
        _JOURNAL_CACHE["records"] = _load(JOURNAL)
        _JOURNAL_CACHE["docs_true"] = None
        _JOURNAL_CACHE["docs_false"] = None
    return _JOURNAL_CACHE["records"]


def _cached_index(include_deleted: bool):
    key = "true" if include_deleted else "false"
    if _JOURNAL_CACHE[f"docs_{key}"] is None:
        docs, df, N, avgdl = _build_index(_JOURNAL_CACHE["records"], include_deleted)
        _JOURNAL_CACHE[f"docs_{key}"] = docs
        _JOURNAL_CACHE[f"df_{key}"] = df
        _JOURNAL_CACHE[f"N_{key}"] = N
        _JOURNAL_CACHE[f"avgdl_{key}"] = avgdl
    return (_JOURNAL_CACHE[f"docs_{key}"], _JOURNAL_CACHE[f"df_{key}"],
            _JOURNAL_CACHE[f"N_{key}"], _JOURNAL_CACHE[f"avgdl_{key}"])


def _record_text(r: dict, include_deleted: bool) -> str:
    parts = [r.get("msg") or r.get("preview") or ""]
    if include_deleted:
        dw = r.get("deleted_words") or []
        parts.extend(str(x) for x in dw)
    mods = r.get("module_refs") or []
    parts.extend(str(x) for x in mods)
    parts.append(r.get("intent") or "")
    parts.append(r.get("cognitive_state") or "")
    return " ".join(parts)


def _parse_ts(s: str) -> float:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _build_index(records: list[dict], include_deleted: bool):
    docs = [_tok(_record_text(r, include_deleted)) for r in records]
    df: Counter = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    N = max(1, len(docs))
    avgdl = sum(len(d) for d in docs) / N if docs else 0.0
    return docs, df, N, avgdl


def _bm25(qtoks: list[str], doc: list[str], df: Counter, N: int, avgdl: float,
          k1: float = 1.4, b: float = 0.75) -> float:
    if not doc:
        return 0.0
    tf = Counter(doc)
    dl = len(doc)
    score = 0.0
    for q in qtoks:
        if q not in tf:
            continue
        n = df.get(q, 0)
        if n == 0:
            continue
        idf = math.log(1 + (N - n + 0.5) / (n + 0.5))
        f = tf[q]
        denom = f + k1 * (1 - b + b * dl / (avgdl or 1))
        score += idf * f * (k1 + 1) / denom
    return score


def _recency_boost(ts: float, now: float, half_life_days: float = 7.0) -> float:
    if ts <= 0:
        return 0.0
    age_days = max(0.0, (now - ts) / 86400.0)
    return 0.5 * (0.5 ** (age_days / half_life_days))


def _phrase_bonus(query: str, text: str) -> float:
    return 2.0 if query and query.lower() in (text or "").lower() else 0.0


def _filter(r: dict, args) -> bool:
    if args.since:
        if _parse_ts(r.get("ts", "")) < _parse_ts(args.since):
            return False
    if args.until:
        if _parse_ts(r.get("ts", "")) > _parse_ts(args.until):
            return False
    if args.intent and (r.get("intent") or "").lower() != args.intent.lower():
        return False
    if args.state and (r.get("cognitive_state") or "").lower() != args.state.lower():
        return False
    if args.module:
        mods = [str(m).lower() for m in (r.get("module_refs") or [])]
        if not any(args.module.lower() in m for m in mods):
            return False
    return True


def _highlight(text: str, query: str, regex: bool) -> str:
    if not text:
        return ""
    try:
        if regex and query:
            return re.sub(f"({query})", r"[\1]", text, flags=re.IGNORECASE)
        if query:
            for q in _tok(query):
                text = re.sub(f"(?i)({re.escape(q)})", r"[\1]", text)
    except re.error:
        pass
    return text


def search(query: str, args) -> list[tuple[float, dict, dict]]:
    """Return [(score, record, breakdown), ...] sorted desc."""
    any_filter = any([args.since, args.until, args.intent, args.state, args.module])
    if any_filter:
        records = [r for r in _load(JOURNAL) if _filter(r, args)]
        docs_built = False
    else:
        records = _cached_records()
        docs_built = True  # cached index covers all records
    now = datetime.now(timezone.utc).timestamp()
    w_depth = float(args.depth)
    w_recency = float(args.recency)
    w_live = float(args.liveness)

    if args.regex and query:
        try:
            pat = re.compile(query, re.IGNORECASE)
        except re.error as e:
            print(f"bad regex: {e}", file=sys.stderr); sys.exit(2)
        hits = []
        for r in records:
            text = _record_text(r, args.include_deleted)
            if not pat.search(text):
                continue
            rec_boost = _recency_boost(_parse_ts(r.get("ts", "")), now)
            live = _liveness_score(r.get("module_refs") or [])
            if live < args.min_liveness and not args.show_dead:
                continue
            score = 1.0 + w_recency * rec_boost + w_live * live
            hits.append((score, r, {"bm25": 0.0, "recency": rec_boost, "liveness": live}))
        hits.sort(key=lambda x: -x[0])
        return hits

    if docs_built:
        docs, df, N, avgdl = _cached_index(args.include_deleted)
    else:
        docs, df, N, avgdl = _build_index(records, args.include_deleted)
    qtoks = _tok(query)
    scored = []
    for r, d in zip(records, docs):
        bm25 = _bm25(qtoks, d, df, N, avgdl)
        rec = _recency_boost(_parse_ts(r.get("ts", "")), now)
        live = _liveness_score(r.get("module_refs") or [])
        phrase = _phrase_bonus(query, _record_text(r, args.include_deleted)) if query else 0.0
        if live < args.min_liveness and not args.show_dead:
            continue
        score = w_depth * bm25 + w_recency * rec + w_live * live + phrase
        if score > 0 or not query:
            scored.append((score, r, {"bm25": bm25, "recency": rec, "liveness": live, "phrase": phrase}))
    scored.sort(key=lambda x: -x[0])
    return scored


def _stats():
    records = _load(JOURNAL)
    if not records:
        print("empty journal"); return
    intents = Counter((r.get("intent") or "?") for r in records)
    states = Counter((r.get("cognitive_state") or "?") for r in records)
    with_del = sum(1 for r in records if r.get("deleted_words"))
    dead = sum(1 for r in records if (r.get("module_refs") and _liveness_score(r["module_refs"]) == 0.0))
    partial_dead = sum(1 for r in records if (r.get("module_refs") and 0 < _liveness_score(r["module_refs"]) < 1.0))
    first = records[0].get("ts"); last = records[-1].get("ts")
    print(f"records:      {len(records)}")
    print(f"first:        {first}")
    print(f"last:         {last}")
    print(f"with deletes: {with_del} ({100*with_del/len(records):.1f}%)")
    print(f"fully dead:   {dead}  (all module_refs missing from disk)")
    print(f"partial dead: {partial_dead}  (some module_refs missing)")
    print(f"\nintents:      {dict(intents.most_common(8))}")
    print(f"states:       {dict(states.most_common(8))}")


def _dead_report(limit: int = 25):
    """Show prompts whose referenced modules no longer exist."""
    records = _load(JOURNAL)
    dead_records = []
    for r in records:
        refs = r.get("module_refs") or []
        if not refs:
            continue
        missing = [x for x in refs if not _ref_is_alive(str(x))]
        if missing:
            dead_records.append((r.get("ts"), r.get("msg") or "", refs, missing))
    dead_records.sort(key=lambda x: x[0] or "", reverse=True)
    print(f"dead/zombie prompts: {len(dead_records)}  (showing last {limit})\n")
    for ts, msg, refs, missing in dead_records[:limit]:
        print(f"[{ts}]")
        print(f"  msg:     {msg[:140]!r}")
        print(f"  refs:    {refs}")
        print(f"  missing: {missing}\n")


def is_cache_warm() -> bool:
    """Cheap probe: can search_api run in <100ms?"""
    return _JOURNAL_CACHE["docs_true"] is not None


def warm_cache_async() -> None:
    """Kick off cache build in background thread. Non-blocking."""
    import threading
    def _warm():
        try:
            _cached_records()
            _cached_index(True)
            _build_alive_index()
        except Exception:
            pass
    threading.Thread(target=_warm, daemon=True).start()


def search_api(query: str, limit: int = 5, min_liveness: float = 0.0,
               depth: float = 1.0, recency: float = 0.5, liveness: float = 0.3,
               include_deleted: bool = True) -> list[dict]:
    """Programmatic entry point. Used by thought_completer for RAG.

    Returns list of {score, ts, msg, intent, state, module_refs, deleted_words,
    breakdown:{bm25, recency, liveness, phrase}}.
    """
    class _A:
        pass
    a = _A()
    a.regex = False; a.include_deleted = include_deleted
    a.since = None; a.until = None; a.intent = None; a.state = None; a.module = None
    a.depth = depth; a.recency = recency; a.liveness = liveness
    a.min_liveness = min_liveness; a.show_dead = True
    hits = search(query, a)[:limit]
    return [
        {"score": round(s, 3),
         "ts": r.get("ts"),
         "msg": (r.get("msg") or r.get("preview") or "")[:400],
         "intent": r.get("intent"),
         "state": r.get("cognitive_state"),
         "module_refs": r.get("module_refs") or [],
         "deleted_words": r.get("deleted_words") or [],
         "breakdown": {k: round(v, 3) for k, v in br.items()}}
        for s, r, br in hits
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="search prompt_journal.jsonl")
    ap.add_argument("query", nargs="?", default="", help="search query (tokens OR regex)")
    ap.add_argument("--regex", action="store_true", help="treat query as regex")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--include-deleted", action="store_true", default=True,
                    help="search deleted words too (default on)")
    ap.add_argument("--no-deleted", dest="include_deleted", action="store_false")
    ap.add_argument("--depth", type=float, default=1.0,
                    help="weight for BM25 token-depth match (default 1.0)")
    ap.add_argument("--recency", type=float, default=0.5,
                    help="weight for recency boost (default 0.5)")
    ap.add_argument("--liveness", type=float, default=0.3,
                    help="weight for module_ref alive-score (default 0.3)")
    ap.add_argument("--min-liveness", type=float, default=0.0,
                    help="drop prompts whose refs alive-ratio < this")
    ap.add_argument("--show-dead", action="store_true",
                    help="include zombie prompts (refs missing from disk)")
    ap.add_argument("--since", help="ISO date/time lower bound")
    ap.add_argument("--until", help="ISO date/time upper bound")
    ap.add_argument("--intent", help="filter by intent exact match")
    ap.add_argument("--state", help="filter by cognitive_state exact match")
    ap.add_argument("--module", help="filter: module_refs contains substring")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of pretty")
    ap.add_argument("--stats", action="store_true", help="journal stats and exit")
    ap.add_argument("--dead-report", action="store_true",
                    help="list prompts with missing module_refs and exit")
    args = ap.parse_args()

    if args.stats:
        _stats(); return 0
    if args.dead_report:
        _dead_report(limit=args.limit); return 0

    hits = search(args.query, args)[: args.limit]

    if args.json:
        out = [{"score": s, "breakdown": br,
                **{k: r.get(k) for k in
                   ("ts", "msg", "preview", "intent", "cognitive_state",
                    "deleted_words", "module_refs")}}
               for s, r, br in hits]
        print(json.dumps(out, indent=2, default=str))
        return 0

    print(f"query: {args.query!r}  hits: {len(hits)}  "
          f"(weights: depth={args.depth} recency={args.recency} liveness={args.liveness})\n")
    for i, (score, r, br) in enumerate(hits, 1):
        ts = r.get("ts", "?")
        msg = r.get("msg") or r.get("preview") or ""
        msg = _highlight(msg, args.query, args.regex)
        intent = r.get("intent") or "?"
        state = r.get("cognitive_state") or "?"
        mods = r.get("module_refs") or []
        dw = r.get("deleted_words") or []
        live_tag = f"live={br['liveness']:.2f}" if mods else "live=n/a"
        print(f"[{i:>2}] score={score:.2f}  {ts}  intent={intent}  state={state}  "
              f"bm25={br['bm25']:.2f} rec={br['recency']:.2f} {live_tag}")
        if msg.strip():
            print(f"     msg: {msg[:260]}")
        if dw:
            print(f"     deleted: {dw}")
        if mods:
            print(f"     modules: {mods[:6]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
