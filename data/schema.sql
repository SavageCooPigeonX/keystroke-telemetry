-- operator_profile schema (thought completer, Phase 0)
-- resolves D3: SQLite, table per shard, WAL journal mode.
-- one db file: data/operator_profile.db
--
-- conventions:
--   - all tables have id INTEGER PRIMARY KEY AUTOINCREMENT
--   - all tables have created_at REAL (unix epoch) indexed for TTL sweeps
--   - intent_key is a soft FK to intent_keys.key_id (no enforced FK so
--     deletes don't cascade; lifecycle is handled by key manager)
--   - JSON blobs stored as TEXT (SQLite JSON1 extension available)

-- ── META ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL,
    applied_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS intent_keys (
    key_id TEXT PRIMARY KEY,                -- e.g. "k_arch_refactor"
    centroid_vec TEXT NOT NULL,             -- JSON array of floats (384-dim)
    birth_at REAL NOT NULL,
    last_match_at REAL NOT NULL,
    match_count INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'active',   -- active|dormant|archived
    split_from TEXT,                        -- parent key_id if from split
    merged_into TEXT,                       -- target key_id if merged
    meta_json TEXT                          -- free-form metadata
);
CREATE INDEX IF NOT EXISTS ix_intent_keys_state ON intent_keys(state);
CREATE INDEX IF NOT EXISTS ix_intent_keys_last_match ON intent_keys(last_match_at);

-- ── SHARDS ────────────────────────────────────────────────────────

-- 1. vocabulary — fragment → candidate expansions, voice fingerprint
CREATE TABLE IF NOT EXISTS shard_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fragment TEXT NOT NULL,
    expansion TEXT,
    intent_key TEXT,
    fragment_vec TEXT,                      -- JSON array, cached embedding
    freq INTEGER NOT NULL DEFAULT 1,
    last_seen_at REAL NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vocab_fragment ON shard_vocabulary(fragment);
CREATE INDEX IF NOT EXISTS ix_vocab_intent_key ON shard_vocabulary(intent_key);
CREATE INDEX IF NOT EXISTS ix_vocab_last_seen ON shard_vocabulary(last_seen_at);

-- 2. cognition — WPM, deletion patterns, hesitation signatures
CREATE TABLE IF NOT EXISTS shard_cognition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    ts REAL NOT NULL,
    wpm REAL,
    deletion_ratio REAL,
    hesitation REAL,
    state TEXT,                             -- abandoned|restructuring|focused|...
    prompt_preview TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_cog_session ON shard_cognition(session_id);
CREATE INDEX IF NOT EXISTS ix_cog_ts ON shard_cognition(ts);

-- 3. learned_pairs — fragment → accepted completion, the core training data
CREATE TABLE IF NOT EXISTS shard_learned_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fragment TEXT NOT NULL,
    completion TEXT NOT NULL,
    intent_key TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    accept_kind TEXT NOT NULL DEFAULT 'accept',  -- accept|edit|reject
    file_targets_json TEXT,                 -- JSON array of file paths
    session_id TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lp_fragment ON shard_learned_pairs(fragment);
CREATE INDEX IF NOT EXISTS ix_lp_intent_key ON shard_learned_pairs(intent_key);
CREATE INDEX IF NOT EXISTS ix_lp_created ON shard_learned_pairs(created_at);

-- 4. file_affinity — which files get touched under which intent keys
CREATE TABLE IF NOT EXISTS shard_file_affinity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_key TEXT NOT NULL,
    file_path TEXT NOT NULL,
    touch_count INTEGER NOT NULL DEFAULT 1,
    last_touch_at REAL NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(intent_key, file_path)
);
CREATE INDEX IF NOT EXISTS ix_fa_intent_key ON shard_file_affinity(intent_key);
CREATE INDEX IF NOT EXISTS ix_fa_file ON shard_file_affinity(file_path);

-- 5. correction_log — rejected completions + why
CREATE TABLE IF NOT EXISTS shard_correction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fragment TEXT NOT NULL,
    rejected_completion TEXT NOT NULL,
    chosen_completion TEXT,
    intent_key TEXT,
    reason TEXT,                            -- free-form or enum later
    session_id TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_cl_fragment ON shard_correction_log(fragment);
CREATE INDEX IF NOT EXISTS ix_cl_intent_key ON shard_correction_log(intent_key);

-- 6. exploration — deleted-word substrate, paths-not-taken
CREATE TABLE IF NOT EXISTS shard_exploration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    ts REAL NOT NULL,
    deleted_text TEXT NOT NULL,
    surrounding_fragment TEXT,
    reconstructed_intent TEXT,
    intent_key TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_exp_session ON shard_exploration(session_id);
CREATE INDEX IF NOT EXISTS ix_exp_ts ON shard_exploration(ts);

-- 7. session_summary — compressed session-level decisions
CREATE TABLE IF NOT EXISTS shard_session_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    started_at REAL NOT NULL,
    ended_at REAL,
    intent_keys_active_json TEXT,           -- JSON array of key_ids
    accepted_completions INTEGER NOT NULL DEFAULT 0,
    rejected_completions INTEGER NOT NULL DEFAULT 0,
    files_touched_json TEXT,
    summary_text TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ss_started ON shard_session_summary(started_at);

-- ── CLOSURE LEDGER ────────────────────────────────────────────────
-- tracks the 5-condition closure from §9. emitted intents live here
-- until conditions 1-5 are verified, then marked closed.

CREATE TABLE IF NOT EXISTS intent_ledger (
    intent_id TEXT PRIMARY KEY,             -- uuid or slug
    fragment TEXT NOT NULL,
    completion TEXT NOT NULL,
    intent_key TEXT,
    file_targets_json TEXT,
    emitted_at REAL NOT NULL,
    cond_captured INTEGER NOT NULL DEFAULT 0,
    cond_routed INTEGER NOT NULL DEFAULT 0,
    cond_acted INTEGER NOT NULL DEFAULT 0,
    cond_verified INTEGER NOT NULL DEFAULT 0,
    cond_stable INTEGER NOT NULL DEFAULT 0,
    closed_at REAL,
    session_id TEXT
);
CREATE INDEX IF NOT EXISTS ix_ledger_intent_key ON intent_ledger(intent_key);
CREATE INDEX IF NOT EXISTS ix_ledger_emitted ON intent_ledger(emitted_at);
CREATE INDEX IF NOT EXISTS ix_ledger_closed ON intent_ledger(closed_at);
