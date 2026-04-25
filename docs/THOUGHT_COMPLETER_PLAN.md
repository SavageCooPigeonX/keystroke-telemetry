# Thought Completer — Planning Doc

**Status:** planning
**Date:** 2026-04-23
**Owner:** operator
**Supersedes (partially):** `docs/ARCHITECTURE_CONSENSUS_v3.md`, `docs/INTENT_SIMULATION.md`

---

## 1. One-line product statement

> The thought completer is the primary organ: it takes an operator fragment,
> renders candidate full intents using a dynamic operator profile assembled
> from self-managing intent keys, and hands resolved intents to copilot
> (frontend) and the deepseek loop (closure). Every acceptance/correction
> trains the profile and sharpens file identity.

Everything else in the repo is either an **input signal**, a **storage shard**,
or an **executor** for this organ.

---

## 2. Why this reframe

Previous architectures centered on:

- coding agent loops (deepseek, sim) — downstream
- self-healing codebase — an output
- intent closure — a KPI, not a product
- singularity merges — wrong primitive

The missing primary organ was the **compressor between operator intent and
system action**. Without it, every downstream daemon had to guess.

With the completer, we compress at the source. Intents are clean before
they hit the pipeline. Closure rate rises because inputs are cleaner, not
because loops are smarter.

---

## 3. Dynamic operator profile — structure

### 3.1 Multi-shard architecture

The profile is NOT a single blob. It is a set of **self-managing shards**,
each owned by an intent key class:

```
operator_profile/
├── shards/
│   ├── vocabulary/          # voice fingerprint, typical words, fragment → full mappings
│   ├── cognition/           # WPM baselines, deletion patterns, hesitation signatures
│   ├── learned_pairs/       # fragment → accepted_completion history
│   ├── file_affinity/       # which files the operator touches under which intent keys
│   ├── correction_log/      # rejected completions, why they were wrong
│   ├── exploration/         # deleted-word substrate, paths-not-taken
│   └── session_summary/     # compressed session-level decisions
├── intent_keys.json         # active intent keys with TTL
├── shard_registry.yaml      # who owns what, when it expires
└── profile_index.json       # fast lookup by tag
```

Each shard has:

- **owner daemon** (who writes it)
- **TTL** (when entries expire or compress)
- **consumers** (who reads it)
- **compression rule** (how it shrinks when it grows too big)

### 3.2 Self-managing intent keys

An **intent key** is a compact identifier for a recurring intent class,
derived from intent_numeric vectors clustered over time.

Example keys:
- `k_debug_pipeline` (cluster of debugging-the-sim-loop prompts)
- `k_arch_refactor` (cluster of restructuring prompts)
- `k_narrative_audit` (cluster of audit-my-architecture prompts)

Keys self-manage via:

1. **Birth**: new cluster of ≥5 similar intent vectors → new key
2. **Growth**: each matched prompt strengthens the key
3. **Split**: key becomes too broad → splits into sub-keys
4. **Merge**: two keys drift together → merge
5. **Sleep**: no matches for 30d → key goes dormant
6. **Death**: dormant for 90d → archived

Keys reference:
- file set (which files are typically touched under this key)
- prompt templates (typical fragment shapes)
- completion history (what operator accepted)
- failure modes (what the loop failed at)

### 3.3 Why multi-shard + self-managing keys is required

A single blob profile:
- bloats forever
- can't distinguish intent classes
- conflates vocabulary with cognition with affinity
- can't be versioned per axis
- can't sleep stale knowledge

Shards + keys fix each one:
- shards bloat independently and compress independently
- keys classify before storage
- axes are separated by shard boundary
- each shard has its own version
- sleep happens at key granularity

This is the **same pattern** the pigeon compiler uses for code files.
We are applying it to operator cognition.

---

## 4. On every prompt — the match pipeline

When operator submits a prompt (fragment or full), thought completer:

```
1. Extract intent_numeric vector from prompt
2. Match against active intent keys → ranked [(key, similarity)]
3. For top-K keys, pull shard slices:
   - vocabulary.fragment_completions matching this key
   - learned_pairs where prior_fragment ≈ current_fragment
   - file_affinity → candidate file targets
   - correction_log → avoid past wrong completions
   - session_summary → recent session drift
4. Pull file-side context for candidate files:
   - python code slice (relevant functions)
   - rename history
   - bug profile
   - open problems / chronic flags
5. Synthesize 3 candidate completions with confidence scores
6. Present to operator (popup / ghost text / narrative panel)
7. On accept/edit/reject:
   - update learned_pairs shard
   - update correction_log shard if rejected
   - update file_affinity shard with confirmed file targets
   - emit clean intent object to copilot + deepseek
```

Key point: steps 1–5 are **<300ms target** (local), step 6 is ghost/popup UI,
step 7 is async learning.

---

## 5. What gets pulled into view per match

Per the user's explicit request, on each prompt match the completer surfaces:

| View | Source shard / file | Purpose |
|---|---|---|
| Operator prompts learned vs completions across time | `learned_pairs/` | show evolution of same intent class |
| Intent manifests applicable | `shards/learned_pairs` + intent key registry | reusable recipes |
| Python code (relevant files) | file body + AST slice by intent key affinity | ground-truth for completion |
| File rename history | `pigeon_registry.json` | continuity across identity shifts |
| Bug profile | `docs/BUG_PROFILES.md` + scanner output | known pitfalls |
| Open problems | `logs/self_fix/*.json` + intent backlog | live blockers |

These are rendered in the **optimized intent view** (narrative panel) next to
the completion candidates, not injected into the LLM prompt blindly.
Operator sees them; completer uses them selectively based on intent key.

---

## 6. Absorption plan — what collapses into the completer

| Existing component | New role under completer |
|---|---|
| `prompt_enricher` | rendering step of the completer |
| `context_select_agent` | file-numeric module, absorbed |
| `intent_backlog` | open-fragment queue |
| `deleted_words` reconstruction | in-band exploration signal |
| `operator_state_daemon` | cognition shard writer |
| `prompt_telemetry` | vocabulary + cognition shard writer |
| `operator_probes` | clarifying-question mode |
| `intent_numeric` | key extraction core |
| `pigeon_registry` | file_affinity ground truth |
| copilot-instructions `current-query` | completer live display |

Seven-plus daemons become **one primary organ with tiered shard writers**.
This is the actual singularity: conceptual consolidation around one center.

---

## 7. What stays outside the completer

| Component | Role | Relationship |
|---|---|---|
| deepseek daemon | closure executor | receives clean intent |
| file_sim | fidelity check before edits | receives intent + file targets |
| self_fix scanner | bug source of truth | feeds bug profile shard |
| copilot (VS Code) | frontend builder | receives clean intent |
| pigeon compiler | file identity persistence | feeds file_affinity shard |
| entropy map | post-edit verification | confirms closure |
| observatory / narrative UI | dashboard | reads shards, renders |

These are **peripherals**. The completer is the brain; these are
sense organs, hands, and mirrors.

---

## 8. Lanes (solves prior fragmentation)

Three explicit lanes with strict write domains:

### Lane A — Live (keystroke-speed, ≤300ms)
- keystroke telemetry → vocabulary + cognition shard
- thought completer (local fast path) → candidate render
- operator_state_daemon → cognition shard

### Lane B — Cycle (prompt-speed, ≤5s)
- thought completer (LLM enrichment) → final candidates
- context injection → file-side slice
- learned_pair writer → on acceptance

### Lane C — Background (minute-speed)
- deepseek closure loop → receives accepted intents
- self_fix scanner → bug profile shard
- shard compression / key lifecycle (split/merge/sleep)
- narrative render for file personas

No two daemons write the same shard field. Ownership declared in
`shard_registry.yaml`.

---

## 9. Closure definition (carried forward from prior doc)

An intent is **closed** when:

1. It was captured as a fragment and completed (accepted candidate), AND
2. It was routed to file targets (file_affinity confirmed), AND
3. Action occurred (copilot edit or deepseek execution), AND
4. Post-action verification passed (tests or entropy non-regression), AND
5. Operator did not re-open the same intent key within session TTL.

`intent_closure_rate = closed_intents_7d / total_intents_7d`.

This is the **one KPI**. Organism health, compliance %, bug counts are all
derivatives.

---

## 10. Risks and mitigations (restated)

| Risk | Mitigation |
|---|---|
| Latency >300ms breaks flow | tiered: local fast-path, LLM only on pause |
| Suggestion fatigue | quiet by default, fire on hesitation/deletion-burst |
| Over-fitting to past | exploration term: sometimes surface deleted-word paths |
| Wrong completion corrupts profile | completion audit trail + rollback |
| Cold-start for new operators | onboarding mode + shared baseline shards |
| Narrative drift | periodic fidelity check: re-derive narrative from raw graph |
| Shard bloat | per-shard compression rules with TTL |
| Intent key explosion | split/merge/sleep lifecycle with caps |

---

## 11. Eventual extension — beyond code

Once operator profile is rich enough, the same completer completes:

- emails (cadence shard)
- docs (argument shard)
- prompts (fragment shard — this is the MVP)
- code (pattern shard — via file_affinity)
- issues/specs (structure shard)

**This is the meta-product.** The coding loop is the proving ground. The
thinking substrate is the long-term surface.

---

## 12. Implementation phases

### Phase 0 — Foundation (1–2 days)
- Define `shard_registry.yaml` with 7 shards, owners, TTLs, consumers
- Build `src/operator_profile_shards_seq001_v001.py` — shard read/write API
- Migrate existing `operator_profile.md`, `rework_log.json`,
  `file_profiles.json`, intent_numeric output into shards

### Phase 1 — Intent key lifecycle (2–3 days)
- Build `src/intent_keys_seq001_v001.py` — cluster / birth / growth / split / merge / sleep
- Seed from existing `logs/prompt_journal/*.jsonl` historical prompts
- Verify clusters match operator intuition (manual review)

### Phase 2 — Completer core (3–5 days)
- Build `src/thought_completer_seq001_v001.py`
- Input: fragment + shards + file context
- Output: 3 ranked candidates + confidence + file targets
- Tiered: local fast + LLM enrichment

### Phase 3 — UI hook (1–2 days)
- Wire completer into VS Code extension popup
- Ghost-text render for top candidate
- Full panel for intent view (prompts learned, manifests, code, history, bugs)
- Accept / edit / reject events → learned_pairs writer

### Phase 4 — Closure wiring (2–3 days)
- Accepted intent → copilot frontend channel
- Accepted intent → deepseek closure queue
- Verification hook → closure confirmation
- `intent_closure_rate` metric + dashboard

### Phase 5 — Absorption (cleanup)
- Deprecate prompt_enricher / context_select_agent as separate daemons
- Collapse intent_backlog into shard
- Route copilot-instructions current-query block through completer

---

## 13. First provable slice — one-prompt demo

Minimum viable demonstration (end-to-end, 400–600 LOC new):

1. Operator types fragment: "maintain profile"
2. Completer:
   - extracts intent_numeric vector
   - matches `k_arch_refactor` (top key from past 703 prompts)
   - pulls learned_pairs, file_affinity, bug_profile for that key
   - renders 3 candidates:
     - (a) "maintain dynamic operator profile via multi-shard architecture"
     - (b) "maintain profile shards with self-managing intent keys"
     - (c) "maintain profile freshness loop for operator cognition"
   - shows file targets: `intent_numeric`, `operator_profile.md`,
     `shard_manager` (candidate new module)
3. Operator accepts (a)
4. Learned pair stored: ("maintain profile", key=`k_arch_refactor`, chosen=a)
5. Intent object emitted to copilot AND deepseek queue
6. Closure confirmed when copilot or deepseek returns an edit that the
   operator keeps for ≥1 session.

Either this works and the product is real, or we see exactly which
stage fails and fix that stage.

---

## 14. Non-goals for now

- Multi-operator profiles (single operator for v1)
- Team / shared shards (single machine)
- Cloud sync (local only)
- Monetization scaffolding
- Cross-editor support (VS Code first, then maybe)
- Replacing copilot (we USE copilot, don't replace)

---

## 15. Open decisions — RESOLVED 2026-04-23

### D1. Local vs API for fast path → **LOCAL**

Live lane budget is ≤300ms. API roundtrip (DeepSeek/Gemini) is 300–800ms
on a good day, 2s+ on a bad one. Non-negotiable: the fast path runs local.

- **Live lane (≤300ms):** local embedder + local heuristics + cached
  learned-pairs lookup. No network.
- **Cycle lane (≤5s):** API calls allowed for candidate refinement when
  local confidence <0.6.
- **Background lane:** API-heavy (narrative diffs, sim projections,
  image renders).

Implication: completer must ship with an offline-capable core. API is
a quality upgrade, not a dependency.

### D2. Embedding model → **sentence-transformers `all-MiniLM-L6-v2` (local)**

Follows from D1. 22MB model, ~10ms/embed on CPU, 384-dim vectors,
well-benchmarked for short-text semantic similarity — which is exactly
what fragment-to-intent-key matching is.

- Rejected: Gemini embedding API (violates live lane latency)
- Rejected: OpenAI `text-embedding-3-small` (still API)
- Rejected: larger models like `mpnet-base-v2` (2–3× slower, marginal
  quality gain for short fragments)

Cache embeddings of known intent keys in memory. Re-embed only fragment
per keystroke burst. Budget: 10ms embed + 5ms cosine-topk = 15ms.

### D3. Shard storage → **SQLite (single file, table per shard)**

- **JSONL:** no indexed lookup, read cost grows linearly with history.
  Fatal for learned-pairs shard which must be hot on every keystroke.
- **LMDB:** binary, opaque, hard to inspect. Overkill for our data volume.
- **SQLite:** indexed queries, WAL mode = true ACID transactions (required
  for the transactional coder writes in Part 2 of brainstorm), stdlib,
  single file (`data/operator_profile.db`), dead-simple debugging with
  any SQLite browser.

Schema: one table per shard. `learned_pairs`, `vocabulary`, `cognition`,
`file_affinity`, `correction_log`, `exploration`, `session_summary`.
WAL journal mode. `PRAGMA synchronous=NORMAL` for write speed.

### D4. Ambiguity tiebreaker → **deterministic tiered, operator-in-loop as last resort. No LLM tiebreak.**

When top-2 intent keys tie within 0.05 cosine similarity:

1. **Recency bias:** key most recently activated in current session wins.
2. **File co-occurrence:** if operator has an open file that matches
   one key's typical file targets, that key wins.
3. **Stalemate → operator picks:** render both candidates side-by-side
   in the completer UI. Operator click resolves.

LLM tiebreak is rejected because: (a) adds 300–800ms, violates live
lane; (b) drifts — same fragment can produce different tiebreaks across
calls; (c) hides the ambiguity from the operator, who is the actual
authority on their own intent.

Every operator-resolved tie becomes a learned pair → reduces future
ambiguity over time. This is the system improving itself.

### D5. Copilot-instructions strip → **shadow mode then aggressive**

Two-phase rollout:

- **Phase 4 (shadow, 7 days):** completer writes its own `current-query`
  block to a *side file* (`logs/completer_current_query.md`). Old
  pipeline keeps writing the main block. Daily diff report:
  "completer beat / matched / lost vs old pipeline."
- **Phase 5 (cutover):** if completer ≥70% match-or-beat over 7-day
  window, strip aggressively. Same-day deletions from
  `.github/copilot-instructions.md`:
  - `pigeon:current-query` (completer owns this)
  - deleted-words reconstruction (completer owns unsaid threads)
  - `pigeon:operator-probes` (completer's UI hook replaces)
  - `pigeon:intent-backlog` (closure rate replaces)

**KEEP** (not owned by completer):
- `pigeon:task-queue`
- `pigeon:active-template`
- `pigeon:voice-style`
- `pigeon:operator-state`
- `pigeon:prompt-telemetry`
- `pigeon:task-context`

Target: copilot-instructions.md drops from ~730 lines to ~300 lines.
Stale-block alerts should drop from 3 → 0 because removed blocks can't
go stale.

If completer fails shadow (<70% match), strip nothing. Do not ship.

---

## 16. Success signals (90-day)

- `intent_closure_rate` ≥ 60% (currently <20% by inspection)
- Median fragment → accepted candidate latency ≤ 400ms
- 10+ stable intent keys with clear semantic meaning
- 3 stale copilot-instructions blocks → 0
- Organism health KPI replaced by closure rate in all dashboards
- Operator can describe a past intent and the completer surfaces the
  exact historical completion within 2 seconds

---

*End of plan. Next doc update triggered when Phase 0 completes or any
open decision in §15 resolves.*


---

## 16. Phase 7 — manifest_chain_proposer (coder orchestration)

**Status:** planning · **Date:** 2026-04-23 · **Supersedes:** file_sim 4-way debate path

### 16.1 Why this phase exists

Operator history (`logs/prompt_journal.jsonl`, retrieved via `scripts/prompt_search.py`) shows a consistent model over 55+ prompts referencing `chain`/`manifest`/`deepseek`:

- 2026-04-10 19:39 · *"chain the manifest across nodes forwards / backwards"*
- 2026-04-24 02:46 · *"10 hour+ task loops / file sims to fully push until entropy increase"*
- 2026-04-24 03:08 · *"files propose a theory on how to fix it — siblings propose fixes to grader — grader does file proposal expansion — that kicks off manifest chain"* (deleted: `"off file sims"`)
- 2026-04-24 03:30 · *"copilot = builder, coder agent = closer"*
- 2026-04-24 05:38 · *"why am I still leaning into manifest chaining vs 4 file sim old path"*

The deletion of `"off file sims"` at 03:08, rewritten to `"manifest chain"`, is the decision already made. This phase formalizes it.

### 16.2 Goal

Replace the **file_sim 4-candidate debate** (chooses 1 winner, low confidence, edits single file, high reopen rate) with a **manifest chain** (proposes a multi-file coordinated edit plan, executes as one transaction, closes on entropy-stable).

### 16.3 Pipeline

```
intent_id (from completer queue)
  -> chain_seed: first file = highest file_affinity for intent_key
  -> for each seed file:
       - load last-5 diffs + renames + sibling contracts
       - generate FIX THEORY (deepseek lane-B call, cycle budget)
  -> chain_expansion:
       - for each theory: pull sibling files via pigeon_registry + shard_registry consumers
       - expanded files re-run theory generation, possibly refining original
  -> chain_grader:
       - contract validation: does chain preserve all declared emits/consumes?
       - entropy delta: does chain reduce or increase red-layer entropy?
       - if entropy INCREASE: halt, mark intent cond_verified=false, open correction
       - if ENTROPY_STABLE or DECREASE: proceed
  -> deepseek_assembly:
       - single prompt carrying full chain + all personas + all contracts
       - atomic multi-file patch (accept-all or reject-all)
  -> checkpoint_capture (Phase 8 hook):
       - snapshot module signatures + public-fn hashes for each file in chain
  -> closure:
       - cond_routed (queued) -> cond_acted (patch applied) -> cond_verified
         (checkpoint matches) -> cond_stable (1hr quiet)
```

### 16.4 Module layout

- `src/manifest_chain_proposer_seq001_v001.py` — new, owns the pipeline
- reads: `pigeon_registry.json`, `shard_registry.yaml`, `absorption_declarations.yaml`, `logs/prompt_journal.jsonl` (via `prompt_search.search_api`), shard `file_affinity` + `learned_pairs`
- writes: `logs/chain_proposals.jsonl`, `shard_learned_pairs` (when accepted)
- invokes: `deepseek_daemon` (existing), `entropy_map` (existing read-only)
- lane: **B (cycle, <=5s)** for proposal, **C (background)** for 10hr+ closure loops

### 16.5 Data structures

```python
@dataclass
class ChainNode:
    file_path: str
    role: str                  # "seed" | "expansion" | "contract_peer"
    fix_theory: str
    confidence: float
    persona: dict              # fears, partners, contracts
    last_diffs: list[dict]     # up to 5

@dataclass
class ManifestChain:
    intent_id: str
    nodes: list[ChainNode]
    entropy_before: float
    entropy_after_est: float
    contract_violations: list[str]
    grade: float               # 0..1; gate on >= 0.7 to assemble

@dataclass
class ChainAssemblyResult:
    chain: ManifestChain
    deepseek_patch: dict       # multi-file diff
    applied: bool
    checkpoint_ids: list[str]  # Phase 8 hooks
```

### 16.6 Halt conditions (from operator 02:46)

Long-running chain closure stops on ANY:

1. **Entropy increase** — red-layer score rises after patch; auto-revert
2. **File sleep** — all nodes report `no_changes_needed` on re-probe
3. **Contract violation** — emits/consumes drift; patch rejected
4. **Operator override** — explicit `reject` from completer UI
5. **Budget exhaustion** — >10hr wall clock, >N deepseek calls

### 16.7 Absorption / deprecation

- `file_sim_seq001_v005_d0421__*` — demoted to **lane-C cold advisor**
  - still computes per-file `needs_change` scores as background signal
  - no longer gates coder orchestration
  - `absorption_declarations.yaml`: status `deprecated_but_retained`
  - deletion scheduled Phase 8 if chain proposer match_rate > 0.75 for 14 days
- `priority_closure_loop.py` — thin shim that reads completer queue, kicks chain proposer, no longer runs sim-debate locally

### 16.8 Measurable wins (KPIs)

| metric | today (sim) | target (chain) |
|---|---|---|
| avg confidence of chosen edit | 0.50-0.92 spread | >=0.75 floor |
| reopened intents within 24h | baseline X | <X * 0.5 |
| files touched per accepted intent | 1.0 | 2.1 (matches real surface) |
| closure_rate_7d | ~0% (new metric) | >=0.60 |
| deepseek calls per closed intent | 3-4 | 1-2 |

### 16.9 Open decisions (resolve before code)

- **D6 chain ordering** — topological sort (deps first) vs reverse-topological (leaves first)? Lean leaves-first: cheapest to test, fastest entropy signal.
- **D7 chain size cap** — max nodes per chain before forcing split? Proposal: 6.
- **D8 expansion strategy** — breadth-1 siblings only, or transitive closure? Proposal: breadth-1 + operator opt-in for transitive.
- **D9 entropy source** — use existing `pigeon:entropy-map` block, or new per-chain entropy function? Proposal: read existing map; compute delta locally.
- **D10 checkpoint capture timing** — before or after deepseek patch? Proposal: snapshot before (baseline), compare after (drift).

### 16.10 Ship order

1. Module scaffold + ChainNode/ManifestChain dataclasses
2. seed picker from file_affinity (no LLM yet; deterministic)
3. persona loader (reads `file_profiles.json`, `pigeon_registry.json`)
4. fix-theory generator (deepseek, lane B)
5. contract validator (read-only, fast)
6. entropy delta estimator (local)
7. grader composition
8. deepseek assembly call
9. closure hook wiring to completer ledger
10. end-to-end slice analogous to Sec.13

### 16.11 Non-goals for Phase 7

- Replacing deepseek with in-house model
- Training a grader model (rule-based first)
- Cross-repo chains (single workspace only)
- Automatic chain regeneration on CI failures (Phase 8)
