# MASTER MANIFEST — keystroke-telemetry

*Auto-updated 2026-03-24 · 23 src modules · 19 streaming modules · ~62 compiler modules · 19 brain modules (13 core + 6 flow engine) · 7 React components*

**This codebase reads minds, rewires AI reasoning, refactors itself, watches the whole thing happen in a living neural visualization, reads its own deleted thoughts before starting work, and now routes context-accumulating intelligence packets through its own code graph.**

---

## System Overview

Four interlocking systems. Each one feeds the next. The last one watches all the others.

| System | Entry Point | Modules | Status |
|---|---|---:|---|
| **Keystroke Telemetry** | `src/` | 23 + 3 cognitive | ✅ Live |
| **Pigeon Code Compiler** | `pigeon_compiler/` | ~62 | ✅ Live |
| **Streaming Layer** | `streaming_layer/` | 19 | ✅ Live · 100% compliant |
| **Pigeon Brain** | `pigeon_brain/` | 19 + 7 React | **✅ Live · dual-substrate · real-time trace · context veins · flow engine** |
| **Flow Engine** | `pigeon_brain/flow/` | 6 | **✅ Live · context-accumulating dataflow · 3 routing modes** |
| **VS Code Extension** | `vscode-extension/` | — | ✅ Live · TypeScript |

---

## src/ — Core Telemetry (23 modules)

| Seq | Module (search by) | Lines | Status | Role |
|---|---|---:|---|---|
| 001 | `timestamp_utils_seq001*` | 23 | ✅ | Millisecond epoch utility |
| 002 | `models_seq002*` | 44 | ✅ | `KeyEvent`, `MessageDraft` dataclasses |
| 003 | `logger_seq003*` | 163 | ✅ | Core telemetry logger, `SCHEMA_VERSION` |
| 004 | `context_budget_seq004*` | 95 | ✅ | Token cost scorer, hard/soft caps |
| 005 | `drift_watcher_seq005*` | 108 | ✅ | Cross-session drift detection |
| 006 | `resistance_bridge_seq006*` | 124 | ✅ | Telemetry → compiler resistance signal |
| 007 | `streaming_layer_seq007*` | 1155 | 🔴 CRIT | **Intentional monolith** — test harness only |
| 008 | `operator_stats_seq008*` | 397 | 🟠 WARN | Persistent markdown memory, cognitive history |
| 009 | `rework_detector_seq009*` | 111 | ✅ | AI answer quality from typing signal |
| 010 | `query_memory_seq010*` | 125 | ✅ | Recurring query + unsaid thought detector |
| 011 | `file_heat_map_seq011*` | 144 | ✅ | Per-module cognitive load tracker |
| 012 | `push_narrative_seq012*` | 199 | ✅ | Per-push narrative — files speak as agents |
| 013 | `self_fix_seq013*` | 352 | 🟠 WARN | Cross-file problem detection + resolution |
| 014 | `cognitive_reactor_seq014*` | 350 | 🟠 WARN | Autonomous code modification from telemetry |
| 015 | `pulse_harvest_seq015*` | 254 | ⚠️ OVER | Prompt→file edit pairing, sub-second timing |
| 016 | `prompt_recon_seq016*` | 215 | ⚠️ OVER | Prompt reconstruction + mutation tracking |
| 017 | `dynamic_prompt_seq017*` | ~340 | ⚠️ OVER | **Task-aware CoT injection** into copilot-instructions.md + codebase health |
| 018 | `task_queue_seq018*` | 180 | ✅ | Copilot-managed task queue, auto-seeded from self-fix |
| 019 | `file_consciousness_seq019*` | ~200 | ✅ | AST-derived function consciousness dating |
| 020 | `copilot_prompt_manager_seq020*` | ~200 | ⚠️ OVER | Audits and manages all injected prompt blocks |
| 021 | `mutation_scorer_seq021*` | ~120 | ✅ | Correlates prompt mutations to rework scores |
| 022 | `rework_backfill_seq022*` | ~100 | ✅ | Reconstructs historical rework scores |
| 023 | `session_handoff_seq023*` | ~120 | ✅ | Session handoff summary generator |

### src/cognitive/ — Intelligence Layer (3 modules)

| Module | Lines | Status | Role |
|---|---:|---|---|
| `adapter_seq001*` | 125 | ✅ | Cognitive state → agent behavior adapter |
| `unsaid_seq002*` | 226 | ⚠️ OVER | Detects what operators meant but didn't say |
| `drift_seq003*` | 234 | ⚠️ OVER | Typing pattern drift across sessions |

### Data Flow

```
VS Code Extension (keystrokes)
  └─ flush → classify_bridge.py
       └─ OperatorStats.ingest() → operator_profile.md

PER-PROMPT PIPELINE (prompt_journal_seq019):
  1. Force fresh composition            (analyze_and_log() from raw keystrokes)
  2. Bind composition to prompt         (text similarity, score ≥ 0.95 bypasses age)
  3. Extract deleted_words + rewrites   (from bound composition)
  4. Predict next struggles             (journal history pattern mining)
  5. Write prompt_telemetry_latest.json (snapshot: binding + predictions)
  6. Inject into copilot-instructions   (<!-- pigeon:prompt-telemetry -->)
  Result: Copilot sees your deleted words BEFORE starting work.

POST-COMMIT PIPELINE (git_plugin.py):
  1. Rename files + bump versions       (pigeon naming convention)
  2. Rewrite all imports                (auto-heals after renames)
  3. Rebuild MANIFEST.md files          (17 folders)
  4. prompt_recon_seq016                → prompt_compositions.jsonl + copilot_mutations.json
  5. self_fix_seq013                    → docs/self_fix/{hash}.md
  6. push_narrative_seq012              → docs/push_narratives/{hash}.md
  7. DeepSeek API call                  → operator_coaching.md
  8. dynamic_prompt_seq017              → .github/copilot-instructions.md
     └─ inject_task_context()           (incl. codebase health from context_veins.json)
  9. task_queue_seq018                  → task_queue.json
     └─ inject_task_queue()
 10. auto-commit [pigeon-auto]
```

### Per-Prompt Telemetry

On every Copilot message, `prompt_journal_seq019` writes an enriched JSON entry to `logs/prompt_journal.jsonl` that cross-references: cognitive state, WPM, deletion ratio, deleted words, rewrites, active tasks, hot modules, intent classification, module refs, and running session stats. This is the unified analysis layer — one file to reconstruct any session.

**New (2026-03-24):** Per-prompt composition binding now works. Before building a response, `log_enriched_entry()` forces a fresh composition analysis from raw keystrokes, matches the current prompt to its composition via text similarity (score ≥ 0.95 bypasses age filter), and injects the operator's deleted words + rewrites directly into the `<!-- pigeon:prompt-telemetry -->` context block. Copilot sees what you deleted before it starts thinking.

**Predictive Debug:** `_predict_next_issues()` mines the prompt journal for three patterns:
1. Which modules appear in prompts after frustrated/hesitant states
2. Build→debug cycles (implement module X → debug module X within 5 prompts)
3. Module heat + recent mention trending

Predictions surface in `prompt_telemetry_latest.json` as `predicted_struggles` and are visible in every Copilot context window.

### Injected Context Blocks (in copilot-instructions.md)

| Block | Source | Sections |
|---|---|---|
| `<!-- pigeon:task-context -->` | `dynamic_prompt_seq017` | Task focus · Cognitive state + CoT directive · Unsaid threads · Module hot zones · AI rework surface · Recent work · **Coaching directives** · **Fragile contracts** · **Known issues** · **Persistent gaps** · Prompt evolution · **File consciousness** · **Codebase health (veins/clots)** |
| `<!-- pigeon:operator-state -->` | `git_plugin._refresh_operator_state()` | LLM-synthesized behavioral instructions |
| `<!-- pigeon:auto-index -->` | `git_plugin._refresh_copilot_instructions()` | All module token counts |

---

## streaming_layer/ — Compiled Package (19 modules, 100% compliant)

Original `src/streaming_layer_seq007*` (1155 lines) compiled by pigeon. All 19 files ≤200 lines.

Entry points: `streaming_layer_orchestrator_seq016*`, `streaming_layer_orchestrator_seq017*`

---

## pigeon_brain/ — The Neural Visualizer (19 modules + React UI)

**Treats the codebase as a neural network.** Every Python module is a neuron. Every import is a synapse. Human typing telemetry overlaid with machine execution traces — the only system that identifies which modules are killing both humans and AI simultaneously.

### Python Modules

| Seq | Module (search by) | Lines | Status | Role |
|---|---|---:|---|---|
| 001 | `models_seq001*` | ~85 | ✅ | `ExecutionEvent`, `Electron`, `DeathCause` — isomorphic to keystroke models |
| 002 | `execution_logger_seq002*` | ~150 | ✅ | Agent telemetry logger — stall detection, loop threshold, latency |
| 003 | `graph_extractor_seq003*` | ~150 | ✅ | AST + pigeon_registry → 137-node adjacency graph, 260 import edges |
| 004 | `graph_heat_map_seq004*` | ~120 | ✅ | Failure accumulation per node — danger zones, death rates, cause breakdown |
| 005 | `loop_detector_seq005*` | ~120 | ✅ | Recurring path fingerprinting — detects agents stuck in loops |
| 006 | `failure_detector_seq006*` | ~130 | ✅ | Death classification — stale (0.9), timeout (0.7), loop (0.65), exception (0.75) |
| 007 | `observer_synthesis_seq007*` | ~160 | ✅ | Aggregates execution telemetry → coaching Markdown + dual-substrate hotspots |
| 008 | `dual_substrate_seq008*` | ~200 | ✅ | **THE KILLER** — merges human hesitation + agent death rate → `dual_score` per node |
| 009 | `cli_seq009*` | ~120 | ✅ | CLI: `graph`, `observe`, `dual`, `stats`, `simulate`, `live`, `trace` |
| 010 | `demo_sim_seq010*` | ~180 | ✅ | Fake electron simulation with DANGER_PATTERNS for failure-prone modules |
| 011 | `trace_hook_seq011*` | ~150 | ✅ | `sys.settrace` → maps real Python calls to graph node names at runtime |
| 012 | `live_server_seq012*` | ~240 | ⚠️ OVER | WebSocket (ws://8765) + HTTP snapshot, 20Hz broadcast, event injection |
| 013 | `traced_runner_seq013*` | ~140 | ✅ | Wraps any Python script with trace hook, pushes events to live server |
| — | `context_veins.py` | ~350 | ✅ | **Codebase health** — import graph → vein/clot scoring, self-trim recommendations |

### pigeon_brain/flow/ — Context-Accumulating Dataflow Engine (6 modules, 100% compliant)

**Treats the code graph as a river system.** ContextPackets flow from an origin module through the graph. At each node, the module "wakes up" if relevant (keyword match, fear overlap, heat threshold, dependency chain) and contributes intelligence. Edges amplify or decay signal based on vein health. Terminal nodes synthesize everything into enriched Markdown tasks.

| Seq | Module (search by) | Lines | Status | Role |
|---|---|---:|---|---|
| 001 | `context_packet_seq001*` | 119 | ✅ | `ContextPacket` + `NodeIntel` dataclasses — decay (`IMPORTANCE_DECAY=0.92`), depth cap (`MAX_DEPTH=15`), loop death, `MAX_ACCUMULATED=30` |
| 002 | `node_awakener_seq002*` | 152 | ✅ | Relevance gating — keyword overlap, fear match, heat auto-relevant (≥0.5), dependency chain. `RELEVANCE_THRESHOLD=0.3` |
| 003 | `flow_engine_seq003*` | 172 | ✅ | Loads `graph_cache.json` + `dual_view.json` + `context_veins.json`, routes packets via `run_flow()` / `run_multi()` |
| 004 | `path_selector_seq004*` | 197 | ✅ | 3 routing modes: `targeted` (dependency chain, depth 10), `heat` (greedy dual-score, depth 8), `failure` (death signals, depth 6). `find_origin()` with tokenizer |
| 005 | `task_writer_seq005*` | 167 | ✅ | Terminal node — synthesizes accumulated NodeIntel → enriched Markdown. `write_multi()` merges 3 perspectives with consensus fears |
| 006 | `vein_transport_seq006*` | 120 | ✅ | Edge effects — amplify strong veins (`1.05×`), decay weak (`0.93×`), dead-vein warnings (`< 0.15`). Bidirectional edge check |

**How it works:**
1. `find_origin()` maps a keyword (e.g. `"self_fix"`) to a graph node
2. `path_selector` chooses the next hop based on mode (targeted walks dependencies, heat follows dual-scores, failure follows death signals)
3. At each node, `node_awakener` checks relevance — irrelevant nodes are skipped silently
4. Relevant nodes contribute `NodeIntel` (risk level, specific warnings, fears) to the packet
5. `vein_transport` amplifies/decays importance as the packet crosses edges
6. When the path ends, `task_writer` synthesizes everything into Markdown
7. `--multi` runs all 3 modes from the same origin and merges the perspectives

### React UI (`pigeon_brain/ui/`)

| Component | Role |
|---|---|
| `PigeonBrain.jsx` | Main graph — ReactFlow with 137 profiler-card nodes, live edge animation (green glow + drop-shadow), LIVE/OFFLINE indicator |
| `NodeNeuron.jsx` | Profiler card per module — name, version, stats grid (tokens/lines/calls/deaths/loops), heat bars (human + dual), personality, `cardFlash` on active |
| `ObserverPanel.jsx` | Right sidebar — aggregate stats, live event feed (call=green, return=blue, exception=red), dual-substrate hotspot list, full node profile on click |
| `ElectronLayer.jsx` | Animated electron dots flowing along edges |
| `useLiveTrace.js` | WebSocket hook — auto-reconnect (3s), TTL-based node/edge activation (800ms/1.2s), 200-event buffer |
| `styles.css` | Dark theme `#0a0a1a`, neon accents, `cardFlash` + `feedSlide` + `livePulse` keyframes |
| `vite.config.js` | Vite 5.3.5 + React plugin + custom middleware to serve `dual_view.json` |

**Stack:** React 18.3.1, @xyflow/react 12.0.0, Vite 5.3.5 (pinned — 5.4+ breaks on Windows w/ rolldown native binding)

### CLI Commands

```bash
py -m pigeon_brain graph      # Build cognition graph (137 nodes, 260 edges)
py -m pigeon_brain dual       # Generate dual-substrate view (human + agent heat merged)
py -m pigeon_brain observe    # Generate agent_coaching.md
py -m pigeon_brain stats      # Print graph statistics
py -m pigeon_brain simulate   # Run demo simulation with fake electrons
py -m pigeon_brain live       # Start WebSocket trace server (ws://8765, http://8766)
py -m pigeon_brain trace X.py # Run any script with real-time tracing

# ── Flow Engine ──
py -m pigeon_brain.flow --mode targeted --origin cognitive_reactor  # Targeted dependency chain
py -m pigeon_brain.flow --mode heat                                 # Greedy dual-score hotspots
py -m pigeon_brain.flow --mode failure                              # Death-signal path
py -m pigeon_brain.flow --multi --origin self_fix                   # Multi-perspective (all 3 modes)
```

### Data Files

| File | Purpose | Updated |
|---|---|---|
| `pigeon_brain/dual_view.json` | 137 enriched neurons — human hesitation + agent death merged per node | `py -m pigeon_brain dual` |
| `pigeon_brain/graph_cache.json` | Graph topology cache (137 nodes, 260 edges) | `py -m pigeon_brain graph` |
| `pigeon_brain/context_veins.json` | Vein/clot health scores per module + trim recommendations | `py -m pigeon_brain.context_veins .` |
| `pigeon_brain/exec_events.jsonl` | Execution event log (simulated or traced) | On simulation/trace |
| `pigeon_brain/trace_log.jsonl` | Trace hook output from `traced_runner` | `py -m pigeon_brain trace` |
| `pigeon_brain/flow/` (stdout) | Enriched Markdown tasks from flow engine routing | `py -m pigeon_brain.flow` |

### Data Flow

```
pigeon_registry.json (152 modules)
    │
    ▼
graph_extractor ─→ graph_cache.json (137 nodes, 260 edges)
    │
    ├─→ demo_sim (fake electrons)     ─┐
    ├─→ traced_runner (real electrons)  ├─→ execution_logger ─→ exec_events.jsonl
    └─→ trace_hook (sys.settrace)      ┘         │
                                                  ▼
                                    graph_heat_map + loop_detector + failure_detector
                                                  │
                                                  ▼
            file_heat_map.json ─→ dual_substrate ←─ graph_heat_map.json
            (human hesitation)                      (agent deaths)
                                        │
                                        ▼
                                  dual_view.json (137 enriched nodes)
                                        │
                          ┌─────────────┴─────────────────────┐
                          ▼                                   ▼
                    React UI                    WebSocket Server
                  (profiler cards,              (ws://127.0.0.1:8765)
                   edge animation,                    │
                   observer panel)                    ▼
                          ▲                     trace_hook events
                          └──── live events ────┘ (20 pushes/sec)
                                        │
                                        ▼
                              ┌── Flow Engine ──┐
                              │ graph_cache.json │
                              │ dual_view.json   │→ ContextPacket routes through graph
                              │ context_veins    │   nodes awaken, contribute intel
                              └──────┬───────────┘   edges amplify/decay signal
                                     ▼
                              task_writer → Markdown tasks
                              (targeted / heat / failure / multi-perspective)
```

---

## pigeon_compiler/ — The Compiler (~62 modules)

| Subpackage | Files | Role |
|---|---|---|
| `state_extractor/` | 6 | AST parsing, call graphs, resistance scoring |
| `weakness_planner/` | 1 | DeepSeek cut plan generation |
| `cut_executor/` | 11 | File slicing, bin-packing, class decomposition |
| `rename_engine/` | 12 | Autonomous renames, import rewriting, self-healing |
| `runners/` | 9 | Pipeline orchestrators |
| `integrations/` | 1 | DeepSeek API adapter |
| `bones/` | 5 | Shared utilities |
| root | 5 | `git_plugin`, `cli`, `pigeon_limits`, `session_logger`, `pre_commit_audit` |

Key entry points:
- `py -m pigeon_compiler.runners.run_clean_split_seq010*` — compile one file
- `py -m pigeon_compiler.runners.run_batch_compile_seq015*` — compile entire codebase
- `py -m pigeon_compiler.git_plugin` — post-commit hook

---

## Registry & State Files

| File | Purpose | Updated |
|---|---|---|
| `pigeon_registry.json` | Every module: seq, ver, date, desc, intent, token history | Every commit |
| `operator_profile.md` | Living cognitive profile, 45+ history entries | Every session |
| `operator_coaching.md` | DeepSeek-synthesized behavioral directives | Every 8 submitted msgs |
| `file_heat_map.json` | Per-module hesitation + WPM + miss counts | Per session |
| `rework_log.json` | AI response quality log | Per response |
| `query_memory.json` | Recurring queries + abandoned drafts | Per query |
| `task_queue.json` | Copilot-managed task queue (auto-seeded from self-fix) | Every commit |
| `pigeon_brain/dual_view.json` | 137 enriched neurons — dual-substrate heat per node | `py -m pigeon_brain dual` |
| `pigeon_brain/graph_cache.json` | Graph topology cache (137 nodes, 260 edges) | `py -m pigeon_brain graph` |
| `MASTER_MANIFEST.md` | This file | On demand |
| `**/MANIFEST.md` | Per-folder module reference | Every commit |
| `docs/push_narratives/*.md` | Per-commit module self-narratives | Every commit |
| `docs/self_fix/*.md` | Automated problem detection reports | Every commit |
| `logs/prompt_journal.jsonl` | Enriched prompt journal (cross-refs all telemetry per prompt) | Every message |
| `logs/chat_compositions.jsonl` | Keystroke compositions incl. deleted words + cognitive state | Every message |
| `logs/copilot_prompt_mutations.json` | Prompt file evolution snapshots | Every commit |

---

## Compliance Summary

| Package | Files | Compliant | Compliance % |
|---|---:|---:|---:|
| `src/` | 23 | 13 | 57% |
| `src/cognitive/` | 3 | 1 | 33% |
| `pigeon_brain/` (core) | 13 | 12 | **92%** |
| `pigeon_brain/flow/` | 6 | 6 | **100%** |
| `streaming_layer/` | 19 | 19 | **100%** |
| `pigeon_compiler/` (root) | 5 | 2 | 40% |
| `pigeon_compiler/rename_engine/` | 12 | 8 | 67% |
| `pigeon_compiler/runners/` | 9 | 6 | 67% |
| `pigeon_compiler/cut_executor/` | 11 | 11 | **100%** |
| `pigeon_compiler/state_extractor/` | 6 | 6 | **100%** |

**Known over-cap intentional exceptions:**
- `streaming_layer_seq007*` (1155 lines) — test harness, not in production path
- `git_plugin.py` (1038 lines) — orchestrator, single-module design requirement
- `operator_stats_seq008*` (397 lines) — candidate for next pigeon compile run
- `live_server_seq012*` (~240 lines) — WebSocket + HTTP dual server, marginal overage

