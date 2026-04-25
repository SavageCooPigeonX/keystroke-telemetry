"""intent_keys_seq001_v001 — intent key lifecycle + clustering.

Phase 1 of THOUGHT_COMPLETER_PLAN.

responsibilities:
  - embed fragments into fixed-dim vectors (D2: sentence-transformers if
    installed, hashed n-gram fallback otherwise)
  - cluster prompt history into intent keys
  - manage lifecycle: birth/growth/split/merge/sleep/death
  - match a new fragment against active keys → ranked [(key_id, similarity)]
  - backfill from logs/prompt_journal.jsonl

writes to: intent_keys table (via operator_profile_shards).
no other module writes intent_keys. lane C (background) for lifecycle,
lane A (live) for match_fragment().
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
import math
import re
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

# ensure sibling modules importable whether loaded as `src.foo` or `foo`
import sys as _sys
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in _sys.path:
    _sys.path.insert(0, str(_HERE))

from operator_profile_shards_seq001_v001 import (
    ShardStore,
    bump_intent_key_match,
    upsert_intent_key,
)

EMBED_DIM = 384  # matches all-MiniLM-L6-v2 for drop-in upgrade later
SIM_BIRTH_THRESHOLD = 0.55      # new fragment must exceed this to join an existing key
CLUSTER_MIN_MEMBERS = 5         # §3.2 birth rule
DORMANT_SECS = 30 * 86400       # §3.2 sleep
ARCHIVE_SECS = 90 * 86400       # §3.2 death
TIE_WINDOW = 0.05               # D4 tiebreaker window


# ─── EMBEDDING ────────────────────────────────────────────────────


class _Embedder:
    """Pluggable embedder. Prefers sentence-transformers if installed."""

    def __init__(self) -> None:
        self._st_model: Any = None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.backend = "sentence-transformers"
            self.dim = 384
        except Exception:
            self.backend = "hashed-ngram"
            self.dim = EMBED_DIM

    def embed(self, text: str) -> list[float]:
        if self._st_model is not None:
            vec = self._st_model.encode(text, normalize_embeddings=True)
            return [float(x) for x in vec.tolist()]
        return _hashed_ngram_vec(text, self.dim)


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    return _NON_ALNUM.sub(" ", text.lower()).strip()


def _hashed_ngram_vec(text: str, dim: int) -> list[float]:
    """Deterministic char-3gram + word-1gram hashed vector, L2-normalized.

    Good enough for short fragment similarity. Zero dependencies.
    """
    norm = _normalize(text)
    if not norm:
        return [0.0] * dim
    vec = [0.0] * dim
    # char 3-grams
    padded = f"  {norm}  "
    for i in range(len(padded) - 2):
        tri = padded[i : i + 3]
        h = int.from_bytes(hashlib.blake2b(tri.encode(), digest_size=8).digest(), "big")
        idx = h % dim
        sign = 1.0 if (h >> 63) & 1 else -1.0
        vec[idx] += sign
    # word tokens
    for tok in norm.split():
        if not tok:
            continue
        h = int.from_bytes(hashlib.blake2b(tok.encode(), digest_size=8).digest(), "big")
        idx = h % dim
        sign = 1.0 if (h >> 63) & 1 else -1.0
        vec[idx] += sign * 2.0  # words weighted higher than chars
    # L2 normalize
    norm_val = math.sqrt(sum(x * x for x in vec))
    if norm_val == 0:
        return vec
    return [x / norm_val for x in vec]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    # assume both pre-normalized
    return dot


_embedder: _Embedder | None = None


def get_embedder() -> _Embedder:
    global _embedder
    if _embedder is None:
        _embedder = _Embedder()
    return _embedder


def embed(text: str) -> list[float]:
    return get_embedder().embed(text)


# ─── CLUSTERING ───────────────────────────────────────────────────


def _agglomerative_cluster(
    vecs: list[list[float]],
    threshold: float = SIM_BIRTH_THRESHOLD,
) -> list[list[int]]:
    """Single-linkage agglomerative clustering by cosine similarity.

    Returns list of clusters, each cluster is a list of indices into `vecs`.
    O(n^2) — fine for seeding from ~1k historical prompts.
    """
    n = len(vecs)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if cosine(vecs[i], vecs[j]) >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def _centroid(vecs: Sequence[Sequence[float]]) -> list[float]:
    if not vecs:
        return [0.0] * EMBED_DIM
    dim = len(vecs[0])
    acc = [0.0] * dim
    for v in vecs:
        for i, x in enumerate(v):
            acc[i] += x
    n = len(vecs)
    acc = [x / n for x in acc]
    norm_val = math.sqrt(sum(x * x for x in acc))
    if norm_val == 0:
        return acc
    return [x / norm_val for x in acc]


def _propose_key_id(fragments: Sequence[str], idx: int) -> str:
    """Derive a stable, readable key_id from cluster content."""
    joined = " ".join(fragments[:6]).lower()
    words = [w for w in re.findall(r"[a-z]{4,}", joined)]
    stop = {
        "this", "that", "with", "from", "have", "been", "were", "they",
        "them", "then", "than", "will", "would", "should", "could",
        "about", "when", "what", "which", "where", "there", "their",
        "your", "youre", "dont", "doesnt", "cant", "maybe", "like",
        "just", "still", "also", "into", "onto", "some", "thing",
        "things", "really", "need", "needs", "make", "made",
    }
    terms = [w for w in words if w not in stop][:2]
    if not terms:
        terms = [f"cluster{idx}"]
    return "k_" + "_".join(terms)


# ─── SEED / BACKFILL ──────────────────────────────────────────────


def _load_journal_messages(path: Path, min_chars: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("msg") or ""
        if not isinstance(msg, str) or len(msg.strip()) < min_chars:
            continue
        out.append(rec)
    return out


def seed_from_journal(
    store: ShardStore,
    journal_path: Path | str = Path("logs/prompt_journal.jsonl"),
    max_records: int = 1000,
    min_cluster_size: int = CLUSTER_MIN_MEMBERS,
) -> dict[str, Any]:
    """Backfill intent_keys from historical prompts.

    Returns summary dict with counts.
    """
    path = Path(journal_path)
    records = _load_journal_messages(path)[-max_records:]
    if not records:
        return {"records": 0, "clusters": 0, "keys_created": 0}

    fragments = [r["msg"][:400] for r in records]
    vecs = [embed(f) for f in fragments]
    clusters = _agglomerative_cluster(vecs)
    # keep only sufficiently-supported clusters
    clusters = [c for c in clusters if len(c) >= min_cluster_size]
    clusters.sort(key=len, reverse=True)

    created = 0
    for idx, member_idxs in enumerate(clusters):
        member_vecs = [vecs[i] for i in member_idxs]
        member_frags = [fragments[i] for i in member_idxs]
        centroid = _centroid(member_vecs)
        key_id = _propose_key_id(member_frags, idx)
        # disambiguate collisions
        base = key_id
        suffix = 2
        existing = {r["key_id"] for r in store.conn.execute(
            "SELECT key_id FROM intent_keys"
        ).fetchall()}
        while key_id in existing:
            key_id = f"{base}_{suffix}"
            suffix += 1
        upsert_intent_key(
            store,
            key_id=key_id,
            centroid_vec=centroid,
            state="active",
            meta={
                "seeded_from": str(path.name),
                "seed_size": len(member_idxs),
                "seed_sample_fragments": member_frags[:3],
            },
        )
        # backfill match count
        store.conn.execute(
            "UPDATE intent_keys SET match_count = ? WHERE key_id = ?",
            (len(member_idxs), key_id),
        )
        created += 1

    return {
        "records": len(records),
        "clusters": len(clusters),
        "keys_created": created,
        "embedder": get_embedder().backend,
    }


# ─── MATCH (live, lane A) ─────────────────────────────────────────


def match_fragment(
    store: ShardStore,
    fragment: str,
    top_k: int = 3,
    recent_session_keys: Sequence[str] | None = None,
    open_files: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Return top-K intent keys for a fragment with D4 tiebreaking.

    Output: [{key_id, similarity, reason}, ...] ordered by similarity desc.
    Reason tags: "cosine", "tiebreak:recency", "tiebreak:file_cooccurrence".
    """
    frag_vec = embed(fragment)
    rows = store.conn.execute(
        "SELECT key_id, centroid_vec FROM intent_keys WHERE state = 'active'"
    ).fetchall()
    if not rows:
        return []
    scored: list[tuple[str, float]] = []
    for r in rows:
        try:
            cv = json.loads(r["centroid_vec"])
        except Exception:
            continue
        if len(cv) != len(frag_vec):
            continue
        scored.append((r["key_id"], cosine(frag_vec, cv)))
    scored.sort(key=lambda kv: kv[1], reverse=True)

    # D4: tiered tiebreaker for ties within TIE_WINDOW
    results: list[dict[str, Any]] = []
    if not scored:
        return results

    top_sim = scored[0][1]
    tied: list[tuple[str, float]] = []
    rest: list[tuple[str, float]] = []
    for kid, sim in scored:
        if top_sim - sim <= TIE_WINDOW:
            tied.append((kid, sim))
        else:
            rest.append((kid, sim))

    if len(tied) == 1:
        results.append({"key_id": tied[0][0], "similarity": tied[0][1], "reason": "cosine"})
    else:
        # tier 1: recency
        recent_set = set(recent_session_keys or [])
        tied_sorted = sorted(
            tied,
            key=lambda kv: (kv[0] in recent_set, kv[1]),
            reverse=True,
        )
        if tied_sorted[0][0] in recent_set and (
            len(tied_sorted) == 1 or tied_sorted[1][0] not in recent_set
        ):
            results.append({
                "key_id": tied_sorted[0][0],
                "similarity": tied_sorted[0][1],
                "reason": "tiebreak:recency",
            })
            tied_sorted = tied_sorted[1:]
        else:
            # tier 2: file co-occurrence
            if open_files:
                placeholders = ",".join("?" * len(open_files))
                key_ids = [kid for kid, _ in tied_sorted]
                kid_ph = ",".join("?" * len(key_ids))
                cooc = store.conn.execute(
                    f"SELECT intent_key, SUM(touch_count) AS score "
                    f"FROM shard_file_affinity "
                    f"WHERE intent_key IN ({kid_ph}) AND file_path IN ({placeholders}) "
                    f"GROUP BY intent_key",
                    (*key_ids, *open_files),
                ).fetchall()
                cooc_map = {r["intent_key"]: r["score"] or 0 for r in cooc}
                if cooc_map:
                    tied_sorted.sort(
                        key=lambda kv: (cooc_map.get(kv[0], 0), kv[1]),
                        reverse=True,
                    )
                    if cooc_map.get(tied_sorted[0][0], 0) > 0:
                        results.append({
                            "key_id": tied_sorted[0][0],
                            "similarity": tied_sorted[0][1],
                            "reason": "tiebreak:file_cooccurrence",
                        })
                        tied_sorted = tied_sorted[1:]
        # remaining ties: surface all — operator tier 3 resolves in UI
        for kid, sim in tied_sorted:
            if any(r["key_id"] == kid for r in results):
                continue
            results.append({"key_id": kid, "similarity": sim, "reason": "tiebreak:operator_pick"})

    for kid, sim in rest:
        if len(results) >= top_k:
            break
        results.append({"key_id": kid, "similarity": sim, "reason": "cosine"})

    if results:
        bump_intent_key_match(store, results[0]["key_id"])

    return results[:top_k]


# ─── LIFECYCLE (lane C, background) ───────────────────────────────


def sweep_lifecycle(store: ShardStore, now: float | None = None) -> dict[str, int]:
    """Apply sleep/archive based on last_match_at. Returns counts."""
    t = now or time.time()
    slept = store.conn.execute(
        "UPDATE intent_keys SET state = 'dormant' "
        "WHERE state = 'active' AND last_match_at < ?",
        (t - DORMANT_SECS,),
    ).rowcount
    archived = store.conn.execute(
        "UPDATE intent_keys SET state = 'archived' "
        "WHERE state = 'dormant' AND last_match_at < ?",
        (t - ARCHIVE_SECS,),
    ).rowcount
    return {"slept": slept or 0, "archived": archived or 0}


# ─── CLI ──────────────────────────────────────────────────────────


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="intent key lifecycle + seed")
    parser.add_argument("--seed", action="store_true", help="seed from prompt_journal")
    parser.add_argument("--match", type=str, help="match a fragment and print top keys")
    parser.add_argument("--sweep", action="store_true", help="run lifecycle sweep")
    parser.add_argument("--list", action="store_true", help="list active keys")
    parser.add_argument("--journal", type=str, default="logs/prompt_journal.jsonl")
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--min-cluster", type=int, default=CLUSTER_MIN_MEMBERS)
    args = parser.parse_args()

    store = ShardStore()

    if args.seed:
        summary = seed_from_journal(
            store,
            journal_path=args.journal,
            max_records=args.max_records,
            min_cluster_size=args.min_cluster,
        )
        print(json.dumps(summary, indent=2))

    if args.match:
        hits = match_fragment(store, args.match, top_k=5)
        print(json.dumps(hits, indent=2))

    if args.sweep:
        print(json.dumps(sweep_lifecycle(store), indent=2))

    if args.list:
        rows = store.conn.execute(
            "SELECT key_id, match_count, state, last_match_at FROM intent_keys "
            "ORDER BY match_count DESC"
        ).fetchall()
        for r in rows:
            print(f"  {r['key_id']:40s}  n={r['match_count']:4d}  state={r['state']}")
        print(f"total: {len(rows)}  embedder: {get_embedder().backend}")

    store.close()


if __name__ == "__main__":
    _main()
