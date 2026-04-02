# MASTER MANIFEST — keystroke-telemetry

*Auto-updated 2026-03-30 · 28 src modules · 19 streaming modules · ~62 compiler modules · 19 brain modules (13 core + 6 flow engine) · 7 React components*

**This codebase reads minds, rewires AI reasoning, refactors itself, watches the whole thing happen in a living neural visualization, reads its own deleted thoughts before starting work, routes context-accumulating intelligence packets through its own code graph, cross-correlates physical keystrokes with AI edits, outputs intent-alignment training data per edit, and auto-tunes its own personality to match how you actually talk.**

---

## System Overview

Four interlocking systems. Each one feeds the next. The last one watches all the others.

| System | Entry Point | Modules | Status |
|---|---|---:|---|
| **Keystroke Telemetry** | `src/` | 28 + 3 cognitive | ✅ Live |
| **Pigeon Code Compiler** | `pigeon_compiler/` | ~62 | ✅ Live |
| **Pigeon Code Compilor (standalone)** | [`pip install pigeon-code-compilor`](https://myaifingerprint.com) | 13 | **✅ Released — open-source** |
| **Streaming Layer** | `streaming_layer/` | 19 | ✅ Live · 100% compliant |
| **Pigeon Brain** | `pigeon_brain/` | 19 + 7 React | **✅ Live · dual-substrate · real-time trace · context veins · flow engine** |
| **Flow Engine** | `pigeon_brain/flow/` | 6 | **✅ Live · context-accumulating dataflow · 3 routing modes** |
| **VS Code Extension** | `vscode-extension/` | — | ✅ Live · TypeScript |

---

## Novelty Thesis

This repo is close to something novel, but only if it is treated as one closed-loop system instead of a pile of adjacent experiments.

What is **not** novel on its own:
- keystroke telemetry
- prompt injection
- rename engines and compilers
- graph visualization
- narrative reports and coaching summaries

What is getting close to novel is the way those parts are being closed together into one adaptive surface:

1. The operator is modeled from raw typing before prompt submit.
2. The assistant is steered from deleted intent, hesitation, task context, and live codebase health.
3. The codebase exposes its own state through self-fix, veins/clots, rework, flow routing, and evolving metadata.
4. Every push and every prompt feed the next loop instead of producing dead reports.

That combination points at a different category than a normal coding assistant or a normal instrumentation stack. The emerging product is an **operator-aware development runtime**: a system that models the human, the assistant, and the repo simultaneously, then updates its own reasoning surface on every cycle.

The practical consequence is important: the canonical artifact should not be a dozen parallel dashboards. It should be one compressed reasoning surface that the model can actually use. The prompt blocks, auto-index, registry, file-state surfaces, and future filename encoding should converge toward that single control plane.

---

## src/ — Core Telemetry (28 modules)

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
| 024 | `unsaid_recon_seq024*` | ~100 | ✅ | Fires on high-deletion prompts, reconstructs unsaid intent via DeepSeek |
| 025 | `push_cycle_seq025*` | ~200 | ✅ | **The push is the unit** — cycle state, sync score, moon predictions, coaching |
| 026 | `unified_signal_seq026*` | ~200 | ✅ | Merges 6 telemetry sources → `unified_edits.jsonl` (3-tier waterfall) |
| 027 | `training_pairs_seq027*` | ~200 | ✅ | **Intent alignment training data** — per-edit + per-push user↔copilot pairs |
| 028 | `voice_style_seq028*` | ~250 | ✅ | **Personality adapter** — extracts operator voice from raw prompts, zero LLM |

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
 10. push_cycle_seq025                  → push cycle state + moon predictions
 11. training_pairs_seq027              → logs/training_cycle_summaries.jsonl
     └─ generate_cycle_summary()        (rework avg, latency, physical_keystroke_rate, intent distribution)
 12. voice_style_seq028                 → .github/copilot-instructions.md
     └─ inject_voice_style()            (extracts operator voice from 60+ prompts, zero LLM)
 13. auto-commit [pigeon-auto]
```

### Per-Prompt Telemetry

On every Copilot message, `prompt_journal_seq019` writes an enriched JSON entry to `logs/prompt_journal.jsonl` that cross-references: cognitive state, WPM, deletion ratio, deleted words, rewrites, active tasks, hot modules, intent classification, module refs, and running session stats. This is the unified analysis layer — one file to reconstruct any session.

**New (2026-03-28):** Per-prompt composition binding now works. Before building a response, `log_enriched_entry()` forces a fresh composition analysis from raw keystrokes, matches the current prompt to its composition via text similarity (score ≥ 0.95 bypasses age filter), and injects the operator's deleted words + rewrites directly into the `<!-- pigeon:prompt-telemetry -->` context block. Copilot sees what you deleted before it starts thinking.

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
| `<!-- pigeon:voice-style -->` | `voice_style_seq028` | Brevity · Caps · Fragments · Questions · Directives · Vocabulary fingerprint · Style directives |
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
py -m pigeon_brain.flow "Fix the hardcoded import in __main__.py"      # Targeted (default) with auto-origin
py -m pigeon_brain.flow --mode targeted --origin cognitive_reactor "analyze reactor drama"  # Explicit origin
py -m pigeon_brain.flow --mode heat "self_fix keeps failing"            # Greedy dual-score hotspots
py -m pigeon_brain.flow --mode failure "import rewriter breaks"         # Death-signal path
py -m pigeon_brain.flow --multi --origin self_fix "why does self_fix keep failing"  # Multi-perspective (all 3 modes)
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
pigeon_registry.json (188 modules)
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
| `rename_engine/` | 12 | Autonomous renames, import rewriting, self-healing — **extracted as [`pigeon-code-compilor`](https://myaifingerprint.com)** |
| `runners/` | 9 | Pipeline orchestrators |
| `integrations/` | 1 | DeepSeek API adapter |
| `bones/` | 5 | Shared utilities |
| root | 5 | `git_plugin`, `cli`, `pigeon_limits`, `session_logger`, `pre_commit_audit` |

Key entry points:
- `py -m pigeon_compiler.runners.run_clean_split_seq010*` — compile one file
- `py -m pigeon_compiler.runners.run_batch_compile_seq015*` — compile entire codebase
- `py -m pigeon_compiler.git_plugin` — post-commit hook

**Standalone open-source release:** The rename engine (scan, rename, import rewrite, compliance audit, manifest build) is available as `pip install pigeon-code-compilor`. Zero external deps. Works on any Python codebase. [myaifingerprint.com](https://myaifingerprint.com) · [GitHub](https://github.com/SavageCooPigeonX/pigeon-rename)

---

## vscode-extension/ — VS Code Extension (TypeScript + Python helpers)

The extension is the live nerve center — every keystroke, every AI edit, every chat response flows through it.

### Cross-Correlation Edit Classification (NEW)

Replaced naive 8-char threshold with **physical keystroke ↔ text mutation cross-correlation**. On every `onDidChangeTextDocument`, the extension reads the tail of `os_keystrokes.jsonl` and classifies edits:

| Priority | Classification | Signal |
|---:|---|---|
| 1 | `paste` | Ctrl+V within ±500ms |
| 2 | `undo` | Ctrl+Z within ±500ms |
| 3 | `copilot_tab_accept` | Tab key within ±500ms |
| 4 | `copilot_apply` / `copilot_edit` | Recent AI response + no physical keystroke |
| 5 | `copilot_inline` | Multiline insert, no physical keystroke |
| 6 | `human_edit` | Physical keystroke present |
| 7 | `unknown` | Fallback |

Each classified edit is logged to `logs/copilot_edits.jsonl` with `nearby_os_events` count and `had_physical_keystroke` boolean.

### AI Cognition Timing

All 3 response paths (`_callCopilot`, `_callDeepSeek`, `registerChatParticipant`) now track:
- `queue_latency_ms` — time from request to first token
- `generation_time_ms` — first token to completion
- `total_latency_ms` — end-to-end
- `chunk_count` — streaming chunk count

### Python Helpers

| File | Purpose |
|---|---|
| `pulse_watcher.py` | Watches edit_pairs.jsonl → pairs prompt to file edit → fires `training_pairs_seq027.capture_training_pair()` |
| `classify_bridge.py` | Processes raw keystroke batches → cognitive state classification |

---

## Training Pairs — Intent Alignment Data (NEW)

**Every edit is a training label.** `training_pairs_seq027` captures:

```json
{
  "user_intent": { "raw_prompt", "classified_intent", "cognitive_state", "wpm", "deletion_ratio", "deleted_words", "composition_time_ms" },
  "copilot_intent": { "edit_why", "file", "edit_sources", "had_physical_keystroke", "latency_ms" },
  "alignment": { "rework_score", "rework_verdict", "latency_ms", "had_physical_keystroke" }
}
```

**Per-edit:** Fires via `pulse_watcher.py` after each edit pair is written.
**Per-push:** `generate_cycle_summary()` aggregates all pairs since last push → avg rework, latency, physical keystroke rate, intent/source distributions.

Stress tested: 94 pairs/sec throughput, 20 concurrent threads zero corruption.

---

## Voice Style — Personality Adapter (NEW)

**Zero LLM calls.** `voice_style_seq028` extracts the operator's actual voice from raw prompts using pure regex + counting.

15 features extracted: `avg_prompt_words`, `avg_word_length`, `vocabulary_richness`, `slang_rate`, `contraction_rate`, `technical_density`, `question_rate`, `directive_rate`, `dash_rate`, `ellipsis_rate`, `exclamation_rate`, `no_caps_rate`, `fragment_rate`, `top_words`

Derives actionable style directives (formality, caps, brevity, fragment tolerance, etc.) and injects `<!-- pigeon:voice-style -->` into copilot-instructions.md. Auto-fires on every push.

Current profile (60 prompts): no_caps=100%, fragments=82%, dash_rate=1.08 → 6 directives generated.

---

## Registry & State Files

| File | Purpose | Updated |
|---|---|---|
| `pigeon_registry.json` | Every module: seq, ver, date, desc, intent, token history (188 tracked) | Every commit |
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
| `logs/copilot_edits.jsonl` | AI edit classifications (paste/undo/copilot_tab/copilot_apply/human) with cross-correlation | Every edit |
| `logs/unified_edits.jsonl` | Merged signal from 6 telemetry sources (edit_pairs + copilot_edits + compositions + journal + rework + heat) | Per merge run |
| `logs/training_pairs.jsonl` | Per-edit intent alignment: user_intent vs copilot_intent vs alignment score | Every edit (via pulse_watcher) |
| `logs/training_cycle_summaries.jsonl` | Per-push training aggregates: avg rework, latency, physical keystroke rate, intent distribution | Every commit |
| `logs/voice_style.json` | Extracted operator voice features (15 metrics) + style directives | Every commit |

---

## Compliance Summary

| Package | Files | Compliant | Compliance % |
|---|---:|---:|---:|
| `src/` | 28 | 18 | 64% |
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

