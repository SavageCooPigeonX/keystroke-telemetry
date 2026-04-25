"""operator_profile_shards_seq001_v001 — SQLite-backed shard R/W for thought completer.

Phase 0 deliverable. Resolves D3 (storage = SQLite, WAL, table per shard).

responsibilities:
  - open/init the single db file from data/schema.sql
  - enforce WAL + synchronous=NORMAL
  - provide thin typed R/W functions per shard
  - expose transaction() context manager for the atomic coder writes
    described in THOUGHT_COMPLETER_PLAN §Part 2 (coder, reframed)
  - load shard_registry.yaml metadata for consumers to inspect

this module is the ONLY place that touches the db. every other daemon
(prompt_telemetry_daemon, operator_state_daemon, thought_completer,
intent_keys_manager, session_compactor) calls into here.

non-goals for v1:
  - compression/TTL sweep (separate module, lane C)
  - intent key clustering (intent_keys_seq001_v001, Phase 1)
  - embedding cache (thought_completer, Phase 2)
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
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "data" / "operator_profile.db"
DEFAULT_SCHEMA = REPO_ROOT / "data" / "schema.sql"
DEFAULT_REGISTRY = REPO_ROOT / "shard_registry.yaml"

SCHEMA_VERSION = 1


# ─── CORE ─────────────────────────────────────────────────────────


class ShardStore:
    """Single-writer SQLite wrapper for the operator profile shards."""

    def __init__(
        self,
        db_path: Path | str = DEFAULT_DB,
        schema_path: Path | str = DEFAULT_SCHEMA,
    ) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._registry: dict[str, Any] | None = None

    # ── connection mgmt ────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                isolation_level=None,  # manual BEGIN/COMMIT
                timeout=5.0,
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=OFF")
            self._init_schema()
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_schema(self) -> None:
        assert self._conn is not None
        cur = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        needs_init = cur.fetchone() is None
        if needs_init:
            if not self.schema_path.exists():
                raise FileNotFoundError(
                    f"schema file missing: {self.schema_path}"
                )
            sql = self.schema_path.read_text(encoding="utf-8")
            self._conn.executescript(sql)
            self._conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, time.time()),
            )

    # ── transactions ───────────────────────────────────────────────

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """BEGIN ... COMMIT / ROLLBACK. Used for atomic coder writes."""
        c = self.conn
        c.execute("BEGIN IMMEDIATE")
        try:
            yield c
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise

    # ── registry ───────────────────────────────────────────────────

    def registry(self) -> dict[str, Any]:
        if self._registry is None:
            if not DEFAULT_REGISTRY.exists() or yaml is None:
                self._registry = {}
            else:
                self._registry = yaml.safe_load(
                    DEFAULT_REGISTRY.read_text(encoding="utf-8")
                ) or {}
        return self._registry


# ─── SHARD WRITERS ────────────────────────────────────────────────


def _now() -> float:
    return time.time()


def write_vocabulary(
    store: ShardStore,
    fragment: str,
    expansion: str | None = None,
    intent_key: str | None = None,
    fragment_vec: list[float] | None = None,
) -> int:
    """Upsert by fragment: increment freq, refresh last_seen_at."""
    now = _now()
    c = store.conn
    cur = c.execute(
        "SELECT id, freq FROM shard_vocabulary WHERE fragment = ?",
        (fragment,),
    )
    row = cur.fetchone()
    if row is not None:
        c.execute(
            "UPDATE shard_vocabulary SET freq = ?, last_seen_at = ?, "
            "expansion = COALESCE(?, expansion), "
            "intent_key = COALESCE(?, intent_key), "
            "fragment_vec = COALESCE(?, fragment_vec) "
            "WHERE id = ?",
            (
                row["freq"] + 1,
                now,
                expansion,
                intent_key,
                json.dumps(fragment_vec) if fragment_vec is not None else None,
                row["id"],
            ),
        )
        return int(row["id"])
    cur = c.execute(
        "INSERT INTO shard_vocabulary "
        "(fragment, expansion, intent_key, fragment_vec, freq, last_seen_at, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?, ?)",
        (
            fragment,
            expansion,
            intent_key,
            json.dumps(fragment_vec) if fragment_vec is not None else None,
            now,
            now,
        ),
    )
    return int(cur.lastrowid or 0)


def write_cognition(
    store: ShardStore,
    session_id: str,
    wpm: float | None = None,
    deletion_ratio: float | None = None,
    hesitation: float | None = None,
    state: str | None = None,
    prompt_preview: str | None = None,
    ts: float | None = None,
) -> int:
    now = _now()
    c = store.conn
    cur = c.execute(
        "INSERT INTO shard_cognition "
        "(session_id, ts, wpm, deletion_ratio, hesitation, state, prompt_preview, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, ts or now, wpm, deletion_ratio, hesitation, state, prompt_preview, now),
    )
    return int(cur.lastrowid or 0)


def write_learned_pair(
    store: ShardStore,
    fragment: str,
    completion: str,
    intent_key: str | None = None,
    confidence: float = 0.0,
    accept_kind: str = "accept",
    file_targets: list[str] | None = None,
    session_id: str | None = None,
) -> int:
    now = _now()
    c = store.conn
    cur = c.execute(
        "INSERT INTO shard_learned_pairs "
        "(fragment, completion, intent_key, confidence, accept_kind, "
        " file_targets_json, session_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            fragment,
            completion,
            intent_key,
            confidence,
            accept_kind,
            json.dumps(file_targets) if file_targets else None,
            session_id,
            now,
        ),
    )
    return int(cur.lastrowid or 0)


def touch_file_affinity(
    store: ShardStore,
    intent_key: str,
    file_path: str,
) -> int:
    """Upsert (intent_key, file_path) — increment touch_count."""
    now = _now()
    c = store.conn
    c.execute(
        "INSERT INTO shard_file_affinity "
        "(intent_key, file_path, touch_count, last_touch_at, created_at) "
        "VALUES (?, ?, 1, ?, ?) "
        "ON CONFLICT(intent_key, file_path) DO UPDATE SET "
        "touch_count = touch_count + 1, last_touch_at = excluded.last_touch_at",
        (intent_key, file_path, now, now),
    )
    cur = c.execute(
        "SELECT id FROM shard_file_affinity WHERE intent_key = ? AND file_path = ?",
        (intent_key, file_path),
    )
    row = cur.fetchone()
    return int(row["id"]) if row else 0


def write_correction(
    store: ShardStore,
    fragment: str,
    rejected_completion: str,
    chosen_completion: str | None = None,
    intent_key: str | None = None,
    reason: str | None = None,
    session_id: str | None = None,
) -> int:
    now = _now()
    cur = store.conn.execute(
        "INSERT INTO shard_correction_log "
        "(fragment, rejected_completion, chosen_completion, intent_key, reason, session_id, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fragment, rejected_completion, chosen_completion, intent_key, reason, session_id, now),
    )
    return int(cur.lastrowid or 0)


def write_exploration(
    store: ShardStore,
    deleted_text: str,
    session_id: str | None = None,
    surrounding_fragment: str | None = None,
    reconstructed_intent: str | None = None,
    intent_key: str | None = None,
    ts: float | None = None,
) -> int:
    now = _now()
    cur = store.conn.execute(
        "INSERT INTO shard_exploration "
        "(session_id, ts, deleted_text, surrounding_fragment, reconstructed_intent, intent_key, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, ts or now, deleted_text, surrounding_fragment, reconstructed_intent, intent_key, now),
    )
    return int(cur.lastrowid or 0)


def upsert_session_summary(
    store: ShardStore,
    session_id: str,
    started_at: float | None = None,
    ended_at: float | None = None,
    intent_keys_active: list[str] | None = None,
    accepted: int | None = None,
    rejected: int | None = None,
    files_touched: list[str] | None = None,
    summary_text: str | None = None,
) -> int:
    now = _now()
    c = store.conn
    cur = c.execute(
        "SELECT id FROM shard_session_summary WHERE session_id = ?",
        (session_id,),
    )
    row = cur.fetchone()
    if row is None:
        cur = c.execute(
            "INSERT INTO shard_session_summary "
            "(session_id, started_at, ended_at, intent_keys_active_json, "
            " accepted_completions, rejected_completions, files_touched_json, "
            " summary_text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                started_at or now,
                ended_at,
                json.dumps(intent_keys_active) if intent_keys_active else None,
                accepted or 0,
                rejected or 0,
                json.dumps(files_touched) if files_touched else None,
                summary_text,
                now,
            ),
        )
        return int(cur.lastrowid or 0)
    # update existing
    c.execute(
        "UPDATE shard_session_summary SET "
        "ended_at = COALESCE(?, ended_at), "
        "intent_keys_active_json = COALESCE(?, intent_keys_active_json), "
        "accepted_completions = COALESCE(?, accepted_completions), "
        "rejected_completions = COALESCE(?, rejected_completions), "
        "files_touched_json = COALESCE(?, files_touched_json), "
        "summary_text = COALESCE(?, summary_text) "
        "WHERE id = ?",
        (
            ended_at,
            json.dumps(intent_keys_active) if intent_keys_active else None,
            accepted,
            rejected,
            json.dumps(files_touched) if files_touched else None,
            summary_text,
            row["id"],
        ),
    )
    return int(row["id"])


# ─── INTENT KEYS ──────────────────────────────────────────────────


def upsert_intent_key(
    store: ShardStore,
    key_id: str,
    centroid_vec: list[float],
    state: str = "active",
    split_from: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    now = _now()
    c = store.conn
    cur = c.execute("SELECT key_id FROM intent_keys WHERE key_id = ?", (key_id,))
    if cur.fetchone() is None:
        c.execute(
            "INSERT INTO intent_keys "
            "(key_id, centroid_vec, birth_at, last_match_at, match_count, state, split_from, meta_json) "
            "VALUES (?, ?, ?, ?, 0, ?, ?, ?)",
            (
                key_id,
                json.dumps(centroid_vec),
                now,
                now,
                state,
                split_from,
                json.dumps(meta) if meta else None,
            ),
        )
    else:
        c.execute(
            "UPDATE intent_keys SET centroid_vec = ?, state = ?, meta_json = COALESCE(?, meta_json) "
            "WHERE key_id = ?",
            (
                json.dumps(centroid_vec),
                state,
                json.dumps(meta) if meta else None,
                key_id,
            ),
        )


def bump_intent_key_match(store: ShardStore, key_id: str) -> None:
    store.conn.execute(
        "UPDATE intent_keys SET match_count = match_count + 1, last_match_at = ? WHERE key_id = ?",
        (_now(), key_id),
    )


# ─── INTENT LEDGER (closure tracking) ─────────────────────────────


def emit_intent(
    store: ShardStore,
    fragment: str,
    completion: str,
    intent_key: str | None = None,
    file_targets: list[str] | None = None,
    session_id: str | None = None,
) -> str:
    intent_id = f"int_{uuid.uuid4().hex[:12]}"
    now = _now()
    store.conn.execute(
        "INSERT INTO intent_ledger "
        "(intent_id, fragment, completion, intent_key, file_targets_json, "
        " emitted_at, cond_captured, session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
        (
            intent_id,
            fragment,
            completion,
            intent_key,
            json.dumps(file_targets) if file_targets else None,
            now,
            session_id,
        ),
    )
    return intent_id


_COND_COLS = {
    "captured": "cond_captured",
    "routed": "cond_routed",
    "acted": "cond_acted",
    "verified": "cond_verified",
    "stable": "cond_stable",
}


def mark_condition(store: ShardStore, intent_id: str, condition: str) -> None:
    col = _COND_COLS.get(condition)
    if col is None:
        raise ValueError(f"unknown condition {condition!r}; expected one of {list(_COND_COLS)}")
    store.conn.execute(
        f"UPDATE intent_ledger SET {col} = 1 WHERE intent_id = ?",
        (intent_id,),
    )
    # if all 5 conditions met and not yet closed, close it
    store.conn.execute(
        "UPDATE intent_ledger SET closed_at = ? "
        "WHERE intent_id = ? AND closed_at IS NULL "
        "AND cond_captured = 1 AND cond_routed = 1 AND cond_acted = 1 "
        "AND cond_verified = 1 AND cond_stable = 1",
        (_now(), intent_id),
    )


def closure_rate_7d(store: ShardStore) -> float:
    window = _now() - 7 * 86400
    cur = store.conn.execute(
        "SELECT "
        "  SUM(CASE WHEN emitted_at >= ? THEN 1 ELSE 0 END) AS emitted, "
        "  SUM(CASE WHEN closed_at IS NOT NULL AND closed_at >= ? THEN 1 ELSE 0 END) AS closed "
        "FROM intent_ledger",
        (window, window),
    )
    row = cur.fetchone()
    emitted = row["emitted"] or 0
    closed = row["closed"] or 0
    return float(closed) / float(emitted) if emitted else 0.0


# ─── READERS ──────────────────────────────────────────────────────


def search_learned_pairs(
    store: ShardStore,
    fragment_like: str | None = None,
    intent_key: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if fragment_like:
        clauses.append("fragment LIKE ?")
        params.append(f"%{fragment_like}%")
    if intent_key:
        clauses.append("intent_key = ?")
        params.append(intent_key)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    cur = store.conn.execute(
        f"SELECT * FROM shard_learned_pairs {where} ORDER BY created_at DESC LIMIT ?",
        params,
    )
    return [dict(r) for r in cur.fetchall()]


def top_file_affinities(
    store: ShardStore,
    intent_key: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    cur = store.conn.execute(
        "SELECT file_path, touch_count, last_touch_at FROM shard_file_affinity "
        "WHERE intent_key = ? ORDER BY touch_count DESC LIMIT ?",
        (intent_key, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def active_intent_keys(store: ShardStore) -> list[dict[str, Any]]:
    cur = store.conn.execute(
        "SELECT key_id, match_count, last_match_at, state FROM intent_keys "
        "WHERE state = 'active' ORDER BY last_match_at DESC"
    )
    return [dict(r) for r in cur.fetchall()]


# ─── CLI smoke test ───────────────────────────────────────────────


def _smoke() -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp()) / "smoke.db"
    store = ShardStore(db_path=tmp, schema_path=DEFAULT_SCHEMA)

    # write one of each
    write_vocabulary(store, "maintain profile", "maintain dynamic operator profile", "k_arch_refactor")
    write_cognition(store, "sess_001", wpm=52.0, deletion_ratio=0.25, hesitation=0.44, state="focused")
    write_learned_pair(
        store,
        "maintain profile",
        "maintain dynamic operator profile via multi-shard architecture",
        intent_key="k_arch_refactor",
        confidence=0.82,
        file_targets=["src/operator_profile_shards_seq001_v001.py"],
        session_id="sess_001",
    )
    touch_file_affinity(store, "k_arch_refactor", "src/operator_profile_shards_seq001_v001.py")
    touch_file_affinity(store, "k_arch_refactor", "src/operator_profile_shards_seq001_v001.py")
    write_correction(store, "maintain profile", "profile a maintenance budget", reason="misread verb")
    write_exploration(store, "budget", session_id="sess_001", surrounding_fragment="maintain profile budget")
    upsert_session_summary(store, "sess_001", intent_keys_active=["k_arch_refactor"], accepted=1)
    upsert_intent_key(store, "k_arch_refactor", [0.1] * 384)
    bump_intent_key_match(store, "k_arch_refactor")

    intent_id = emit_intent(
        store,
        "maintain profile",
        "maintain dynamic operator profile via multi-shard architecture",
        intent_key="k_arch_refactor",
        file_targets=["src/operator_profile_shards_seq001_v001.py"],
        session_id="sess_001",
    )
    for cond in ("routed", "acted", "verified", "stable"):
        mark_condition(store, intent_id, cond)

    # transaction rollback check
    try:
        with store.transaction():
            write_learned_pair(store, "rollback me", "should not persist")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    leftover = search_learned_pairs(store, fragment_like="rollback me")
    assert not leftover, "transaction rollback failed"

    # commit check
    with store.transaction():
        write_learned_pair(store, "tx frag", "tx completion")
    assert search_learned_pairs(store, fragment_like="tx frag"), "transaction commit failed"

    # readers
    lp = search_learned_pairs(store, fragment_like="maintain")
    fa = top_file_affinities(store, "k_arch_refactor")
    keys = active_intent_keys(store)
    rate = closure_rate_7d(store)

    print(f"learned_pairs       : {len(lp)}")
    print(f"file_affinity rows  : {len(fa)} (top touch_count={fa[0]['touch_count'] if fa else 0})")
    print(f"active intent_keys  : {len(keys)}")
    print(f"closure_rate_7d     : {rate:.2%}")
    print(f"db file             : {tmp}")
    store.close()


if __name__ == "__main__":
    _smoke()
