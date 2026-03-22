# keystroke-telemetry

> **Three systems. One closed loop. Zero LLM calls for the core signal.**
>
> Keystroke patterns reveal cognitive state → cognitive state steers Copilot's chain-of-thought → AI behavior adapts in real time → rework detection measures if it worked → feeds back in.

---

## Status (2026-03-22)

The self-compiling loop is live and chewing through its own codebase.

| Phase | Status |
|---|---|
| Keystroke capture + cognitive state classification | ✅ Live |
| Post-commit telemetry pipeline (11 injected sections) | ✅ Live |
| Pigeon Compiler — DeepSeek cut plan + AST bin-packing | ✅ Live |
| Auto-compile on commit (self_fix triggers `run_clean_split`) | ✅ Live |
| Self-healing exclusion logic (vscode-ext / client / orchestrators) | ✅ Live |
| Codebase auto-refactoring loop (2 files per commit, ~$0.001 each) | ✅ Running |
| Compiled so far | `compliance_seq008` → 12f, `heal_seq009` → 6f, `manifest_builder_seq007` → 32f, `nametag_seq011` → 9f |
| Remaining over-cap targets | 11 files (~$0.013 total to finish) |
| AI response capture (UIA → rework triple) | 🔲 Planned |

---

## Value Audit — For Devs and Vibecoders of 2026+

*An honest analysis of what this system actually does that nothing else does, and where it will matter most.*

### What vibecoders are doing wrong right now

"Vibe coding" in 2026 means sending a prompt, accepting the diff, sending another prompt. The human is reduced to **a prompt router** — they have no way to tell the AI what they're actually confused about, what they deleted from their last message, or why a previous answer failed. The AI models the code, not the person.

This repo is a bet on a different model: **the bottleneck isn't the AI's capability — it's the AI's lack of operator context.** Every piece of ambiguity that a human resolves silently (hesitation, deletion, rewrite, abandon) is a signal that gets lost in the current human-AI interface.

### What this system uniquely provides

| Capability | Status | Why it matters |
|---|---|---|
| **Unsaid thread capture** | ✅ Live | Prompts contain only what the operator committed to — the deleted half is usually the most revealing. This is the only system that reads deleted keystrokes before send. |
| **Per-file cognitive load** | ✅ Live | After 100+ sessions, you can tell which modules the operator dreads. That's a proxy for technical debt no static analyzer can produce. |
| **CoT steering from live state** | ✅ Live | Copilot's reasoning changes based on whether you're in flow, frustrated, or hesitant. Not with a settings toggle — automatically, on every message. |
| **Rework → miss rate feedback** | ✅ Live | Every AI response that triggers heavy deletion after is marked as a miss. The AI knows its own failure rate by module. |
| **Self-narrating codebase** | ✅ Live | Each file generates a first-person account of why it was last changed, what it assumes, and what could break it. This is ambient documentation that gets more useful as the codebase ages. |
| **Self-compiling to pigeon spec** | ✅ Live | The codebase enforces its own 200-line cap autonomously. Every commit automatically triggers DeepSeek to decompose oversized files. The codebase refactors itself. |
| **Prompt evolution tracking** | ✅ Live | The system has a diff history of how its own AI context prompt has mutated across 30+ commits. You can see which features improved the AI response quality and which were noise. |
| **Task queue managed by AI** | ✅ Live | Copilot manages a task backlog seeded from the automated code scanner. Tasks auto-close when the referenced MANIFEST.md is updated. |

### The honest gaps

| Gap | Impact | Mitigation in progress |
|---|---|---|
| **No response text captured** | Rework is measured but you can't correlate *what was said* with *why it failed*. Miss rate is approximate. | UIA reader stub exists (`client/uia_reader.py`). Needs the Copilot panel accessibility tree walked. |
| **Classification noise at session start** | First few prompts of a session produce unreliable state (baseline not calibrated). History accumulates quickly. | Self-calibrating baselines introduced in v008. |
| **Windows-only core** | UIA, OS hook, VS Code extension path assumptions. Most of the telemetry capture is Windows-native. Cross-platform would require a different input hook. | Acknowledged. Not a priority. |
| **DeepSeek dependency for coaching** | Operator coaching and push narratives require an API key. Remove the key and the coaching loop goes silent; the rest still works. | Graceful degradation: all non-DeepSeek sections still inject. |
| **Pigeon filenames in tests** | Tests that hardcode versioned filenames break on the next rename. Self-fix scanner flags these as CRITICAL. | `test_all.py` uses dynamic glob search — pattern to follow. |

### Who this is useful for, ranked

1. **Solo devs with long-running projects** — the cognitive load map becomes extremely accurate after 50+ sessions. You surface which parts of your own codebase you avoid, and the AI gets briefed on exactly that.

2. **Vibecoders building production systems** — rework measurement gives you an empirical signal that your prompts are degrading in quality. Most vibe coders have no idea when they've entered a session where the AI is consistently wrong.

3. **Teams that want structured AI context** — the pigeon naming convention and auto-generated MANIFESTs produce a self-describing codebase. New contributors (human or AI) can orient in under 5 minutes.

4. **Anyone building an AI-heavy tool who wants to close the feedback loop** — the architecture here (capture → classify → inject → measure → adapt) is a pattern worth copying even if you don't use this exact stack.

### What this is *not*

- Not a linting tool. Use ruff.
- Not a documentation generator. The MANIFESTs are navigation aids, not API docs.
- Not a test framework. The 4 core tests are sanity checks for the telemetry pipeline, not test coverage.
- Not an LLM wrapper or prompt library. Zero LLM calls in the core signal path.

---



1. **Reads human cognition through typing patterns** — pauses, deletions, rewrites, and abandoned drafts are not noise. They are the highest-bandwidth signal channel between a human and a machine. This system reads them.

2. **Enforces LLM-readable code structure** — the Pigeon Compiler decomposes files above 200 lines into smaller, named, self-documenting modules. File names carry living metadata and mutate on every commit.

3. **Injects operator state directly into Copilot's chain-of-thought** — every commit triggers a pipeline that reads all live signals and rewrites `.github/copilot-instructions.md` with a task-context block. The AI reads this before reasoning about your prompt.

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
           reads: operator_profile, prompt_compositions, file_heat_map,
                  rework_log, query_memory, push_narratives, self_fix,
                  operator_coaching, copilot_mutations, git log
   9. task_queue_seq018                  → task_queue.json
      └─ inject_task_queue()
           auto-seeds from self_fix reports
           marks done when MANIFEST.md is updated
  10. auto-commit [pigeon-auto]
 ────────────────────────────────────────────────────────────
      │
      ▼
 Copilot reads injected context on next message
      │  task focus, CoT directive, unsaid threads, hot zones,
      │  coaching directives, fragile contracts, known issues
      ▼
 AI response generated with operator-aware reasoning
      │
      ▼
 rework_detector_seq009
      │  measures post-response typing: heavy deletion = miss
      ▼
 rework_log.json → feeds into next injection
      │
      ▼
 logs/ai_responses.jsonl  (planned)
      │  UIA capture of Copilot panel response text
      │  (prompt → response → rework_score) triples
      ▼
 narrative analysis + prompt mutation scoring
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
│   └── copilot-instructions.md      ← auto-updated on every commit
├── src/                             ← core telemetry (23 modules)
│   ├── timestamp_utils_seq001*      ← epoch ms utility
│   ├── models_seq002*               ← KeyEvent, MessageDraft dataclasses
│   ├── logger_seq003*               ← core telemetry logger
│   ├── context_budget_seq004*       ← token cost scorer
│   ├── drift_watcher_seq005*        ← cross-session drift detection
│   ├── resistance_bridge_seq006*    ← telemetry → compiler signal
│   ├── streaming_layer_seq007*      ← MONOLITH (test harness only, intentional)
│   ├── operator_stats_seq008*       ← persistent cognitive profile
│   ├── rework_detector_seq009*      ← AI answer quality measurement
│   ├── query_memory_seq010*         ← recurring query + unsaid detector
│   ├── file_heat_map_seq011*        ← per-module cognitive load
│   ├── push_narrative_seq012*       ← per-push file self-narratives
│   ├── self_fix_seq013*             ← cross-file problem scanner + auto-compile trigger
│   ├── cognitive_reactor_seq014*    ← autonomous code modification
│   ├── pulse_harvest_seq015*        ← prompt → edit pairing
│   ├── prompt_recon_seq016*         ← prompt reconstruction + mutation tracking
│   ├── dynamic_prompt_seq017*       ← task-aware CoT injection ←── THE CORE
│   ├── task_queue_seq018*           ← Copilot-managed task queue
│   ├── prompt_journal_seq019*       ← enriched prompt journal (cross-ref all telemetry)
│   ├── copilot_prompt_manager_seq020* ← prompt block auditing
│   ├── mutation_scorer_seq021*      ← correlates prompt mutations to rework
│   ├── rework_backfill_seq022*      ← reconstructs historical rework scores
│   ├── session_handoff_seq023*      ← session summary generator
│   └── cognitive/
│       ├── adapter_seq001*          ← state → behavior adapter
│       ├── unsaid_seq002*           ← detects unsaid thoughts
│       └── drift_seq003*            ← typing pattern drift
├── streaming_layer/                 ← compiled package (19 files, 100% compliant)
├── pigeon_compiler/                 ← the compiler (~62 modules)
│   ├── git_plugin.py                ← post-commit orchestrator
│   ├── pigeon_limits.py             ← compliance thresholds + exclusion logic
│   ├── rename_engine/               ← file renames + import rewriting
│   │   ├── compliance_seq008/       ← compiled package (12 files) ✅
│   │   ├── heal_seq009/             ← compiled package (6 files) ✅
│   │   ├── manifest_builder_seq007/ ← compiled package (32 files) ✅
│   │   └── nametag_seq011/          ← compiled package (9 files) ✅
│   ├── cut_executor/                ← file slicing + bin-packing
│   ├── state_extractor/             ← AST + call graph analysis
│   ├── weakness_planner/            ← DeepSeek cut plan generation
│   └── runners/                     ← pipeline entry points
├── vscode-extension/                ← TypeScript keystroke capture
├── docs/
│   ├── push_narratives/             ← per-commit module self-narratives
│   └── self_fix/                    ← automated problem detection reports
├── logs/
│   ├── prompt_journal.jsonl         ← enriched journal (cross-refs all telemetry per prompt)
│   ├── chat_compositions.jsonl      ← keystroke compositions + deleted words + cognitive state
│   ├── copilot_prompt_mutations.json ← prompt file evolution snapshots
│   └── ai_responses.jsonl           ← (planned) Copilot response text + rework triples
├── operator_profile.md              ← living cognitive profile
├── operator_coaching.md             ← DeepSeek behavioral synthesis
├── file_heat_map.json               ← per-module cognitive load data
├── rework_log.json                  ← AI response quality log
├── query_memory.json                ← recurring query fingerprints
├── task_queue.json                  ← Copilot-managed task queue (auto-seeded from self-fix)
├── pigeon_registry.json             ← all module versions + token history (96 modules)
├── MASTER_MANIFEST.md               ← full project reference
├── CHANGELOG.md                     ← patch notes
└── test_all.py                      ← 4 core tests (always run before commit)
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

All 4 must pass before every commit.

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

## Current Status (2026-03-17)

| Component | Status |
|---|---|
| VS Code extension keystroke capture | ✅ Live (110+ session flushes) |
| Cognitive state classification | ✅ Live (5 states, 45+ profile entries) |
| Operator stats accumulation | ✅ Fixed (DATA block regex) |
| Unsaid thread detection | ✅ Live |
| File heat map per-module | ✅ Live |
| Rework detection | ✅ Live |
| Push narratives | ✅ Live (8 narratives) |
| Self-fix scanner | ✅ Live (20 problems detected last scan) |
| Prompt reconstruction | ✅ Live (24 mutations tracked) |
| Dynamic CoT injection | ✅ Live (11 sections, all data sources wired) |
| Task queue | ✅ Live (auto-seeded, manifest-linked, Copilot-managed) |
| Post-commit pipeline | ✅ Fully wired (10-step auto-commit) |
| Pigeon compiler | ✅ Operational |
| MASTER_MANIFEST | ✅ Rebuilt |
| Tests | ✅ 4/4 passing |

**Known open issues (tracked in `task_queue.json`):**
- `stress_test.py`, `test_all.py` have hardcoded pigeon imports — `tq-001`, `tq-002`
- AI response capture not yet implemented — `tq-003`, `tq-006`
- 76 `(background)` queries polluting `query_memory.json` — `tq-007`
- `operator_stats_seq008*` (397 lines) and `self_fix_seq013*` (352 lines) need pigeon compile — `tq-004`, `tq-005`

---

## License

MIT. See `LICENSE`.
