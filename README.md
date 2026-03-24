# keystroke-telemetry

> **Five systems. One closed loop. Zero LLM calls for the core signal. A real-time neural visualizer that watches itself think. Context-accumulating intelligence packets flow through the code graph. And it reads your deleted thoughts before it starts working.**
>
> Keystroke patterns reveal cognitive state → cognitive state steers Copilot's chain-of-thought → AI behavior adapts in real time → rework detection measures if it worked → Pigeon Brain watches the whole thing happen live, lights up the call graph, and tells you where both you and the AI are dying. The Flow Engine routes intelligence packets through the graph — nodes wake up, contribute warnings, and the signal amplifies or decays along import-health edges. Every prompt's deleted words are injected into Copilot's context before it writes a single line.

---

## Status (2026-03-24)

The self-compiling loop is live and chewing through its own codebase. Pigeon Brain is online — 137 neurons mapped, 260 edges, dual-substrate heat flowing, WebSocket trace server broadcasting at 20Hz. The Flow Engine routes context-accumulating intelligence packets through the code graph across 3 modes (targeted/heat/failure). Keystroke deleted word pipeline is live — every prompt's unsaid thoughts are captured before Copilot starts reasoning. Context veins score the import graph health and surface self-trim recommendations.

| Phase | Status |
|---|---|
| Keystroke capture + cognitive state classification | ✅ Live |
| **Deleted word capture (per-prompt)** | **✅ Live — bound to composition, injected into CoT** |
| **Predictive debug from prompt history** | **✅ Live — pattern mining: frustration→module, build→debug cycles** |
| Post-commit telemetry pipeline (12 injected sections) | ✅ Live |
| Pigeon Compiler — DeepSeek cut plan + AST bin-packing | ✅ Live |
| Auto-compile on commit (self_fix triggers `run_clean_split`) | ✅ Live |
| Self-healing exclusion logic (vscode-ext / client / orchestrators) | ✅ Live |
| Codebase auto-refactoring loop (2 files per commit, ~$0.001 each) | ✅ Running |
| **Context veins — import graph health + self-trim** | **✅ Live (137 nodes, 4 clots, 21 arteries)** |
| **Flow Engine — context-accumulating dataflow** | **✅ Live (6 modules, 3 routing modes, multi-perspective merge)** |
| **Pigeon Brain — dual-substrate neural visualizer** | **✅ Live** |
| **Live execution tracing via sys.settrace** | **✅ Live** |
| **WebSocket real-time event broadcast** | **✅ Live** |
| **React graph UI with profiler cards** | **✅ Live** |
| Compiled so far | `compliance_seq008` → 12f, `heal_seq009` → 6f, `manifest_builder_seq007` → 32f, `nametag_seq011` → 9f |
| Remaining over-cap targets | 11 files (~$0.013 total to finish) |
| AI response capture (UIA → rework triple) | 🟨 Planned |

---

## What This Actually Is

This is a system that **reads your mind through your fingers**, **rewires the AI's reasoning in real time**, **refactors its own source code autonomously**, **visualizes the entire thing as a living neural network that lights up when you run code through it**, and **routes context-accumulating intelligence packets through the code graph to surface what matters**.

Five systems working in concert:

1. **Keystroke Telemetry** — captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls — pure signal processing. **Now with per-prompt deleted word binding** — Copilot sees what you deleted before it starts thinking.

2. **Pigeon Code Compiler** — autonomous code decomposition engine. Enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target). Filenames carry living metadata — they mutate on every commit. The codebase refactors itself.

3. **Dynamic Prompt Layer** — task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations, **codebase health veins/clots**, **predictive debug scores**) and generates a context block that steers how Copilot reasons. Self-updates on every commit and every prompt.

4. **Pigeon Brain** — dual-substrate execution observation layer. Maps every module in the codebase as a neuron in a graph (**137 nodes, 260 edges**). Tracks where humans hesitate AND where AI agents die. Overlays both heat maps on the same visualization. Real-time `sys.settrace` instrumentation lights up edges and cards as actual function calls flow through the system. **Context veins** score import graph health and flag dead/bloated modules for self-trimming.

5. **Flow Engine** — context-accumulating dataflow through the code graph. A `ContextPacket` starts at any module and routes through dependencies. At each node, modules "wake up" if relevant and contribute intelligence (risks, warnings, fears). Edges amplify or decay signal based on vein health. Three routing modes — **targeted** (dependency chains), **heat** (dual-score hotspots), **failure** (death signals) — can run independently or merge via multi-perspective synthesis. Zero LLM calls — pure graph traversal + pattern matching.

---

## Pigeon Brain: The Neural Visualizer

**This is the part that makes people stop scrolling.**

Pigeon Brain treats your codebase as a neural network. Every Python module is a neuron. Every import is a synapse. When you run code, electrons (function calls) flow through the graph in real time. When something dies — an exception, a timeout, a stale import, an infinite loop — **the neuron turns red and stays red**.

But here's the part that doesn't exist anywhere else: **it overlays human cognitive heat on the same graph**. The keystroke telemetry system has been profiling which modules make the operator hesitate, delete, abandon, and rework. Pigeon Brain takes that data and combines it with agent execution failures to identify **dual-substrate hotspots** — the modules that are killing both humans and machines simultaneously.

**New (2026-03-24): Context Veins.** The import graph is now scored as a circulatory system. Healthy imports are veins (scored 0–1.0). Dead/bloated modules are clots. The system identifies 4 current clots and 21 critical arteries across 137 nodes. Self-trim recommendations surface automatically in Copilot's context window.

These are the most important decomposition targets in your entire codebase. No static analyzer finds them. No linter flags them. Only the combination of human typing patterns and machine execution traces can surface them.

### Architecture

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

### 19 Python Modules (13 core + 6 flow engine)

| Module | Lines | Role |
|---|---:|---|
| `models_seq001` | ~85 | `ExecutionEvent`, `Electron`, `DeathCause` — isomorphic to keystroke models |
| `execution_logger_seq002` | ~150 | Core agent telemetry logger — stall detection, loop threshold, latency scoring |
| `graph_extractor_seq003` | ~150 | AST + pigeon_registry → adjacency list with 137 nodes and 260 import edges |
| `graph_heat_map_seq004` | ~120 | Failure accumulator per node — danger zones, death rates, cause breakdown |
| `loop_detector_seq005` | ~120 | Recurring path fingerprinting — detects agents stuck in loops |
| `failure_detector_seq006` | ~130 | Death classification — stale_import (0.9), timeout (0.7), loop (0.65), exception (0.75) |
| `observer_synthesis_seq007` | ~160 | Aggregates all execution telemetry → coaching Markdown + dual-substrate hotspot identification |
| `dual_substrate_seq008` | ~200 | **The killer feature** — merges human hesitation + agent death rate into `dual_score` per node |
| `cli_seq009` | ~120 | CLI: `graph`, `observe`, `dual`, `stats`, `simulate`, `live`, `trace` |
| `demo_sim_seq010` | ~180 | Realistic electron simulation with DANGER_PATTERNS for failure-prone modules |
| `trace_hook_seq011` | ~150 | `sys.settrace` instrumentation — maps real Python calls to graph node names at runtime |
| `live_server_seq012` | ~240 | WebSocket server (20Hz broadcast) + HTTP snapshot — accepts injected events from traced_runner |
| `traced_runner_seq013` | ~140 | Wraps any Python script with the trace hook, pushes events to live server |
| **flow/** `context_packet_seq001` | 119 | `ContextPacket` + `NodeIntel` dataclasses — importance decay (0.92), depth cap (15), loop death |
| **flow/** `node_awakener_seq002` | 152 | Relevance gating — keyword overlap, fear match, heat threshold (≥0.5), dependency chain |
| **flow/** `flow_engine_seq003` | 172 | Loads graph_cache + dual_view + context_veins, routes packets via `run_flow()` / `run_multi()` |
| **flow/** `path_selector_seq004` | 197 | 3 routing modes — targeted (dependency, depth 10), heat (dual-score, depth 8), failure (death, depth 6) |
| **flow/** `task_writer_seq005` | 167 | Terminal node — synthesizes accumulated NodeIntel → enriched Markdown. Multi-perspective merge |
| **flow/** `vein_transport_seq006` | 120 | Edge effects — amplify strong veins (1.05×), decay weak (0.93×), dead-vein warnings (<0.15) |

### React UI (7 components)

| Component | Role |
|---|---|
| `PigeonBrain.jsx` | Main graph — ReactFlow with 137 profiler-card nodes, live edge animation, LIVE indicator |
| `NodeNeuron.jsx` | Profiler card per module — name, version, stats grid, heat bars, personality, flash animation on call |
| `useLiveTrace.js` | WebSocket hook — auto-reconnect, TTL-based node/edge activation (800ms/1.2s), 200-event buffer |
| `ObserverPanel.jsx` | Right sidebar — stats, live event feed, dual-substrate hotspots, danger zones, full node profile on click |
| `ElectronLayer.jsx` | Animated dots for flowing electrons |
| `styles.css` | Dark theme — `#0a0a1a` base, neon green/red/blue accents, `cardFlash` + `feedSlide` + `livePulse` animations |
| `vite.config.js` | Vite 5.3.5 + React plugin + dual_view.json middleware |

### Commands

```bash
# Build the cognition graph (137 nodes, 260 edges)
py -m pigeon_brain graph

# Generate dual-substrate view (human heat + agent heat merged)
py -m pigeon_brain dual

# Analyze context veins (import graph health + self-trim)
py -m pigeon_brain.context_veins .

# Run observer synthesis → agent_coaching.md
py -m pigeon_brain observe

# Demo simulation with 20 fake electrons
py -m pigeon_brain simulate --electrons 20

# Start live trace server (WebSocket + HTTP)
py -m pigeon_brain live

# Run any script with real-time tracing (lights up the graph)
py -m pigeon_brain trace test_all.py

# ── Flow Engine ──
py -m pigeon_brain.flow "Fix the hardcoded import in __main__.py"      # Targeted (default) with auto-origin
py -m pigeon_brain.flow --mode targeted --origin cognitive_reactor "analyze reactor drama"  # Explicit origin
py -m pigeon_brain.flow --mode heat "self_fix keeps failing"            # Greedy dual-score hotspots
py -m pigeon_brain.flow --mode failure "import rewriter breaks"         # Death-signal path
py -m pigeon_brain.flow --multi --origin self_fix "why does self_fix keep failing"  # Multi-perspective

# Start the UI
cd pigeon_brain/ui && npm run dev
# → http://localhost:3333
```

### What You See

Each module renders as a **profiler card** — a mini cProfile manifest showing:
- Module name + version
- Token count, line count, call count, death count, loop count
- Human hesitation bar (orange) + dual score bar (severity-colored)
- Personality classification + last-called timestamp

When you run `py -m pigeon_brain trace test_all.py`:
- **Edges glow green** when a function call traverses them (1.2s fade)
- **Cards flash green** when a module is entered (0.8s fade)
- **Live event feed** scrolls in the observer panel — call/return/exception with timestamps
- **LIVE** indicator pulses green in the top-left corner

Click any card to see the full dual-substrate profile: human hesitation score, agent death rate, coupled modules, fears, death causes, import relationships.

---

## Flow Engine: Context-Accumulating Dataflow (`pigeon_brain/flow/`)

**The newest intelligence layer.** Instead of asking "what's wrong with module X?", you ask the *codebase itself* — and it answers by routing a context packet through the graph, letting each module contribute what it knows.

### How It Works

A `ContextPacket` starts at an origin module and flows through the graph:

1. **Origin detection** — `find_origin("self_fix")` maps a keyword to a graph node using tokenized matching (splits on underscores)
2. **Path selection** — three modes pick the next hop:
   - **targeted** — follows dependency chains (depth 10) — "what does this module depend on and what depends on it?"
   - **heat** — greedy follows highest `dual_score` neighbors (depth 8) — "where are the hotspots?"
   - **failure** — follows death signals: exception rate, loop rate, stale imports (depth 6) — "what's dying?"
3. **Node awakening** — at each hop, `node_awakener` checks relevance (keyword overlap, fear match, heat ≥0.5, dependency). Irrelevant nodes are skipped.
4. **Intel contribution** — relevant nodes add `NodeIntel`: risk level (low/medium/high/critical), specific warnings, fears from file consciousness
5. **Edge transport** — `vein_transport` amplifies signal on strong veins (1.05×), decays on weak (0.93×), warns on dead veins (<0.15 health)
6. **Terminal synthesis** — `task_writer` produces enriched Markdown: origin context, routed path, accumulated intel, consensus fears
7. **Multi-perspective** — `--multi` runs all 3 modes from the same origin and merges results, surfacing fears that appear across perspectives

### 6 Modules (927 lines total, 100% pigeon-compliant)

| Module | Lines | Key exports |
|---|---:|---|
| `context_packet_seq001` | 119 | `ContextPacket`, `NodeIntel`, `create_packet()` |
| `node_awakener_seq002` | 152 | `awaken()`, `RELEVANCE_THRESHOLD=0.3` |
| `flow_engine_seq003` | 172 | `load_graph_data()`, `run_flow()`, `run_multi()` |
| `path_selector_seq004` | 197 | `select_next()`, `find_origin()`, 3 mode functions |
| `task_writer_seq005` | 167 | `write_task()`, `write_multi()` |
| `vein_transport_seq006` | 120 | `transport()`, `DEAD_VEIN_HEAT=0.15` |

### Data Sources

The flow engine reads 3 JSON files (all auto-generated by other pigeon_brain modules):
- `graph_cache.json` — topology (137 nodes, 260 edges)
- `dual_view.json` — per-node human + agent heat, fears, personality
- `context_veins.json` — vein/clot health scores, arteries, self-trim targets

### Commands

```bash
# Targeted: follow dependency chain from cognitive_reactor
py -m pigeon_brain.flow --origin cognitive_reactor "analyze reactor dependencies"

# Heat: follow highest dual-score hotspots
py -m pigeon_brain.flow --mode heat "which modules are hottest"

# Failure: follow death signals
py -m pigeon_brain.flow --mode failure "what is dying"

# Multi-perspective: run all 3 modes, merge into one analysis
py -m pigeon_brain.flow --multi --origin self_fix "why does self_fix keep failing"
```

---

## Value Audit — For Devs and Vibecoders of 2026+

*An honest analysis of what this system actually does that nothing else does.*

### What vibecoders are doing wrong right now

"Vibe coding" in 2026 means sending a prompt, accepting the diff, sending another prompt. The human is reduced to **a prompt router** — no way to tell the AI what they're confused about, what they deleted, or why a previous answer failed. The AI models the code, not the person.

This repo is a bet on a different model: **the bottleneck isn't the AI's capability — it's the AI's lack of operator context.**

### What this system uniquely provides

| Capability | Status | Why it matters |
|---|---|---|
| **Unsaid thread capture** | ✅ Live | The deleted half of a prompt is now captured **per-prompt** and injected into CoT before Copilot starts. Only system that reads keystrokes before send. |
| **Per-file cognitive load** | ✅ Live | After 100+ sessions, tells which modules the operator dreads. Technical debt proxy no static analyzer can produce. |
| **CoT steering from live state** | ✅ Live | Copilot's reasoning changes based on flow/frustrated/hesitant — automatically, on every message. |
| **Predictive debug** | ✅ Live | Prompt history mines frustration→module patterns and build→debug cycles to predict next struggles. |
| **Rework → miss rate feedback** | ✅ Live | Heavy deletion after AI response = miss. The AI knows its own failure rate by module. |
| **Self-narrating codebase** | ✅ Live | Each file generates a first-person account of why it was last changed and what could break it. |
| **Self-compiling to pigeon spec** | ✅ Live | 200-line cap enforced autonomously. Every commit triggers DeepSeek decomposition. |
| **Prompt evolution tracking** | ✅ Live | Diff history of how its own AI context prompt has mutated across 48+ commits. |
| **Task queue managed by AI** | ✅ Live | Copilot manages a task backlog seeded from the automated code scanner. |
| **Context veins (codebase health)** | ✅ Live | Import graph scored as veins/clots. Dead modules flagged. Self-trim recommendations. 137 nodes scored. |
| **Flow Engine (context-accumulating dataflow)** | ✅ Live | Intelligence packets route through the code graph. Nodes wake up, contribute risks. 3 modes + multi-perspective merge. Zero LLM calls. |
| **Dual-substrate neural visualization** | ✅ Live | Human cognitive load AND AI execution failures on the same graph. 137 neurons profiled. |
| **Real-time execution tracing** | ✅ Live | `sys.settrace` + WebSocket at 20Hz. Watch your call graph light up as code runs. |
| **Module profiler cards** | ✅ Live | cProfile-style cards: tokens, lines, calls, deaths, loops, hesitation bars, personality, fears. |

### The honest gaps

| Gap | Impact | Mitigation |
|---|---|---|
| **No response text captured** | Can't correlate *what was said* with *why it failed*. | UIA reader stub exists. Needs accessibility tree walking. |
| **Classification noise at session start** | First few prompts unreliable. | Self-calibrating baselines in v008. |
| **Windows-only core** | UIA, OS hook, VS Code extension path assumptions. | Acknowledged. Not a priority. |
| **DeepSeek dependency for coaching** | Remove the key and coaching goes silent; rest still works. | Graceful degradation. |

---

## The Closed Loop

```
 Keystrokes (VS Code Extension)
      │
      ▼
 classify_bridge.py
      │  WPM, deletion%, hesitation, pause patterns
      ▼
 OperatorStats → operator_profile.md
      │  45+ history entries, state distribution, time-of-day patterns
      ▼
 ─────────────────── POST-COMMIT PIPELINE ──────────────────
 git commit
   1. rename files + bump versions       (pigeon naming convention)
   2. rewrite all imports                (auto-heals after renames)
   3. rebuild MANIFEST.md files          (17 folders)
   4. prompt_recon_seq016                → prompt_compositions.jsonl
                                         → copilot_prompt_mutations.json
   5. self_fix_seq013                    → docs/self_fix/{hash}.md
   6. push_narrative_seq012              → docs/push_narratives/{hash}.md
   7. DeepSeek API call                  → operator_coaching.md
   8. dynamic_prompt_seq017              → .github/copilot-instructions.md
      └─ inject_task_context()
   9. task_queue_seq018                  → task_queue.json
  10. auto-commit [pigeon-auto]
 ────────────────────────────────────────────────────────────
      │
      ▼
 Copilot reads injected context → AI response
      │
      ▼
 rework_detector_seq009 (heavy deletion = miss)
      │
      ▼
 rework_log.json → feeds into next injection
      │
      ▼                              ┌──────────────────────────┐
 ─── PIGEON BRAIN (LIVE) ──         │  React UI (localhost:3333) │
      │                              │  profiler cards + edges   │
 graph_extractor ←─ registry         │  live event feed          │
      │                              │  observer panel           │
 trace_hook (sys.settrace)           └──────────┬───────────────┘
      │                                         │
 live_server (ws://8765) ──── WebSocket ────────┘
      │                           20 pushes/sec
 dual_substrate                  edges glow, cards flash
      │
 file_heat_map + graph_heat_map
 (human heat)    (agent heat)
      │
      ▼
 dual_view.json (137 neurons, dual_score per node)
                                        │
                              ┌── Flow Engine ──┐
                              │ 3 routing modes  │ → enriched Markdown tasks
                              │ nodes awaken     │   (per-module intel, fears,
                              │ veins transport  │    consensus, recommendations)
                              └──────────────────┘
```

---

## System 1: Keystroke Telemetry

### VS Code Extension (`vscode-extension/`)

TypeScript extension that captures every keystroke in the Copilot chat input:
- Timestamps at millisecond resolution
- Pause durations between keystrokes
- Deletion sequences
- Message submit vs. abandon events
- Active file context

Flushes to `classify_bridge.py` at configurable intervals. Running live — 110+ session flushes logged.

### Cognitive State Classification

Five states derived from raw keystroke metrics:

| State | Signal Pattern | CoT Directive |
|---|---|---|
| `flow` | high WPM, low deletion, low hesitation | "Match their speed. Assume expertise. Go deeper than asked." |
| `frustrated` | moderate WPM, high deletion, mid hesitation | "Lead with the fix. Skip explanations unless asked." |
| `hesitant` | low WPM, moderate deletion, high hesitation | "Offer 2 interpretations. End with a clarifying question." |
| `restructuring` | variable WPM, high deletion, high hesitation | "Use numbered steps. Match the effort in their prompt." |
| `abandoned` | incomplete message, no submit | "Be direct and welcoming. They may be re-approaching." |

### Unsaid Thread Detection (`query_memory_seq010`)

When an operator types a query, deletes part of it, and sends a different version — the deleted fragment is captured. These "unsaid threads" accumulate in `logs/prompt_compositions.jsonl` and are injected into every Copilot session:

```
### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- "by pigeon unless approv"
- "uld really be purged"
- "they all sho"
```

Copilot can now reason about what the operator *almost* asked.

### Rework Detection (`rework_detector_seq009`)

After an AI response, the system monitors the next 30 seconds of typing. If the operator deletes heavily and rewrites, the response is marked `miss`. Miss rate per module accumulates in `rework_log.json` and surfaces in the injected context so Copilot knows which of its previous answers failed.

### File Heat Map (`file_heat_map_seq011`)

Every flush records which file the operator has open alongside their cognitive metrics. Over time, a per-module profile builds up showing which files cause the most hesitation and which have the highest AI miss rate. Hot zones are surfaced in every Copilot session:

```
### Module Hot Zones
- `context_budget` (hes=0.778)
- `push_narrative` (hes=0.778)
- `import_rewriter` (hes=0.735)
```

---

## System 2: Pigeon Code Compiler (`pigeon_compiler/`)

### The Problem It Solves

LLMs degrade on long files. A 600-line module gives the model too much context noise to reason precisely about a 10-line function. The Pigeon Compiler enforces a hard 200-line cap and 50-line target on every Python file in the project.

### How It Works

1. **State extraction** (`state_extractor/`) — AST parsing, call graph construction, shared state detection, import tracing. Produces an "ether map" (JSON) describing the full structure of a file.

2. **Weakness planning** (`weakness_planner/`) — sends the ether map to DeepSeek with a structured prompt. DeepSeek returns a cut plan: which functions belong together, what to name the new files, how to handle shared state.

3. **Cut execution** (`cut_executor/`) — implements the cut plan: slices source, writes new pigeon-compliant files, generates `__init__.py`, rewrites imports across the codebase.

4. **Rename engine** (`rename_engine/`) — after every commit, renames files to encode living metadata:

```
{name}_seq{NNN}_v{NNN}_d{MMDD}__{description}_lc_{intent}.py
```

Example: `dynamic_prompt_seq017_v003_d0317__steers_copilot_cot_from_live_lc_wire_narratives_self.py`

- `seq017` — load order, never changes
- `v003` — bumped on every commit that touches this file
- `d0317` — date of last mutation
- `steers_copilot_cot_from_live` — what it does (from docstring, auto-extracted)
- `wire_narratives_self` — last commit intent slug

**Never hardcode these names.** They mutate. Use `file_search("dynamic_prompt_seq017*")`.

### Self-Healing

The rename engine rewrites all `import` and `from` statements across the codebase after every rename. No broken imports after a version bump.

The `self_fix_seq013` module scans the codebase on every commit for:
- Hardcoded pigeon filenames (CRITICAL — break on next rename)
- Dead exports (functions defined but never called)
- Query noise pollution (background events in query_memory)
- High-coupling modules (6+ dependents — high blast radius for changes)

Results written to `docs/self_fix/{date}_{hash}_self_fix.md` and injected into the Copilot context:

```
### Known Issues
- [CRITICAL] hardcoded_import in `stress_test.py`
- [CRITICAL] hardcoded_import in `test_all.py`
- [HIGH] query_noise
```

### Push Narratives (`push_narrative_seq012`)

On every commit, each changed Python file is fed its own identity (name, version history, token weight, description history, last commit intent) plus live operator signals (rework miss rate, hesitation scores, abandoned queries). A single DeepSeek call generates a first-person narrative for each file:

> *"I was touched to implement a new steering mechanism that uses live context from the operator's active file. I assume `git_plugin` can reliably provide a clean diff — if it returns an empty string, the prompt will generate nonsensical context."*

These narratives accumulate in `docs/push_narratives/`. They surface **fragile contracts and regression watchlists** that get injected into the next Copilot session:

```
### Fragile Contracts
- push_narrative assumes `prompt_recon_attempts` telemetry key
- git_plugin's string type assumption for mutated prompts
- prompt_recon_seq016's fragile string parsing of code blocks
```

---

## System 3: Dynamic Prompt Layer (`src/dynamic_prompt_seq017*`)

### What It Injects

On every commit, `inject_task_context()` rewrites the `<!-- pigeon:task-context -->` block in `.github/copilot-instructions.md`. Copilot reads this file before processing every message.

The block contains 11 live sections:

```markdown
## Live Task Context

*Auto-injected 2026-03-17 05:43 UTC · 62 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `frustrated` (WPM: 102.8 | Del: 28.7% | Hes: 0.659)

> **CoT directive:** Operator is frustrated. Think step-by-step but keep output
> SHORT. Lead with the fix. Skip explanations unless asked.

### Unsaid Threads
- "by pigeon unless approv"
- "uld really be purged"

### Module Hot Zones
- `context_budget` (hes=0.778)
- `push_narrative` (hes=0.778)

### AI Rework Surface
*Miss rate: 100.0% (1 responses)*
- Failed on: ""

### Recent Work
- `f989307` feat: wire narratives + self-fix + coaching + gaps
- `1f60b21` feat: dynamic task-context CoT injection

### Coaching Directives
- **Anticipate Context Shifts**
- **Pre-Empt Refactoring Pain**
- **Counteract Abandonment**

### Fragile Contracts
- push_narrative assumes `prompt_recon_attempts` telemetry key
- git_plugin string type assumption for mutated prompts

### Known Issues
- [CRITICAL] hardcoded_import in `stress_test.py`
- [HIGH] query_noise

### Persistent Gaps
- [3x] call deepseek scope verify

### Prompt Evolution
*This prompt has mutated 24x (186→434 lines). Features added: auto_index,
operator_state, prompt_journal, pulse_blocks, prompt_recon.*
```

### The Second Block: Operator State

A parallel block `<!-- pigeon:operator-state -->` is regenerated by a separate DeepSeek call that synthesizes all 45+ history entries into behavioral instructions:

```markdown
**Dominant: `frustrated`** | Submit: 15% | WPM: 153.5 | Del: 33.3% | Hes: 0.783

- **Pre-Empt Refactoring Pain:** Before suggesting edits to `push_narrative`,
  `context_budget_scorer`, first summarize their apparent purpose.
- **Counteract Abandonment:** Provide the *next minimal, verifiable step*,
  not the whole solution, to maintain momentum.
```

### Data Sources Read

| Source | What it provides |
|---|---|
| `operator_profile.md` (DATA block) | Last 5 cognitive state readings |
| `logs/prompt_journal.jsonl` | Enriched entry per prompt (cross-refs all below) |
| `logs/prompt_compositions.jsonl` | Deleted words (unsaid threads) |
| `file_heat_map.json` | Per-module hesitation + miss counts |
| `rework_log.json` | AI miss rate + worst queries |
| `query_memory.json` | Recurring queries (bg-noise filtered) |
| `docs/push_narratives/*.md` | Fragile contracts + regression watchlists |
| `docs/self_fix/*.md` | CRITICAL/HIGH problems with file names |
| `operator_coaching.md` | DeepSeek-synthesized behavioral rules |
| `logs/copilot_prompt_mutations.json` | Prompt evolution trajectory |
| `git log` | Task focus inference from recent commits |

### Task Queue (`src/task_queue_seq018*`)

Copilot manages a live task queue injected as `<!-- pigeon:task-queue -->` in `copilot-instructions.md`. Every task has:
- A stage (`debugging`, `implementing`, `planning`, `refactor`)
- Focus files (which pigeon modules or source files to touch)
- A `manifest_ref` — the MANIFEST.md file to update when marking done

To complete a task:
1. Do the work
2. Update the referenced `MANIFEST.md` entry
3. Call `mark_done(root, task_id)` in `task_queue_seq018`

Tasks auto-seed from `self_fix` reports (CRITICAL issues become pending queue items). The post-commit pipeline re-injects the queue on every commit so Copilot always sees the current state.

```markdown
### Active Task Queue
- [ ] `tq-001` **Fix hardcoded pigeon import in `test_all.py`** | stage: debugging
  → [MASTER_MANIFEST.md](MASTER_MANIFEST.md)
- [ ] `tq-003` **Implement AI response capture via UIA** | stage: implementing
  → [src/MANIFEST.md](src/MANIFEST.md)
- [ ] `tq-006` **Wire response capture into rework_log** | stage: planning
  → [src/MANIFEST.md](src/MANIFEST.md)
```

---

## Planned: AI Response Capture (`logs/ai_responses.jsonl`)

The one missing sensor in the closed loop: **Copilot's actual response text is never captured**. The rework detector knows a response failed (heavy deletion after) but has no record of what was said.

Planned implementation via UIA (Windows UI Automation — already used in `client/os_hook.py`):
- After each message submit, walk the Copilot chat panel's accessibility tree
- Read the last assistant response text via `IUIAutomationTextPattern` or `ValuePattern`
- Hash + store alongside the prompt journal entry and subsequent rework score

This gives `(prompt_snapshot → response_hash → rework_score)` triples that enable:
- **Narrative grounding** — push narratives can reference what Copilot actually said, not just that it failed
- **Prompt mutation scoring** — correlate which injected sections reduced miss rate over time
- **Dead section pruning** — sections with no empirical correlation to rework reduction get flagged for removal from `copilot-instructions.md`

The self-upgrade loop then closes: inject → measure response → measure rework → score injected sections → rewrite prompt.

---

## Prompt Reconstruction (`src/prompt_recon_seq016*`)

The VS Code extension captures OS-level keystrokes (via UIA/OS hook) and the extension's own keystroke events. `prompt_recon_seq016` reconstructs full prompts from these two streams, including content that was typed and deleted before sending.

Additionally, it tracks how `copilot-instructions.md` itself has evolved across every commit. Current state: **24 mutations, 186 → 434 lines**. Features added per mutation are tracked: `auto_index`, `operator_state`, `prompt_journal`, `pulse_blocks`, `prompt_recon`.

---

## Pulse Harvest (`src/pulse_harvest_seq015*`)

Every `src/*.py` file contains a pulse block:

```python
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-17T05:40:00Z
# EDIT_HASH: auto
# EDIT_WHY:  wire narratives self-fix coaching gaps
# ── /pulse ──
```

When Copilot edits a file, it updates this block. When the file is saved, the VS Code extension harvests the block — pairing the edit timestamp with the prompt journal entry that triggered it. This gives sub-second timing data on prompt → file edit latency.

---

## Enriched Prompt Journal (`src/prompt_journal_seq019*`)

Every Copilot message triggers a journal entry that cross-references all live telemetry sources into a single JSON line. This is the unified telemetry layer — one file you can grep, stream, or analyze to reconstruct any session.

Each entry captures:

| Field | Source |
|---|---|
| `ts`, `session_n`, `msg`, `msg_len` | Direct from the prompt |
| `intent` | Classified: `debugging`, `building`, `restructuring`, `testing`, `exploring`, `shipping`, `documenting`, `continuing` |
| `module_refs` | Module names mentioned in the prompt |
| `cognitive_state` | From `chat_compositions.jsonl` (latest keystroke classification) |
| `signals.wpm`, `signals.deletion_ratio`, `signals.hesitation_count` | Raw telemetry from composition |
| `deleted_words`, `rewrites` | What the operator typed then deleted before sending |
| `task_queue` | Current pending/in-progress tasks from `task_queue.json` |
| `hot_modules` | Top 5 highest-hesitation modules from `file_heat_map.json` |
| `prompt_mutations` | Count of `copilot-instructions.md` mutations |
| `running_stats` | Cumulative: total messages, avg WPM, avg deletion ratio |

Output: `logs/prompt_journal.jsonl` — one JSON object per line, append-only.

```json
{
  "ts": "2026-03-18T02:15:00Z",
  "session_n": 49,
  "msg": "continue",
  "intent": "continuing",
  "cognitive_state": "frustrated",
  "signals": {"wpm": 398.6, "deletion_ratio": 39.5, "hesitation_count": 3},
  "deleted_words": [{"word": "yes but most impor"}],
  "task_queue": {"pending": 10, "in_progress": 0, "done": 5},
  "hot_modules": [{"module": "context_budget", "hes": 0.92}],
  "prompt_mutations": 26,
  "running_stats": {"total_messages": 49, "avg_wpm": 153.5, "avg_deletion_ratio": 33.3}
}
```

---

## Project Structure

```
keystroke-telemetry/
├── .github/
│   └── copilot-instructions.md           ← auto-updated on every commit (608 lines, 44 mutations)
├── src/                                  ← core telemetry (23 modules)
│   ├── timestamp_utils_seq001*           ← epoch ms utility
│   ├── models_seq002*                    ← KeyEvent, MessageDraft dataclasses
│   ├── logger_seq003*                    ← core telemetry logger
│   ├── context_budget_seq004*            ← token cost scorer
│   ├── drift_watcher_seq005*             ← cross-session drift detection
│   ├── resistance_bridge_seq006*         ← telemetry → compiler signal
│   ├── streaming_layer_seq007*           ← MONOLITH (test harness only, intentional)
│   ├── operator_stats_seq008*            ← persistent cognitive profile
│   ├── rework_detector_seq009*           ← AI answer quality measurement
│   ├── query_memory_seq010*              ← recurring query + unsaid detector
│   ├── file_heat_map_seq011*             ← per-module cognitive load
│   ├── push_narrative_seq012*            ← per-push file self-narratives
│   ├── self_fix_seq013*                  ← cross-file problem scanner + auto-compile trigger
│   ├── cognitive_reactor_seq014*         ← autonomous code modification
│   ├── pulse_harvest_seq015*             ← prompt → edit pairing
│   ├── prompt_recon_seq016*              ← prompt reconstruction + mutation tracking
│   ├── dynamic_prompt_seq017*            ← task-aware CoT injection ←── THE CORE
│   ├── task_queue_seq018*                ← Copilot-managed task queue
│   ├── prompt_journal_seq019*            ← enriched prompt journal (cross-ref all telemetry)
│   ├── copilot_prompt_manager_seq020*    ← prompt block auditing
│   ├── mutation_scorer_seq021*           ← correlates prompt mutations to rework
│   ├── rework_backfill_seq022*           ← reconstructs historical rework scores
│   ├── session_handoff_seq023*           ← session summary generator
│   └── cognitive/
│       ├── adapter_seq001*               ← state → behavior adapter
│       ├── unsaid_seq002*                ← detects unsaid thoughts
│       └── drift_seq003*                 ← typing pattern drift
├── pigeon_brain/                         ← THE NEURAL VISUALIZER (19 modules + React UI)
│   ├── models_seq001*                    ← ExecutionEvent, Electron, DeathCause
│   ├── execution_logger_seq002*          ← agent telemetry logger — stalls, loops, latency
│   ├── graph_extractor_seq003*           ← registry → 137-node adjacency graph
│   ├── graph_heat_map_seq004*            ← failure accumulation per neuron
│   ├── loop_detector_seq005*             ← recurring path fingerprinting
│   ├── failure_detector_seq006*          ← death classification (stale, timeout, loop, exception)
│   ├── observer_synthesis_seq007*        ← coaching markdown + hotspot identification
│   ├── dual_substrate_seq008*            ← HUMAN HEAT + AGENT HEAT → dual_score ←── THE KILLER
│   ├── cli_seq009*                       ← 7 subcommands: graph, observe, dual, stats, simulate, live, trace
│   ├── demo_sim_seq010*                  ← fake electron simulation with DANGER_PATTERNS
│   ├── trace_hook_seq011*                ← sys.settrace → graph node mapping at runtime
│   ├── live_server_seq012*               ← WebSocket (ws://8765) + HTTP, 20Hz broadcast
│   ├── traced_runner_seq013*             ← wrap any script with trace + push to live server
│   ├── context_veins.py                  ← import graph health → veins/clots scoring
│   ├── flow/                             ← CONTEXT-ACCUMULATING DATAFLOW ENGINE (6 modules)
│   │   ├── context_packet_seq001*        ← ContextPacket + NodeIntel dataclasses
│   │   ├── node_awakener_seq002*         ← relevance gating (keyword, fear, heat, dependency)
│   │   ├── flow_engine_seq003*           ← loads 3 data sources, routes packets
│   │   ├── path_selector_seq004*         ← 3 modes: targeted, heat, failure
│   │   ├── task_writer_seq005*           ← terminal node → enriched Markdown tasks
│   │   └── vein_transport_seq006*        ← edge effects: amplify/decay/dead-vein warnings
│   ├── dual_view.json                    ← 137 enriched neurons (human + agent heat merged)
│   ├── graph_cache.json                  ← graph topology cache
│   └── ui/                               ← React + @xyflow/react
│       ├── src/
│       │   ├── PigeonBrain.jsx           ← main graph — 125 profiler cards, live edges, LIVE indicator
│       │   ├── NodeNeuron.jsx            ← profiler card — stats grid, heat bars, personality, flash
│       │   ├── ObserverPanel.jsx         ← sidebar — live event feed, dual-substrate hotspots
│       │   ├── ElectronLayer.jsx         ← animated electron dots
│       │   ├── useLiveTrace.js           ← WebSocket hook — auto-reconnect, TTL activation
│       │   ├── styles.css                ← dark theme, neon accents, cardFlash/feedSlide/livePulse
│       │   └── main.jsx                  ← entry point
│       ├── vite.config.js                ← Vite 5.3.5 + dual_view.json middleware
│       └── package.json                  ← react 18.3.1, @xyflow/react 12.0.0
├── streaming_layer/                      ← compiled package (19 files, 100% compliant)
├── pigeon_compiler/                      ← the compiler (~62 modules)
│   ├── git_plugin.py                     ← post-commit orchestrator (1038 lines)
│   ├── pigeon_limits.py                  ← compliance thresholds + exclusion logic
│   ├── rename_engine/                    ← file renames + import rewriting
│   │   ├── compliance_seq008/            ← compiled package (12 files) ✅
│   │   ├── heal_seq009/                  ← compiled package (6 files) ✅
│   │   ├── manifest_builder_seq007/      ← compiled package (32 files) ✅
│   │   └── nametag_seq011/               ← compiled package (9 files) ✅
│   ├── cut_executor/                     ← file slicing + bin-packing
│   ├── state_extractor/                  ← AST + call graph analysis
│   ├── weakness_planner/                 ← DeepSeek cut plan generation
│   └── runners/                          ← pipeline entry points
├── vscode-extension/                     ← TypeScript keystroke capture
├── client/                               ← OS-level hooks + UIA readers
├── docs/
│   ├── push_narratives/                  ← per-commit module self-narratives
│   └── self_fix/                         ← automated problem detection reports
├── logs/
│   ├── prompt_journal.jsonl              ← enriched journal (cross-refs all telemetry per prompt)
│   ├── chat_compositions.jsonl           ← keystroke compositions + deleted words + cognitive state
│   ├── copilot_prompt_mutations.json     ← prompt file evolution snapshots
│   └── ai_responses.jsonl                ← (planned) Copilot response text + rework triples
├── operator_profile.md                   ← living cognitive profile
├── operator_coaching.md                  ← DeepSeek behavioral synthesis
├── file_heat_map.json                    ← per-module cognitive load data
├── rework_log.json                       ← AI response quality log
├── query_memory.json                     ← recurring query fingerprints
├── task_queue.json                       ← Copilot-managed task queue (auto-seeded from self-fix)
├── pigeon_registry.json                  ← all module versions + token history (152 modules)
├── MASTER_MANIFEST.md                    ← full project reference
├── CHANGELOG.md                          ← patch notes
└── test_all.py                           ← 5 core tests (always run before commit)
```

---

## Tests

```bash
$env:PYTHONIOENCODING = "utf-8"
py test_all.py
```

| Test | Covers |
|---|---|
| TEST 1 | `TelemetryLogger` — v2 schema, 3 turns, submit + discard |
| TEST 2 | `Context Budget Scorer` — hard cap, budget, coupling |
| TEST 3 | `DriftWatcher` — baseline + versioned filename drift |
| TEST 4 | `Resistance Bridge` — telemetry → compiler signal |
| TEST 5 | `Edit Pairs` — pulse harvest prompt → file edit pairing |

All 5 must pass before every commit.

---

## Setup

```bash
# Clone
git clone https://github.com/SavageCooPigeonX/keystroke-telemetry
cd keystroke-telemetry

# Install Python dependencies
pip install -e .

# DeepSeek API key (for post-commit narratives + coaching)
$env:DEEPSEEK_API_KEY = "your-key-here"

# Install VS Code extension
cd vscode-extension
npm install
# Press F5 in VS Code to launch Extension Development Host

# ── Pigeon Brain ──
pip install websockets                    # for live trace server
py -m pigeon_brain graph                  # build cognition graph (137 nodes, 260 edges)
py -m pigeon_brain dual                   # generate dual-substrate view
cd pigeon_brain/ui && npm install         # install React UI deps
npm run dev                               # → http://localhost:3333
# In another terminal:
py -m pigeon_brain live                   # start WebSocket trace server (ws://8765)
py -m pigeon_brain trace test_all.py      # run tests with live tracing — watch the graph light up

# Run tests
py test_all.py
```

### Post-commit hook (already installed if you cloned)

```sh
#!/bin/sh
py -m pigeon_compiler.git_plugin
```

Located at `.git/hooks/post-commit`. Runs the full pipeline on every commit.

---

## Key Conventions

**Never hardcode pigeon filenames.** They mutate on every commit. Always use glob patterns:
```python
# WRONG
from src.logger_seq003_v003_d0317__core_keystroke_telemetry import TelemetryLogger

# RIGHT
import glob, importlib
[f] = glob.glob('src/logger_seq003*.py')
mod = importlib.import_module(f.replace('/', '.').rstrip('.py'))
```

**Python on Windows:** use `py` not `python`. Always set `$env:PYTHONIOENCODING = "utf-8"`.

**File size budget:** ≤200 lines hard cap. ≤50 lines target. If you add a file that goes over, pigeon will flag it and the next compile run will split it.

---

## Current Status (2026-03-24)

| Component | Status |
|---|---|
| VS Code extension keystroke capture | ✅ Live (110+ session flushes) |
| Cognitive state classification | ✅ Live (5 states, 45+ profile entries) |
| Operator stats accumulation | ✅ Fixed (DATA block regex) |
| **Deleted word capture (per-prompt)** | **✅ Live — bound per-prompt, injected into CoT** |
| **Predictive debug** | **✅ Live — frustration→module + build→debug cycle mining** |
| Unsaid thread detection | ✅ Live |
| File heat map per-module | ✅ Live |
| Rework detection | ✅ Live |
| Push narratives | ✅ Live (8 narratives) |
| Self-fix scanner | ✅ Live (20 problems detected last scan) |
| Prompt reconstruction | ✅ Live (48 mutations tracked) |
| Dynamic CoT injection | ✅ Live (12 sections, all data sources wired) |
| Task queue | ✅ Live (auto-seeded, manifest-linked, Copilot-managed) |
| Post-commit pipeline | ✅ Fully wired (10-step auto-commit) |
| Pigeon compiler | ✅ Operational |
| **Context veins (codebase health)** | **✅ Live (137 nodes, 4 clots, 21 arteries)** |
| **Flow Engine — context-accumulating dataflow** | **✅ Live (6 modules, 3 modes, multi-perspective)** |
| **Pigeon Brain — neural visualizer** | **✅ Live (137 neurons, 260 synapses)** |
| **Dual-substrate heat mapping** | **✅ Live (human + agent heat merged per node)** |
| **Live execution tracing** | **✅ Live (sys.settrace → WebSocket @ 20Hz)** |
| **React graph UI** | **✅ Live (profiler cards, edge animation, observer panel)** |
| MASTER_MANIFEST | ✅ Rebuilt |
| Tests | ✅ 5/5 passing |

**Known open issues (tracked in `task_queue.json`):**
- `stress_test.py`, `test_all.py` have hardcoded pigeon imports — `tq-001`, `tq-002`
- AI response capture not yet implemented — `tq-003`, `tq-006`
- 76 `(background)` queries polluting `query_memory.json` — `tq-007`
- `operator_stats_seq008*` (397 lines) and `self_fix_seq013*` (352 lines) need pigeon compile — `tq-004`, `tq-005`

---

## License

MIT. See `LICENSE`.
