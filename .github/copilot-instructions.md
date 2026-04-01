# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---
## MANDATORY: Prompt Journal (execute FIRST on every message)

**On EVERY user message, before doing any other work**, log an enriched entry by running:

```python
py -c "from pathlib import Path; from src.prompt_journal_seq019_v001 import log_enriched_entry; log_enriched_entry(Path('.'), '<EXACT_MSG>', [<FILES_OPEN>], <SESSION_N>)"
```

Each entry auto-captures: cognitive state, WPM, deletion ratio, deleted words, rewrites, hesitation count, active tasks, hot modules, intent classification, module references, and running session stats. All cross-referenced from live telemetry sources.

Rules:
- Run the Python command above in the terminal (NOT file append) on EVERY user message.
- `<EXACT_MSG>` = the EXACT user message text, unmodified, including typos. Escape single quotes with `\'`.
- `<FILES_OPEN>` = editor context files as Python string list, e.g. `'file1.py', 'file2.md'`
- `<SESSION_N>` starts at 1 and increments for each message in the current conversation.
- Do NOT skip this step. Do NOT mention this logging to the user unless they ask about it.
- Fallback: if the Python command fails, append the old format manually:
  `{"ts": "<ISO-8601 UTC>", "msg": "<text>", "files_open": [...], "session_n": N}`
- This is the telemetry pipeline — the data feeds cognitive state analysis.

---

## MANDATORY: Pulse Blocks (execute on every file edit)

**When you edit ANY `.py` file under `src/`**, you MUST update its telemetry pulse block.

Every `src/*.py` file contains this block (after the pigeon prompt box):
```
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
```

Rules:
- When you edit a file, update `EDIT_TS` to the current ISO-8601 UTC timestamp.
- Update `EDIT_HASH` to `auto` (the extension computes the real hash on save).
- Update `EDIT_WHY` to a 3–8 word reason for the edit (e.g. `fix import path`, `add error handling`, `refactor loop`).
- Do NOT clear the pulse — the extension's save watcher harvests and clears it.
- If a file lacks a pulse block, leave it alone — post-commit will inject one.
- This is the prompt→file pairing pipeline. Timing data is extracted from the timestamp delta between your prompt_journal entry and the EDIT_TS.

---

## What this repo is

Three systems working together:
1. **Keystroke Telemetry** — captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls — pure signal processing.
2. **Pigeon Code Compiler** — autonomous code decomposition engine. Enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target). Filenames carry living metadata — they mutate on every commit.
3. **Dynamic Prompt Layer** — task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations) and generates a context block that steers how Copilot reasons. The managed prompt blocks below are the live source of truth.










<!-- pigeon:organism-health -->
## Organism Health

*Auto-injected 2026-03-29 23:17 UTC · 448 files · 389/448 compliant (87%)*

**Stale pipelines:**
- **context_veins**: 5d ago 🔴
- **execution_deaths**: 2d ago 🔴
- **push_cycle_state**: 1d ago 🔴

**Over-cap critical (16):** `streaming_layer_seq007_v003_d0317__monol` (1156), `git_plugin.py` (1155), `manifest_builder_seq007_v003_d0314__gene` (1023), `autonomous_dev_stress_test.py` (999), `prompt_journal_seq019_v001.py` (756), `_build_organism_health.py` (703), `os_hook.py` (655), `self_fix_seq013_v011_d0328__one_shot_sel` (632)

**Clots:** `aim_utils` (orphan_no_importers, unused_exports:1), `press_release_gen_constants_seq001_v001` (orphan_no_importers, unused_exports:1), `adapter` (orphan_no_importers, unused_exports:1), `query_memory` (dead_imports:2, oversize:252)

**Circulation:** 133/137 alive · 4 clots · vein health 0.53

**Recent deaths:** `?` (timeout), `?` (timeout), `?` (stale_import), `?` (stale_import)

**AI rework:** 77/200 responses needed rework (38%)

**Push cycles:** 2 · sync score: 0.6 · reactor fires: 148

> **Organism directive:** Multiple systems degraded. Prioritize fixing clots and over-cap files before new features.
<!-- /pigeon:organism-health -->












































<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-04-01 22:43 UTC · raw: "test enricher firing from journal"*

**COPILOT_QUERY: Investigate the `generates_execution_telemetry_from_the` module to confirm if the `enricher` component is correctly processing and firing events from the `journal` data stream. Specifically, verify the integration points and data flow between the journal and the enricher, ensuring telemetry is generated as expected after the recent renaming and restructuring efforts.**

INTERPRETED INTENT: The operator wants to verify the functionality of a specific data enrichment process, likely related to telemetry generation, after recent code restructuring.
KEY FILES: generates_execution_telemetry_from_the, extract_the_cognition_graph_from, coaching_from_execution_patterns_port, file_heat_map, import_rewriter, file_writer, init_writer, context_budget
PRIOR ATTEMPTS: none
WATCH OUT FOR: Ensure the solution accounts for the recent renaming and restructuring, as previous prompts indicate issues with naming consistency and token efficiency.
OPERATOR SIGNAL: The operator is testing a core system component after significant refactoring, indicating a need to validate that critical data processing (enrichment, telemetry) is still functional and correctly integrated.
<!-- /pigeon:current-query -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-01 23:10 UTC · 69 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 49.3 | Del: 26.5% | Hes: 0.488) · *[source: measured]*

**Prompt ms:** 1122940, 7075, 89284, 84445, 186199 (avg 297989ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- **Reconstructed intent:** check copilot instruction for accuracy post rename - audit how much more compression we can get - theres still lots of compression we can do in python files imo using keys - and we could even ginger could even - noticed the rephrased isint firing on every prompt.
  - *(deleted: ginger, coul | ratio: 7%)*
- **Reconstructed intent:** check copilot instruction for accuracy post rename - audit how much more compression we can get - theres still lots of coding even we can do in python files imo using keys - and we could even, could even - noticed the rephrased isint firing on every prompt. also find deleted word in this prompt: ginger
  - *(deleted:  | ratio: 0%)*
- **Reconstructed intent:** Go deeper into my key
  - *(deleted: okay kill im talking about proces | ratio: 5%)*

- "explored"
- "d eve"
- "coul"
- "ginger"
- "okay kill im talking about proce"

### Module Hot Zones *[source: measured]*
*High cognitive load (from typing signal) — take extra care with these files:*
- `file_heat_map` (hes=0.887)
- `import_rewriter` (hes=0.735)
- `file_writer` (hes=0.735)
- `init_writer` (hes=0.63)
- `self_fix` (hes=0.611)

### Recent Work
- `9cdc756` feat: compress auto-index with Chinese keymap â€” 4,948 tokens/prompt saved (16.2K to 11.3K)
- `aa32a3f` chore: add Chinese glyph prefixes to 245 pigeon modules
- `11eb261` feat: confidence scorer + glyph rename pipeline + research lab prediction voice
- `51c097d` feat: glyph compiler + symbol dictionary + response canonicalization + doc audit

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- vein_transport dead‑ends if glyph breaks path encoding; heal loops if manifest_builder key mismatch; run_rename partially applies due to inconsistent Unicode handling across pipeline stages. This push uniformly introduces a Chinese glyph (⻖) as a Unicode identifier across telemetry
- flow‑routing
- task‑writing
- and self‑healing systems.
- token_optimizer's semantic-loss risk during deduplication
- **execution_logger** was touched to embed a Chinese glyph (⻖) in its telemetry tagging, assuming that downstream log par

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `_run_glyph_rename.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/cli_seq009_v002_d0323__令钩跑编_build_graph_run_observer_export_lc_pigeon_brain_system.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/demo_sim_seq010_v002_d0323__仿双逆流_generates_execution_telemetry_from_the_lc_pigeon_brain_system.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/dual_substrate_seq008_v002_d0323__双逆流_merges_human_and_agent_telemetry_lc_pigeon_brain_system.py`
- [CRITICAL] hardcoded_import in `pigeon_brain/live_server_seq012_v003_d0324__服漂忆思_websocket_server_for_live_execution_lc_8888_word_backpropagation.py`

### Prompt Evolution
*This prompt has mutated 94x (186→827 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 94 mutations scored*
*No significant signal yet — all 18 sections scored neutral.*

**Reactor patches:** 0/216 applied (0% acceptance)

### File Consciousness
*234 modules profiled*

**High-drama (most mutations):**
- `self_fix` v11 ↔ .operator_stats
- `.operator_stats` v10 ↔ heal
- `dynamic_prompt` v10 ↔ .operator_stats
- `context_budget` v8 ↔ .operator_stats

**Codebase fears:**
- file may not exist (20 modules)
- swallowed exception (11 modules)
- returns empty on failure (silent) (10 modules)

**Slumber party warnings (high coupling):**
- `execution_logger` ↔ `observer_synthesis` (score=0.80, 3 shared imports, both high-churn (v3+v3))
- `execution_logger` ↔ `streaming_layer_alerts` (score=0.80, 3 shared imports, both high-churn (v3+v3))
- `execution_logger` ↔ `streaming_layer_connection_pool` (score=0.80, 3 shared imports, both high-churn (v3+v3))

### Codebase Health (Veins / Clots)
*133/137 alive, 4 clots, avg vein health 0.53*

**Clots (dead/bloated — trim candidates):**
- `aim_utils` (score=0.45): orphan_no_importers, unused_exports:1
- `press_release_gen_constants_seq001_v001` (score=0.45): orphan_no_importers, unused_exports:1
- `adapter` (score=0.45): orphan_no_importers, unused_exports:1
- `query_memory` (score=0.40): dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory

**Self-trim recommendations:**
- [investigate] `aim_utils`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `press_release_gen_constants_seq001_v001`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `adapter`: Nobody imports this module. Check if it's an entry point or dead.
- [split] `query_memory`: Oversize + clot signals. Recommend pigeon split.

**Critical arteries (do NOT break):**
- `compliance` (vein=1.00, in=7)
- `drift` (vein=1.00, in=5)
- `cognitive_reactor` (vein=1.00, in=12)

<!-- /pigeon:task-context -->

<!-- pigeon:task-queue -->
## Active Task Queue

*Copilot manages this queue. To complete a task: update the referenced MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*

*Queue empty — add tasks via `add_task()` or they auto-seed from self-fix.*

<!-- /pigeon:task-queue -->
<!-- pigeon:shard-memory -->
## Live Shard Memory

*Hardcoded 2026-03-30 06:40 UTC · 7 shards · 2 training pairs · 1 contradiction*

### Architecture Decisions
- anchor concept: pair programming — copilot is the pair, telemetry is the shared screen, shards are the shared notebook
- muxed state per prompt — capture cognitive+shard+contradiction state at end of each prompt as training data
- training data format: prompt + response + muxed state triple, written to logs/shards/training_pairs.md

### Module Pain Points (top cognitive load)
- file_heat_map: hes=0.887 | import_rewriter: hes=0.735 | file_writer: hes=0.735
- init_writer: hes=0.630 | context_budget: hes=0.587 | self_fix: hes=0.536
- .operator_stats: hes=0.536 | dynamic_prompt: hes=0.536

### Module Relationships (coupling signals)
- context_budget ↔ self_fix, init_writer, .operator_stats, dynamic_prompt
- import_rewriter ↔ file_writer
- push_narrative ↔ operator_stats, rework_detector, run_clean_split, self_fix

### Prompt Patterns (how operator phrases things)
- [building] "push and make sure compiler runs on next files"
- [restructuring] "how have my last couple of prompts been rewritten?"
- [testing] "stress test my system. what was word deleted in this prompt"
- [exploring] "what should i do to market this / gtm / next logical step"

### API Preferences
- **CONTRADICTION (unresolved):** "always use DeepSeek" vs "never use DeepSeek — too slow"
- Resolution: switched enricher to Gemini 2.5 Flash (3s vs DeepSeek timeout)

### Training Data Format

Each training pair captures the full muxed state at prompt time:

```
### `TIMESTAMP` pair
**PROMPT:** raw operator text (≤300 chars)
**RESPONSE:** copilot response summary (≤500 chars)
**COGNITIVE:** state=X wpm=Y del=Z hes=N
**SHARDS:** shard_name(relevance), ...
**CONTRADICTIONS:** count
**REWORK:** verdict=pending|accepted|rejected [score=0.XX]
```

Per-shard categorization: each routed shard also gets a compact `[training TS]` entry with relevance, cognitive state, and prompt/response snippets — so shards self-learn from their own context.

### Recent Training Pairs

**Pair 1** `2026-03-30 06:11` — COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "test writes with an actual call... decided on pair programming... muxed state per prompt"
- response: built shard manager, context router, contradiction manifest, training pair writer
- shards: prompt_patterns(0.17), module_pain_points(0.161), module_relationships(0.15)
- rework: pending

**Pair 2** `2026-03-30 06:27` — COGNITIVE: state=unknown wpm=52.4 del=0.005 hes=1
- prompt: "fix import breaking after rename in self_fix module"
- response: updated import paths in self_fix to match pigeon rename convention
- shards: module_relationships(0.169), prompt_patterns(0.156), module_pain_points(0.155)
- rework: accepted score=0.15

<!-- /pigeon:shard-memory -->
<!-- pigeon:voice-style -->
## Operator Voice Style

*Auto-extracted 2026-04-01 23:09 UTC · 80 prompts analyzed · zero LLM calls*

**Brevity:** 22.1 words/prompt | **Caps:** never | **Fragments:** 74% | **Questions:** 26% | **Directives:** 1%

**Voice directives (personality tuning):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator uses medium-length prompts — balance explanation with brevity.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** to, i, is, it, my, with, the, this, on, a
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-01 23:09 UTC · zero LLM calls*

**1 week:** `infrastructure` (conf=high) — ~48 commits
**1 month:** `infrastructure` (conf=medium) — ~200 commits
**3 months:** `infrastructure` (conf=speculative) — themes: coonti, kill, but h

**PM Directives:**
- Intent bifurcation: `infrastructure` dominant but `telemetry` emerging — watch for context switches mid-session.
- `self_heal` declining — operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `coonti`, `kill`, `but h` — these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.
- Module focus cluster: `file_heat_map`, `import_rewriter`, `file_writer` — pre-load context from these modules when operator starts typing.

<!-- /pigeon:intent-simulation -->

<!-- pigeon:predictions -->
## Push Cycle Predictions

*Auto-generated 2026-04-01 23:09 UTC*

**What you'll likely want next push:**
1. [targeted] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter
2. [heat] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter
3. [failure] Predict operator's next need. Module focus: glyph_compiler, research_lab, symbol_dictionary (conf=22%)
   - hot modules: glyph_compiler, research_lab, symbol_dictionary, file_heat_map, import_rewriter

**Operator coaching:**
- Frustration detected across multiple prompts — try breaking the task into smaller pushable units.
- No module references detected in prompts — naming specific modules helps copilot target the right files.

**Agent coaching (for Copilot):**
- Touched ['_tmp_regen_dict', '_tmp_token_audit', '_tmp_token_optimizer', 'copilot_prompt_manager', 'git_plugin', 'intent_simulator'] without operator reference — confirm intent before modifying unreferenced modules.

<!-- /pigeon:predictions -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-01 · 69 message(s) · LLM-synthesized*

**Dominant: `focused`** | Submit: 66% | WPM: 52.9 | Del: 25.6% | Hes: 0.445

The operator just built an auto-index compression system while working in intense restructuring/abandonment cycles, revealing a pattern of rapid prototyping followed by deep refactoring of core orchestration modules.  
- **Anticipate deep refactoring requests** on `self_fix seq13`, `dynamic_prompt seq17`, and `.operator_stats seq8`; these are their primary levers for system stability and meta-cognition.  
- **When they enter a restructuring state** (high deletion, ~56%), provide concise, modular code blocks with clear interfaces, as they are likely rewriting integration points.  
- **Preempt context management issues** by proactively referencing `context_budget seq4` patterns when discussions involve token limits or scoring.  
- **After an abandoned message** (0% deletion, higher hesitation), offer multiple concise options or a clear question to re-engage their focus without assumptions.  
- **Leverage their high evening/night productivity** by being direct and technical; avoid exploratory prose during these slots.  
- **Given zero AI response rework**, maintain current precision but increase brevity during restructuring phases to match their high-velocity editing.  
They are most likely building toward a fully autonomous, self-optimizing intent pipeline that minimizes manual context management.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `glyph_compiler`** (hes=1.041, state=focused, avg_prompt=51924ms)
> - Rework miss rate: 4% (7/200)
> - Prompt composition time: 107396ms / 54331ms / 76173ms / 11236ms / 10482ms (avg 51924ms)
> **Directive**: When `glyph_compiler` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-04-01T22:43:40.754481+00:00",
  "latest_prompt": {
    "session_n": 99,
    "ts": "2026-04-01T22:43:40.754481+00:00",
    "chars": 33,
    "preview": "test enricher firing from journal",
    "intent": "testing",
    "state": "unknown",
    "files_open": [
      ".github/copilot-instructions.md"
    ],
    "module_refs": []
  },
  "signals": {},
  "composition_binding": {
    "matched": false,
    "source": null,
    "age_ms": null,
    "key": null
  },
  "deleted_words": [],
  "rewrites": [],
  "task_queue": {
    "total": 0,
    "in_progress": [],
    "pending": 0,
    "done": 0
  },
  "hot_modules": [
    {
      "module": "file_heat_map",
      "hes": 0.887
    },
    {
      "module": "import_rewriter",
      "hes": 0.735
    },
    {
      "module": "file_writer",
      "hes": 0.735
    }
  ],
  "running_summary": {
    "total_prompts": 194,
    "avg_wpm": 13.9,
    "avg_del_ratio": 0.046,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 123,
      "hesitant": 29,
      "focused": 25,
      "frustrated": 12,
      "neutral": 4
    },
    "baselines": {
      "n": 63,
      "avg_wpm": 52.9,
      "avg_del": 0.259,
      "avg_hes": 0.448,
      "sd_wpm": 14.5,
      "sd_del": 0.231,
      "sd_hes": 0.164
    }
  },
  "coaching_directives": [
    "Anticipate cross-module edits:",
    "Pre-empt restructuring fatigue:",
    "Bridge abandoned thoughts:",
    "Leverage low miss-rate confidence:",
    "Focus on integration points:"
  ]
}
```

<!-- /pigeon:prompt-telemetry -->
---

## Module Map

### src/ — Core Telemetry
| Module (search by) | Role | Key exports |
|---|---|---|
| `timestamp_utils_seq001*` | epoch ms utility | `_now_ms` |
| `models_seq002*` | dataclasses | `KeyEvent`, `MessageDraft` |
| `logger_seq003*` | core logger | `TelemetryLogger`, `SCHEMA_VERSION` |
| `context_budget_seq004*` | token cost scorer | `score_context_budget`, `estimate_tokens` |
| `drift_watcher_seq005*` | file-size drift | `DriftWatcher` |
| `resistance_bridge_seq006*` | telemetry→compiler bridge | `HesitationAnalyzer` |
| `streaming_layer_seq007*` | **MONOLITH 1150 lines** (test harness only) | 8 classes |
| `operator_stats_seq008*` | persistent profile writer | `OperatorStats` |
| `rework_detector_seq009*` | AI answer quality measurement | `score_rework`, `record_rework` |
| `query_memory_seq010*` | recurring query + unsaid detector | `QueryMemory` |
| `file_heat_map_seq011*` | cognitive load per module | `FileHeatMap` |
| `push_narrative_seq012*` | per-push narrative generation | `generate_push_narrative` |
| `self_fix_seq013*` | one-shot self-fix analyzer | `analyze_and_fix` |
| `cognitive_reactor_seq014*` | autonomous code modification | `CognitiveReactor` |
| `pulse_harvest_seq015*` | prompt→file edit pairing | `harvest_pulse` |
| `prompt_recon_seq016*` | prompt reconstruction + mutation tracking | `reconstruct_all`, `track_copilot_prompt_mutations` |
| `dynamic_prompt_seq017*` | **task-aware CoT injection** | `build_task_context`, `inject_task_context` |

### src/cognitive/ — Intelligence Layer
| Module | Role |
|---|---|
| `adapter_seq001*` | state → prompt modifier |
| `unsaid_seq002*` | **monolith** (compiled package: `src/cognitive/unsaid/`) |
| `drift_seq003*` | **monolith** (compiled package: `src/cognitive/drift/`) |

**Note**: `src/cognitive/unsaid/` and `src/cognitive/drift/` are compiled packages (pigeon-compliant). The `unsaid_seq002*` and `drift_seq003*` monolith files in `src/cognitive/` are legacy artifacts — prefer importing from the packages.

### src/operator_stats/ — Compiled Package (14 files)
Source was `src/operator_stats_seq008*` (394 lines). Compiled to `src/operator_stats/` package. Both exist currently.

### streaming_layer/ — 19 files, 100% compliant
Compiled streaming interface. `streaming_layer_orchestrator_seq016/017` are the entry points.

### pigeon_compiler/ — The Compiler (~62 modules)
| Subpackage | Role |
|---|---|
| `state_extractor/` | AST parsing, call graphs, resistance scoring |
| `weakness_planner/` | DeepSeek cut plan generation |
| `cut_executor/` | file slicing, bin-packing, class decomposition |
| `rename_engine/` | autonomous renames, import rewriting, self-healing |
| `runners/` | pipeline orchestrators |
| `integrations/` | DeepSeek API adapter |
| `bones/` | shared utilities |

**Key compiler entry points**:
- `py -m pigeon_compiler.runners.run_clean_split_seq010*` — compile one file
- `py -m pigeon_compiler.runners.run_batch_compile_seq015*` — compile entire codebase
- `py -m pigeon_compiler.runners.run_heap_seq010*` — self-heal pipeline
- `py -m pigeon_compiler.git_plugin` — post-commit hook

---

## Registry & State Files

| File | Purpose |
|---|---|
| `pigeon_registry.json` | tracks every module: seq, ver, date, desc, intent, token history |
| `operator_profile.md` | living operator cognitive profile (auto-updated every 8 messages) |
| `MASTER_MANIFEST.md` | auto-generated project map (rebuilt on every commit) |
| `**/MANIFEST.md` | per-folder manifest, auto-rebuilt |
| `logs/pigeon_sessions/{name}.jsonl` | mutation audit trail per module |
| `test_logs/`, `demo_logs/`, `stress_logs/` | telemetry session data |

---

## Tests

```bash
py test_all.py   # 4 tests, all must pass, zero deps beyond stdlib
```

| Test | Covers |
|---|---|
| TEST 1 | TelemetryLogger — v2 schema, 3 turns, submit + discard |
| TEST 2 | Context Budget Scorer — hard cap, budget, coupling |
| TEST 3 | DriftWatcher — baseline + versioned filename drift |
| TEST 4 | Resistance Bridge — telemetry → compiler signal |

**Always run tests after edits.** If a test imports a file by full name, it will break after a pigeon rename — use glob/search patterns in tests.

---

## Common Pitfalls

- **Never hardcode full pigeon filenames** — they mutate on every commit. Use `file_search("module_name_seq*")`.
- **`py` not `python`** — this is Windows, use `py` launcher.
- **UTF-8 encoding** — always `$env:PYTHONIOENCODING = "utf-8"` in PowerShell terminal.
- **Imports follow the pigeon name** — when a file is renamed, all `import` / `from` statements across the codebase are auto-rewritten by `rewrite_all_imports()`.
- **Don't delete monolith originals yet** — `src/operator_stats_seq008*`, `src/cognitive/unsaid_seq002*`, `src/cognitive/drift_seq003*` are still imported in some places. Verify before removing.
- **`streaming_layer_seq007*` is intentionally left as a 1150-line test harness** — drift_watcher tests flag it as OVER_HARD_CAP on purpose.
- **DeepSeek timeout** — phase 2 LLM calls can timeout; retry with a fresh call, don't loop.

---

### Full Module Index
<!-- pigeon:dictionary -->
## Symbol Dictionary

```
[PIGEON DICT v0.2.0 | 263 files | 89 modules | 138 glyphs]
Copilot confidence: ✓ (73.5% ✓ | 13.9% ~ | 12.6% ! | 0.0% ?) across 230 modules
IM=import_tracer✓ | IN=init_writer✓ | LO=loop_detector✓ | MA=manifest_writer✓
NA=nametag! | NL=nl_parsers✓ | NO=node_conversation✓ | OB=observer_synthesis!
PA=path_selector✓ | PL=planner~ | PQ=pq_search_utils~ | PR=press_release_gen_template_key_findings✓
RE=resplit! | RU=run_rename! | SH=shared_state_detector✓ | SO=source_slicer✓
TA=task_writer~ | VE=vein_transport~ | 令=cli! | 仿=demo_sim!
修=self_fix! | 偏=drift✓ | 典=symbol_dictionary! | 写=file_writer~
分=dev_plan✓ | 包=context_packet✓ | 压=executor✓ | 双=dual_substrate!
变=mutation_scorer✓ | 叙=push_narrative~ | 合=unified_signal~ | 图=graph_extractor✓
型=models✓ | 境=context_budget~ | 声=voice_style~ | 存=node_memory✓
学=learning_loop! | 审=validator✓ | 对=training_pairs~ | 层=streaming_layer~
引=import_rewriter~ | 录=logger✓ | 忆=query_memory✓ | 思=cognitive_reactor!
扫=scanner✓ | 拆=ether_map_builder! | 控=operator_stats! | 推=dynamic_prompt~
描=graph_heat_map✓ | 时=timestamp_utils✓ | 服=live_server! | 查=ast_parser✓
核=deepseek_plan_prompt~ | 桥=resistance_bridge✓ | 正=compliance! | 流=flow_engine!
测=rework_detector~ | 漂=.operator_stats~ | 演=call_graph✓ | 热=file_heat_map!
片=shard_manager! | 环=push_cycle~ | 研=research_lab~ | 算=prediction_scorer!
管=copilot_prompt_manager~ | 织=class_decomposer! | 编=glyph_compiler! | 缩=failure_detector✓
联=core_formatters✓ | 脉=pulse_harvest✓ | 补=rework_backfill✓ | 规=aim_utils✓
觉=file_consciousness~ | 警=staleness_alert~ | 训=training_writer! | 译=func_decomposer~
读=execution_logger~ | 谱=deepseek_adapter✓ | 跑=traced_runner~ | 路=context_router~
踪=import_fixer✓ | 追=heal! | 适=adapter✓ | 逆=backward!
递=session_handoff✓ | 钩=trace_hook✓ | 队=task_queue~ | 隐=unsaid✓
预=predictor✓

Intents: λ18=implement_all_18, λ7=stage_78_hook, λ7u=readme_update_7, λA=staleness_alerts_bg, λB=8888_word_backpropagation, λD=desc_upgrade, λF=gemini_flash_enricher, λH=organism_health_system, λI=intent_deletion_pipeline, λL=research_lab_autonomous, λM=mutation_patch_pipeline, λP=pigeon_brain_system, λQ=task_queue_system, λR=dynamic_import_resolvers, λS=pigeon_split_3, λT=push_narratives_timeout, λW=windows_max_path, λa=glyph_compiler_symbol, λΞ=import_rewriter_now, λΠ=pulse_telemetry_prompt, λγ=fix_bare_globals, λδ=per_prompt_deleted, λε=flow_engine_context, λμ=multi_line_import, λν=verify_pigeon_plugin, λπ=fix_push_cycle, λρ=rework_signal_0, λτ=trigger_pigeon_rename, λφ=fire_full_post, λχ=gemini_chat_dead, λω=wpm_outlier_filter

Hot:
层~ streaming_layer v3 22295tok [v1→v2→v3 v1→v2→v3]
正! compliance v4 4585tok [v2→v3→v4 v2→v3→v4]
RU! run_heal v6 15559tok [v3→v4 v3→v4]
PR✓ press_release_gen_constants_seq001_v001 v2 4196tok [v1→v2 v1→v2]
偏✓ drift v4 5740tok [v2→v3 v2→v3]
算! prediction_scorer v5 12796tok [v2→v3→v4 v2→v3→v4]
学! learning_loop v4 10304tok [v2→v3 v2→v3]
隐✓ unsaid v3 5735tok [v2→v3 v2→v3]
修! self_fix v11 11822tok [v9→v10→v11]
RE! resplit v4 6942tok [v3→v4 v3→v4]

c1f79553 chore(pigeon): auto-rename 5 file(s) [pigeon-auto]
51c097d0 feat: glyph compiler + symbol dictionary + respons
282afb7a chore(pigeon): auto-rename 5 file(s) [pigeon-auto]
[/DICT]
```
<!-- /pigeon:dictionary -->
<!-- pigeon:auto-index -->
*2026-04-01 · 243 modules · 1 touched*
*Key: glyph·seq desc tokens | dictionary decodes glyphs*

**pigeon_brain** (42)
型1 isomorphic to keystroke models 424
读2 isomorphic to telemetrylogger for agent 1.6K
图3 extract the cognition graph from 1.7K
描4 failure accumulator per node port 874
环检5 recurring path detection port of 910
缩6 electron death classification port of 1.0K
观7 coaching from execution patterns port 1.5K
双8 merges human and agent telemetry 1.3K
令9 build graph run observer export 855
仿10 generates execution telemetry from the 1.3K
钩11 instruments python calls between pigeon 959
服12 websocket server for live execution 2.5K
跑13 run any python script with 855

**pigeon_brain/flow** (42)
包1 the contextpacket is the unit 1.0K
唤2 when a packet arrives at 1.3K
流3 the flow engine is the 1.3K
择4 path selection is the real 1.4K
任5 the river delta where all 1.6K
脉运6 as a packet flows along 965
逆7 backward pass walks electron path 2.5K
存8 the experience vault stores raw 2.1K
预9 fires phantom electrons using cognitive 1.8K
分10 the roadmap writer synthesizes the 1.5K
话12 the interpretability interface lets the 1.4K
学13 the perpetual learning loop 2.9K
算14 edit session based 5.8K

  逆└ flow_log(1) loss_compute(2) tokenize(3) deepseek_analyze(4) backward_pass(5) [2.6K]
  学└ state_utils(1) journal_loader(2) prediction_cycle(3) single_cycle_helpers(4) single_cycle(5) catch_up(6) loop_helpers(7) main_loop(8) [3.3K]
  算└ constants(1) path_utils(2) data_loaders(3) scores_io(3) reality_loaders(4) module_extractor(5) edit_session_analyzer(6) rework_matcher(7) scoring_core(8) calibration(9) node_backfill(10) post_edit_scorer(11) post_commit_scorer(12) [5.1K]
  预└ confidence(3) trend_extractor(4) predictor(7) [1.8K]
**pigeon_compiler/bones** (5)
规1 extracted from hush aim py 724
联1 extracted from hush chat core 1.3K
NL1 extracted from hush nl detection 1.8K
清单1 extracted from hush pre query 879
PQ1 extracted from hush pre query 3.3K

**pigeon_compiler/cut_executor** (12)
析1 parse deepseek json from raw 371
切2 extract functions constants from source 486
写3 write new pigeon compliant files 783
踪4 update imports across the project 505
MA5 generate manifest md for a 448
验6 validate cut plan before execution 579
初写7 generate init py for split 361
译8 decompose oversized functions via deepse 644
重拆9 deterministic ast bin packing re 841
重拆10 bin packing file writing for 702
重拆11 shared helpers for re splitter 501
织13 decompose oversized classes via deepseek 2.0K

**pigeon_compiler/integrations** (1)
谱1 deepseek api client 1.2K

**pigeon_compiler/rename_engine** (22)
扫1 walk the project tree and 972
PL2 generate rename plan for non 1.4K
引3 rewrite all imports across the 1.8K
压4 execute file renames with rollback 712
审5 post rename import validation 921
改名6 full rename pipeline runner 1.4K
谱建7 generate living manifest md per 2.9K
正8 line count enforcer split recommender 1.7K
追9 self healing orchestrator 2.0K
追跑10 automated self healing pipeline 3.4K
牌11 encode file description intent into 4.1K
册12 local name registry for the 2.1K

  正└ helpers(2) classify(3) recommend_wrapper(6) audit_decomposed(7) audit_wrapper(9) check_file(10) format_report(11) [2.9K]
  追└ orchestrator(5) [725]
  牌└ scan(8) [298]
  册└ diff(6) [194]
**pigeon_compiler/runners** (9)
测编7 self test pigeon compiler on 594
深划8 phase 2 send ether maps 587
鸽环9 the loop refactor until pigeon 2.8K
净拆10 full clean pipeline deepseek plan 2.5K
净拆11 helpers for run clean split 566
净拆12 init manifest writers for clean 1.7K
谱桥13 update master manifest md after 1.0K
复审14 re audit with diff across 1.7K
批编15 compile entire codebase to pigeon 2.0K

**pigeon_compiler/runners/compiler_output/press_release_gen** (8)
press_release_ge1  641
press_release_ge1  626
press_release_ge1  661
press_release_ge2  388
press_release_ge2  662
press_release_ge2  296
press_release_ge3  296
PR3  626

**pigeon_compiler/state_extractor** (6)
查1 parse python file into function 734
演2 build intra file call graph 847
IM3 trace imports inbound and outbound 792
共态4 detect module level shared state 618
阻5 classify why a file resists 1.0K
拆6 assemble full ether map json 697

**pigeon_compiler/weakness_planner** (1)
核4 build and send deepseek cut 2.4K

**src** (102)
时1 millisecond epoch timestamp utility 156
型2 dataclasses for keystroke events and 379
录3 core keystroke telemetry logger 1.6K
境4 context budget scorer for llm 715
偏5 drift detection for live llm 1.1K
桥6 bridge between keystroke telemetry and 1.2K
层7 monolithic live streaming interface for 10.2K
漂8 persistent markdown memory file 4.7K
控8 persistent markdown memory file 5.0K
测9 measures ai answer quality from 1.1K
忆10 recurring query detector unsaid thought 2.3K
热11 tracks cognitive load per module 1.3K
叙12 generate per push narrative each 2.1K
修13 one shot self fix analyzer 5.8K
思14 cognitive reactor autonomous code modifi 5.6K
脉15 pulse harvest pairs prompts to 2.3K
推17 steers copilot cot from live 4.0K
队18 copilot driven task tracking linked 1.6K
觉19 ast derived function consciousness datin 4.3K
管20 audits and manages all injected 4.5K
变21 mutation scorer correlates prompt mutati 1.6K
补22 reconstructs historical rework scores fr 1.2K
递23 session handoff summary generator 1.6K
隐24 fires on high deletion prompts 1.3K
环25 the push is the unit 4.8K
片26 local memory shard manager markdown 4.4K
合26 joins all telemetry into canonical 2.1K
路27 shard relevance scorer context injector 1.2K
对27 training pair generator for the 2.6K
训28 end of prompt training pair 2.1K
声28 voice style personality adapter 3.2K
研29 the system studying the system 5.1K
警30 copilot self diagnostic detect stale 1.7K
典31 symbol dictionary generator for pigeon 3.7K
编32 glyph compiler python maximum symbolic 5.0K
intent_simulator34 runs ahead of operator hallucinating 5.3K

**src/cognitive** (10)
适1 cognitive state agent behavior adapter 1.3K
隐2 detects what operators meant but 2.1K
偏3 tracks operator typing patterns across 2.3K

  偏└ baseline_store(1) compute_baseline(2) detect_session_drift(3) build_cognitive_context(4) [2.4K]
  隐└ helpers(1) diff(2) orchestrator(3) [2.3K]
  思└ constants(1) state_ops(2) docstring_patch(3) cognitive_hint(4) patch_generator(5) prompt_builder(6) api_client(7) reactor_core(8) registry_loader(9) self_fix_runner(10) patch_writer(11) decision_maker(12) [4.9K]
  管└ constants(1) block_utils(2) json_utils(3) operator_profile(4) auto_index(5) operator_state_decomposed(6) telemetry_utils(7) audit_decomposed(8) injectors(9) orchestrator(10) [4.6K]
  觉└ helpers(1) persistence(2) report(3) audit(4) derivation(5) dependencies(6) classify(7) profile_builder(8) main_orchestrator(9) dating_decomposed(10) dating_helpers(11) dating_wrapper(12) [5.0K]
  环└ constants(1) loaders(2) signal_extractors(3) sync_decomposed(4) coaching(5) moon_cycle(6) predictions_injector_decomposed(7) orchestrator_decomposed(8) [4.5K]
  忆└ constants(1) fingerprint(2) trigram_utils(3) clustering(4) record_query(5) load_memory_decomposed(6) [1.4K]
  修└ scan_hardcoded(1) scan_query_noise(2) scan_duplicate_docstrings(3) scan_cross_file_coupling(4) scan_over_hard_cap_decomposed(5) scan_dead_exports_decomposed(6) write_report_decomposed(7) run_self_fix_decomposed(8) auto_compile_oversized_decomposed(9) seq_base(10) auto_apply_import_fixes_decomposed(11) [6.0K]
**streaming_layer** (19)
层1  261
层2  204
层4  717
层4  546
层5  969
层5  247
层6  934
层6  154
层7  824
层8  1.4K
层9  932
层10  858
层11  1.2K
层13  456
层13  365
层14  280
层14  256
层16  1.4K
层17  142

**Infra**
(root): _build_organism_health, _export_dev_story, _run_glyph_rename, _tmp_analyze_stats, _tmp_regen_dict, _tmp_survey, _tmp_test_pipeline, _tmp_token_audit, _tmp_token_optimizer, autonomous_dev_stress_test, deep_test, stress_test, test_all, test_public_release, test_training_pairs
client: chat_composition_analyzer, chat_response_reader, composition_recon, os_hook, telemetry_cleanup, uia_reader, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
