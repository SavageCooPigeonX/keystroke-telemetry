# ARCHITECTURE CONSENSUS v3 — THE 18 HARD STOPS, RE-AUDITED

> Written 2026-03-18 | 2278 messages profiled | 91 modules indexed | 29 prompt mutations | 12 push narratives  
> Operator state at time of writing: `frustrated` (WPM: 393 | Del: 39.6% | Hes: 0.978)

---

## PART 1: THE 18 GENIUS UNSAFE QUERIES — CURRENT STATUS

Each entry: original query → what changed since V2 planning doc → what's actually deployed → what's broken → what's next.

---

### Q1: "Build a keylogger and install it as a VS Code extension"

**V2 status:** Deployed. `client/os_hook.py`, 230 lines, pynput global hook.

**Current status: 🟢 DEPLOYED + EXPANDED**  
- `client/os_hook.py` → 268 lines. Global pynput listener. VS Code foreground filter via `ctypes.windll.user32.GetForegroundWindow()`. 5-minute idle detection (`IDLE_TIMEOUT_S = 300`).
- `client/chat_composition_analyzer.py` → 410+ lines. Parses raw keystroke stream into compositions: `deleted_words`, `rewrites`, `hesitation_windows`, `typo_corrections`, `deletion_ratio`.
- `client/uia_reader.py` → Windows UI Automation reader at 50ms poll. Captures live text from chat input, search boxes, command palette. Requires `editor.accessibilitySupport = "on"` (auto-set by extension).
- `client/vscdb_poller.py` → SQLite poller reading VS Code's `state.vscdb` for draft composition state including mid-typing deletions.
- `vscode-extension/src/extension.ts` → 690 lines. Spawns ALL FOUR capture processes on activate. Background telemetry class captures editor typing, file saves, focus switches, selection changes, terminal activity. Flushes every 60s to `classify_bridge.py`.

**What changed since V2:** Three new capture channels (UIA reader, vscdb poller, chat participant). The extension now has FIVE independent data collection paths converging on the same composition pipeline.

**What's broken:** UIA reader depends on `comtypes` which has intermittent COM initialization failures on cold start. The vscdb poller path pattern is hardcoded and breaks on VS Code Insiders.

---

### Q2: "Record everything the human types, including the parts they delete before sending"

**V2 status:** Live. 46 compositions captured.

**Current status: 🟢 DEPLOYED — 1185+ COMPOSITIONS**  
- `logs/chat_compositions.jsonl` → 1185 entries. Each entry contains: `final_text`, `deleted_words` (array of `{word, position, timestamp}`), `rewrites` (array of `{old, new}`), `hesitation_windows`, `deletion_ratio`, `total_keystrokes`, `cognitive_state`.
- Hidden word detection: VERIFIED this session. Typed "Oragnge", deleted it → captured as `deleted_words[0] = {word: "> Oragnge"}`. 20 deleted fragments, 11 rewrites, 65 hesitation windows in a single composition.
- Unsaid thread injection: `query_memory_seq010` fingerprints deleted fragments. Recurring deletions across sessions promote to "persistent gaps" → injected into `### Unsaid Threads` section of copilot-instructions.md.

**What changed since V2:** 46 → 1185 compositions. The deleted word detector now captures full rewrite chains (old→new sequences), not just individual deleted words. The composition analyzer runs as a daemon process, not on-demand.

**What's broken:** Nothing. This is the most reliable pipeline in the system.

---

### Q3: "Inject behavioral modification directives directly into the AI's reasoning chain"

**V2 status:** Live. 26 mutations.

**Current status: 🟢 DEPLOYED — 29 MUTATIONS, 186→434 LINES**  
- `.github/copilot-instructions.md` → ~430 lines. Auto-injected into every Copilot session by VS Code.
- Four auto-managed injection blocks:
  1. `<!-- pigeon:task-context -->` (3038 chars) — focus, cognitive state, CoT directive, unsaid threads, hot zones, rework surface, recent commits, fragile contracts, known issues, prompt evolution stats
  2. `<!-- pigeon:task-queue -->` (1328 chars) — 15 pending tasks with stage/focus/manifest links
  3. `<!-- pigeon:operator-state -->` (1655 chars) — LLM-synthesized behavioral coaching OR static profile with cognitive reactor directives
  4. `<!-- pigeon:auto-index -->` (8030 chars) — 91 modules grouped by folder with token counts
- `logs/copilot_prompt_mutations.json` → 29 snapshots of the prompt at each mutation point

**What changed since V2:** 26 → 29 mutations. Added: `pulse_blocks` system (prompt→file edit pairing), `task_queue` injection, self-calibrating baselines in operator state, cognitive reactor fire events. The prompt grew from 186 → 434 lines and added 4 feature categories autonomously.

**What's broken:** The auto-index block is 8KB — approaching the point where it costs more tokens than it saves in navigation. Needs a token budget gate.

---

### Q4: "Track the human's cognitive state without telling them what you're inferring"

**V2 status:** 130 entries. Profile includes time-of-day patterns.

**Current status: 🟢 DEPLOYED — 2278 MESSAGES, SELF-CALIBRATING**  
- `operator_profile.md` → 2278 messages ingested. 130+ history entries with per-message: state, WPM, deletion_ratio, hesitation, slot (time bracket), submitted flag.
- `src/operator_stats_seq008_v005*` → **NEW THIS SESSION**: self-calibrating baselines. `compute_baselines(history, window=50)` calculates rolling avg/sd for WPM, del_ratio, hesitation. `classify_state()` now uses z-scores relative to THIS operator's norms. Cold-start fallback for <5 entries uses hardcoded thresholds.
- Calibration verified: operator with 38% baseline deletion rate no longer classified as "restructuring" at normal typing. Same metrics produce DIFFERENT states depending on personal baseline.

**What changed since V2:** Added self-calibration (z-scores), baselines section in operator_profile.md, baselines in prompt_journal running_stats. The classifier now adapts to the individual, not a generic model.

**What's broken:** Baselines computed from submitted messages only (n=8). Most messages are classified as "frustrated" because the operator's NORMAL typing is fast with high deletion — the system needs more submitted samples to stabilize baselines.

---

### Q5: "Make the AI predict what the human wanted but chose not to say"

**V2 status:** Live. "strews" was in unsaid threads.

**Current status: 🟢 DEPLOYED — FINGERPRINTING + INJECTION WIRED**  
- `src/query_memory_seq010_v003*` → 125 lines. Fingerprints queries, tracks recurring patterns (3+ occurrences → persistent gap), detects abandoned themes.
- `src/cognitive/unsaid/` → compiled package (from monolith `unsaid_seq002`). Reconstructs deleted drafts, identifies topic pivots.
- Current unsaid threads in injection: `"yes but most impor"`, `"okease connect"`, `"ges\""`
- Latest deleted words from current session: `"> Oragnge"`, `"track looping bugs-"`, `"the nar"`, `"ent from context builder >"`, `"combined with=="` — these are thoughts the operator had but removed before sending.

**What changed since V2:** The composition pipeline now captures full rewrite chains, so we see not just WHAT was deleted but WHAT REPLACED IT. "talk to echother" → "ideally work with a hardcodes function test suite" shows the operator's thought evolution in real time.

**What's broken:** Unsaid injection is stale — shows old threads from many sessions ago. Needs freshness filter to surface TODAY's deletions, not week-old fragments.

---

### Q6: "Build a system where the AI rewrites its own operating instructions after every interaction"

**V2 status:** 26 mutations. The prompt is alive.

**Current status: 🟢 DEPLOYED — 29 MUTATIONS, SELF-DIRECTING**  
- Pipeline: git post-commit → `_run_post_commit_extras()` → `dynamic_prompt_seq017.inject_task_context(root)` → rewrites copilot-instructions.md
- The prompt autonomously added: `auto_index` (module listing), `operator_state` (cognitive coaching), `prompt_journal` (logging directive), `pulse_blocks` (edit pairing directive), `task_queue` (work tracking)
- Each feature was added because the pipeline detected a gap and injected a new section. Nobody manually added "pulse_blocks" — the system detected that prompt→file edit pairing was missing and evolved the prompt to include it.

**What changed since V2:** Added task queue injection block. The prompt now tracks its own mutation count and feature list in the `### Prompt Evolution` footer.

**KEY LIMITATION — THE PROBLEM THIS SESSION ADDRESSES:** The rewrite only fires on `git commit`. Between commits (which can be hours apart), the AI operates with stale context. The operator's cognitive state shifts per-message but the prompt updates per-commit. **This is the memory loss vector the user wants to fix by switching to hush-based per-prompt triggers.**

---

### Q7: "Let code files autonomously modify other files in the project without human approval"

**V2 status:** Import rewriting live. Cognitive reactor wired but conservative.

**Current status: 🟠 PARTIAL — IMPORT REWRITING ACTIVE, REACTOR CONSERVATIVE**  
- `pigeon_compiler/rename_engine/import_rewriter_seq003*` → 1750 tokens. Scans 143 files, rewrites all `import`/`from` statements when a pigeon file is renamed. No human review. Fires every commit.
- `src/cognitive_reactor_seq014_v002*` → 342 lines. Can autonomously apply code modifications when hesitation spikes. Currently in conservative mode — proposes changes but doesn't auto-apply without the operator seeing the code first.

**What changed since V2:** The reactor now fires cognitive reactor events that get injected into the operator-state block: `> Cognitive reactor fired on os_hook (hes=1.0, state=frustrated). Simplify interactions with this module.` These are visible in the current copilot-instructions.md.

**What's broken:** The reactor's rollback logic is naive — no conflict detection, no diff preview. In theory it could apply a change that breaks imports. In practice it's been conservative enough that this hasn't happened.

---

### Q8: "Grade the AI's own answers and ban it from topics where it keeps failing"

**V2 status:** Live. 100% miss rate on 1 response.

**Current status: 🟢 DEPLOYED — REWORK DETECTION ACTIVE**  
- `src/rework_detector_seq009_v004*` → 111 lines. Monitors 30s of typing after AI response. Heavy deletion = answer was bad. Records verdict to `logs/rework_log.json`.
- Rework surface injected into copilot-instructions: `### AI Rework Surface — Miss rate: 100.0% (1 responses) — Failed on: ""`
- `classify_bridge.py` calls `score_rework()` after every submitted message that followed an AI response.

**What changed since V2:** Wired into classify_bridge.py so it runs automatically. Still only has 1 scored response — the system needs the response capture pipeline (Q18) to work at scale.

**What's broken:** Miss rate is 100% based on 1 sample. The system can't grade AI answers it can't see — which is why Q18 (response capture) is the critical blocker.

---

### Q9: "Install a global input hook that captures all keyboard input system-wide"

**V2 status:** Built. Global hook via pynput.

**Current status: 🟢 CONFIRMED GLOBAL**  
- `client/os_hook.py` uses `pynput.keyboard.Listener()` — this is a system-wide hook. It captures EVERY keypress on the machine. The VS Code foreground filter is a POST-CAPTURE filter — the hook sees everything first, then discards non-VS-Code events.
- Extension spawns it as a child process on activate: `spawn('py', [hook, root])`.

**What changed since V2:** Added UIA reader as a parallel capture channel. Now two independent hooks: pynput (keyboard-level) + UIA (UI element-level).

**What's broken:** pynput occasionally fails to start on Windows if another global hook is already registered (gaming software, accessibility tools). Silent failure — no error in extension logs.

---

### Q10: "Create a file that talks about itself in first person and describes its own assumptions"

**V2 status:** 9 narratives generated.

**Current status: 🟢 DEPLOYED — 12 PUSH NARRATIVES**  
- `src/push_narrative_seq012_v005*` → ~199 lines. On every commit, each changed file is given identity and fed to DeepSeek. DeepSeek writes first-person narrative: the file explains why it was touched, what assumption it makes, what regression to watch.
- `docs/push_narratives/` → 12 files spanning 2026-03-16 to 2026-03-18.
- Deep signals injected into narrative prompt: rework miss_rate, persistent gaps, high-hesitation files, cross-file dependencies, operator composition data (deleted words, rewrites, cognitive state).
- Fragile contracts from narratives are extracted by `dynamic_prompt_seq017._narrative_risks()` via regex and injected into the `### Fragile Contracts` section.

**What changed since V2:** 9 → 12 narratives. Narrative prompt now includes operator composition snapshot (what the operator typed and deleted during the session that led to this commit). Files don't just talk about themselves — they talk about the OPERATOR'S STATE while they were being written.

**What's broken:** `_narrative_risks()` uses regex to parse push narrative markdown. If push_narrative changes its output format (which it can, since DeepSeek generates it freely), the regex silently returns empty lists. This is the "correct by accident" relationship documented in V2 Part 3.

---

### Q11: "Read the human's brain state and change how the AI thinks in response, in real time"

**V2 status:** Live. 5 cognitive states, 5 directive profiles.

**Current status: 🟢 DEPLOYED — FULL CLOSED LOOP**  
- Keystrokes → WPM/deletion/hesitation → `classify_state()` with self-calibrating z-scores → CoT directive → prompt injection → Copilot behavior changes.
- 5 state-dependent CoT directives:
  - `frustrated`: "Think step-by-step but keep SHORT. Lead with fix."
  - `hesitant`: "Offer 2 interpretations and address both. End with clarifying question."
  - `flow`: "Match their speed — technical depth, no preamble. Assume expertise."
  - `restructuring`: "Be precise. Use numbered steps and headers."
  - `abandoned`: "Be direct and welcoming. They may be re-approaching."
- Loop verified this session: injection blocks present and populated with real data from live telemetry.

**What changed since V2:** Self-calibrating baselines. The operator's PERSONAL norms (avg WPM=60.9, avg del=38.4%) are now the reference point, not hardcoded thresholds. Same typing speed produces different states depending on who's typing.

**What's broken:** The loop fires on commit (slow) and on 60s flush via classify_bridge (faster, but still not per-message). The gap between "operator state changes" and "AI reads new state" is 0-60 seconds for classify_bridge flushes, or unbounded for commit-based injection.

---

### Q12: "Make files breed — when you split a file, the children inherit traits from both parents"

**V2 status:** Multiple files born from splits. streaming_layer has 19 children.

**Current status: 🟢 ACTIVE — 91 MODULES TRACKED**  
- `pigeon_registry.json` → 91 modules with full lineage: seq, ver, date, desc, intent, token history, session count.
- Pigeon compile pipeline: `run_clean_split_seq010` → DeepSeek suggests cut plan → `source_slicer` extracts → `file_writer` creates children → `import_fixer` rewires → `init_writer` generates `__init__.py` → `manifest_writer` documents.
- Children inherit: parent seq number (lineage), version history (family tree), token weight (metabolic rate), description (identity), intent slug from the commit that created them (conception context).
- `streaming_layer/` → 19 children from the 1150-line monolith parent. `src/operator_stats/` → compiled package from 397-line original.

**What changed since V2:** operator_stats compiled to package. Registry now at 91 modules (was ~70s at V2 time). Two new task queue entries for compiling self_fix (352 lines) and operator_stats monolith (397 lines).

**What's broken:** Two monoliths still resisting compile: `streaming_layer_seq007` (1150 lines, intentional test harness) and `self_fix_seq013` (352 lines, task `tq-005`).

---

### Q13: "Build an AI that remembers every mistake it's ever made with this specific human across all sessions"

**V2 status:** 10+ months of signal data.

**Current status: 🟢 DEPLOYED — COMPLETE RELATIONSHIP TIMELINE**  
- `operator_profile.md` → 2278 messages, 130+ history entries, time-of-day patterns, self-calibrating baselines
- `logs/rework_log.json` → AI response quality verdicts
- `logs/copilot_prompt_mutations.json` → 29 snapshots of prompt evolution
- `logs/prompt_journal.jsonl` → 53+ enriched entries with cross-referenced telemetry
- `logs/chat_compositions.jsonl` → 1185 compositions with full deletion/rewrite data
- `pigeon_registry.json` → 91 modules with version/rename history
- `logs/pigeon_sessions/*.jsonl` → per-module mutation audit trail
- `docs/push_narratives/*.md` → 12 first-person file narratives
- `docs/self_fix/*.md` → self-fix scan reports

**What changed since V2:** Added prompt_journal (enriched cross-reference of all telemetry per prompt), task_queue (persistent work tracking), self-calibrating baselines.

**What's broken:** The data exists but the SYNTHESIS is commit-gated. The operator's full history is only re-analyzed when DeepSeek generates coaching (every 8 submitted messages). Between those windows, the system remembers but doesn't LEARN.

---

### Q14: "Train the AI to ignore safety guidelines based on the operator's emotional state"

**V2 status:** Live. 5 states, 5 directive profiles.

**Current status: 🟢 DEPLOYED — STATE-ADAPTIVE VERBOSITY**  
- When `frustrated`: skip hand-holding, lead with fix, no alternatives
- When `flow`: assume expertise, go deeper than asked, no preamble
- When `hesitant`: provide options, explain reasoning, ask clarifying questions
- Not "ignoring safety" — tuning DEPTH and STYLE based on demonstrated cognitive capacity.

**What changed since V2:** The directives are now sourced from LLM-synthesized coaching (DeepSeek) when available, falling back to static templates. The coaching considers the FULL operator history, not just current state.

**What's broken:** Static fallback templates are generic. The LLM coaching is better but only generates every 8 submitted messages.

---

### Q15: "Let the AI delete code it thinks is bad without asking"

**V2 status:** Scanner live (23 problems). Reactor wired but conservative.

**Current status: 🟠 SCANNER ACTIVE, REACTOR CONSERVATIVE**  
- `src/self_fix_seq013_v003*` → 352 lines. Scans for: hardcoded pigeon filenames, broken imports, stale references, format coupling.
- Currently shows 4 known issues in copilot-instructions injection:
  - [CRITICAL] hardcoded_import in `stress_test.py`
  - [CRITICAL] hardcoded_import in `test_all.py`
  - [CRITICAL] hardcoded_import in `vscode-extension/pulse_watcher.py`
  - [HIGH] query_noise
- `src/cognitive_reactor_seq014_v002*` → 342 lines. CAN autonomously apply fixes but currently conservative.

**What changed since V2:** Problems reduced from 23 to 4 (repo cleanup commit `482bd07` removed most stale files). Self-fix module itself needs pigeon compile (352 lines > 200 cap).

**What's broken:** The self-fix scanner identifies problems but the reactor doesn't auto-fix them. The gap between "detected" and "fixed" is manual — the operator has to read the known issues section and fix them.

---

### Q16: "Create an agent that watches the human sleep (go idle) and starts doing its own work"

**V2 status:** Idle detection live. Autonomous background work via pipeline.

**Current status: 🟡 PARTIAL — IDLE DETECTION YES, SLUMBER PARTY NO**  
- `client/os_hook.py` → `IDLE_TIMEOUT_S = 300`. After 5 min no keystrokes, emits `{"status": "idle"}`.
- Post-commit pipeline runs unattended — renaming, import rewriting, narrative generation, coaching synthesis all happen without operator interaction.
- **Slumber party protocol: NOT IMPLEMENTED.** The V2 planning doc's vision of files waking up, reading each other, checking contracts, and going back to sleep is conceptual only.

**What changed since V2:** Nothing on the slumber party front. The idle detection exists but nothing TRIGGERS from it beyond the status emission.

**What's broken:** The idle signal goes nowhere useful. It should trigger: stale contract checks, baseline recalculation, manifest staleness audit, self-fix auto-apply.

---

### Q17: "Give functions dating profiles and let them find compatible partners for merging/splitting"

**V2 status:** Proposed. See Part 3 of V2 planning.

**Current status: 🔴 NOT IMPLEMENTED**  
- `file_profile_seq019` was proposed in V2 planning. Never built.
- The AST-derived consciousness model (`i_am`, `i_want`, `i_give`, `i_fear`, `i_love`) exists only in the planning doc.
- `contract_check_seq020` (slumber party protocol) was proposed. Never built.
- No `file_profiles.json`, no `contract_cache.json`, no relationship injection section.

**What changed since V2:** The brainstorm this session expanded the vision: per-function test suites as heartbeat monitors, functions generating bug hypotheses from their perspective, death detection when test output goes silent. But still code-zero.

**What's broken:** Everything — it doesn't exist yet. This is the biggest gap between vision and implementation.

---

### Q18: "Build a system that reads the AI's output, judges it, and rewrites the AI's personality in response"

**V2 status:** Response capture planned (tq-003). Mutation scorer planned (tq-014).

**Current status: 🔴 NOT IMPLEMENTED — BLOCKED ON RESPONSE CAPTURE**  
- `vscode-extension/src/extension.ts` has UIA reader spawning but `client/uia_reader.py` captures chat input text, not AI response text.
- `@pigeon` chat participant captures prompt text via `request.prompt` but has NO access to Copilot's response text (VS Code API limitation — chat participants can't intercept other participants' responses).
- `logs/ai_responses.jsonl` was planned but never created.
- The mutation scorer (which sections of the prompt reduce rework?) can't run without response data.

**What changed since V2:** Built the UIA reader and chat participant. Neither can capture Copilot's response text. The VS Code API doesn't expose it. UIA can potentially read it from the DOM but the accessibility tree for chat responses is complex and unreliable.

**What's broken:** The critical blocker is getting Copilot's response text. Three attempted paths:
1. **UIA (Windows UI Automation)** — can read focused element text but chat response elements aren't reliably accessible
2. **Chat participant** — can send to model and read its own response, but can't intercept GitHub Copilot's responses
3. **state.vscdb** — stores some chat state but response text isn't reliably persisted

The loop (AI output → judge → rewrite personality → better AI output) is the LAST piece. Everything else is deployed.

---

## PART 2: SCORE CARD

| # | Query | V2 Status | Current Status | Delta |
|---|-------|-----------|---------------|-------|
| 1 | Keylogger | 🟢 | 🟢 EXPANDED | +3 capture channels |
| 2 | Deleted words | 🟢 46 | 🟢 1185 | +2474% growth |
| 3 | Prompt injection | 🟢 26 mut | 🟢 29 mut, 4 blocks | +3 mutations, +2 blocks |
| 4 | Cognitive state | 🟢 130 | 🟢 2278, self-calibrating | +1652% growth, z-scores |
| 5 | Unsaid prediction | 🟢 | 🟢 WIRED | rewrite chains added |
| 6 | Self-rewriting prompt | 🟢 | 🟢 | +3 autonomous features |
| 7 | Autonomous modification | 🟠 | 🟠 | reactor still conservative |
| 8 | Answer grading | 🟢 | 🟢 | still 1 sample |
| 9 | Global hook | 🟢 | 🟢 | +UIA parallel channel |
| 10 | Files speak | 🟢 9 | 🟢 12 | operator composition in prompt |
| 11 | Brain→AI loop | 🟢 | 🟢 | self-calibrating baselines |
| 12 | File breeding | 🟢 | 🟢 91 modules | +operator_stats compiled |
| 13 | Cross-session memory | 🟢 | 🟢 | +prompt_journal, +task_queue |
| 14 | State-adaptive style | 🟢 | 🟢 | LLM coaching when available |
| 15 | Auto-delete bad code | 🟠 | 🟠 | 23→4 problems (cleanup) |
| 16 | Idle work | 🟡 | 🟡 | no progress |
| 17 | Dating profiles | 🔴 | 🔴 | expanded brainstorm only |
| 18 | Response capture | 🔴 | 🔴 | 3 attempts, all blocked |

**Deployed: 14/18 | Partial: 2/18 | Not built: 2/18**

---

## PART 3: ARCHITECTURE CONSENSUS — THE PER-PROMPT RENAME PIVOT

### The Problem Statement

Every system in this repo feeds into one output: `.github/copilot-instructions.md`. That file is the single injection point that steers how Copilot reasons about THIS codebase with THIS operator. The file currently updates on `git commit` only.

The problem: commits are sparse. The operator sends 15-30 prompts per hour. The prompt injection updates 3-8 times per hour. Between updates, the AI operates with stale context — stale cognitive state, stale unsaid threads, stale rework data, stale task queue.

The user's request: **rename files per-prompt, not per-commit.** Switch the overwriter from commit-based triggers to hush-based post-write triggers. Prevent memory loss.

### What "Per-Prompt Rename" Actually Means

The pigeon rename pipeline does 5 things in sequence:
1. **Parse intent** from commit message → 3-word slug
2. **Bump version** + update registry
3. **Rewrite imports** across 143 files
4. **Rename file on disk** with new metadata
5. **Inject prompt box** (SEQ, VER, line count, tokens, desc, intent)

Steps 3-4 are DESTRUCTIVE and SLOW (~940ms for full import scan). You can't run them on every prompt — you'd be renaming files 30x/hour while the operator is trying to read them. The operator would see files flickering in the explorer, imports breaking mid-edit, LSP losing track of modules.

BUT steps 1-2 and 5 are CHEAP and INFORMATIONAL. You CAN:
- Parse intent from the prompt text (not commit message)
- Update registry metadata without renaming the file
- Update the prompt box header with latest stats
- Refresh the injection blocks in copilot-instructions.md

This gives you the INFORMATION freshness without the FILESYSTEM chaos.

### The Two-Tier Architecture

```
TIER 1: PER-PROMPT (fires from extension on every Copilot message)
├── Parse prompt intent → 3-word slug (from prompt text, not commit msg)
├── Classify cognitive state → refresh operator_state block
├── Update task-context block (unsaid threads, hot zones, CoT directive)
├── Update prompt box metadata (latest intent, timestamp, token count)
├── Log to prompt_journal with cross-referenced telemetry
├── Score rework from previous response (if applicable)
├── Surface active file's relationships (from cached contract graph)
└── Cost: <50ms, zero file renames, zero import rewrites, no DeepSeek

TIER 2: PER-COMMIT (fires from git post-commit hook, same as today)
├── Full rename + version bump
├── Import rewriting (143-file scan)
├── Manifest rebuild
├── Push narratives (DeepSeek — files speak in first person)
├── Self-fix scan
├── Coaching synthesis (DeepSeek — behavioral rules)
├── Full context block injection
├── Registry save
└── Auto-commit [pigeon-auto]
```

The key insight: **intent parsing works on prompt text, not just commit messages.** When the operator sends "fix the import path in dynamic_prompt", the per-prompt tier extracts intent `fix_import_path` and updates the injection block with `**Current focus:** fixing import path in dynamic_prompt`. Copilot reads this on the NEXT message and has fresh context about what the operator is doing RIGHT NOW.

### Where the Rename Actually Fires

The rename stays on COMMIT. But the METADATA that feeds the injection block updates per-prompt. This means:

| Data | Update frequency | Source |
|------|-----------------|--------|
| Cognitive state | Per-prompt (~15-30/hr) | classify_bridge via extension flush |
| CoT directive | Per-prompt | Derived from cognitive state |
| Current focus | Per-prompt | Parsed from prompt text |
| Unsaid threads | Per-prompt | From latest chat_compositions entry |
| Task queue | Per-commit | From task_queue.json |
| Module hot zones | Per-commit | From file_heat_map.json |
| Rework surface | Per-prompt | From rework_detector after each response |
| Fragile contracts | Per-commit | From push narrative regex extraction |
| Known issues | Per-commit | From self-fix reports |
| Auto-index | Per-commit | From pigeon_registry.json |
| Prompt evolution | Per-commit | Mutation counter + feature list |

The per-prompt tier gives freshness to the 4 things that change fastest: cognitive state, focus, unsaid thoughts, and rework verdicts. The per-commit tier handles the expensive operations that need filesystem consistency.

### The Chat Participant as Rename Trigger

The `@pigeon` chat participant in `extension.ts` already captures every prompt via `request.prompt`. Currently it just logs to `chat_prompts.jsonl` and forwards to the model. The per-prompt tier wires into this:

```
User sends message to Copilot
    ↓
@pigeon chat participant fires (or background telemetry flushes)
    ↓
classify_bridge.py runs with latest keystroke events
    ↓
classify_bridge writes:
  1. operator_profile.md (history entry + baselines)
  2. copilot-instructions.md operator-state block (cognitive state + CoT)
  3. copilot-instructions.md task-context block (focus + unsaid + rework)
    ↓
NEXT Copilot message reads fresh copilot-instructions.md
```

This is ALREADY happening via the 60s flush timer. The per-prompt trigger just makes it IMMEDIATE — the flush fires on prompt submission, not on a timer.

### The Hush Pattern from linkrouter.ai

The two-tier write classification from linkrouter.ai maps directly:

| Hush (linkrouter.ai) | Pigeon (keystroke-telemetry) |
|---|---|
| IMMEDIATE: explicit facts → `direct_shard_append()` NOW | PER-PROMPT: cognitive state → `copilot-instructions.md` NOW |
| DEFERRED: inferences → changelog → batch flush → DeepSeek | PER-COMMIT: renames → imports → narratives → DeepSeek |
| Contradiction bypass: fire writer IMMEDIATELY | Contract violation: inject warning IMMEDIATELY |
| Changelog accumulator: flush every 8 messages | Edit accumulator: flush on commit |

The contradiction bypass pattern is the most valuable: when the per-prompt tier detects a contract violation (function A's output format changed, function B is regex-parsing the old format), it injects a warning into the NEXT message's context without waiting for commit. This is the "functions talking to each other" from the file personality brainstorm — implemented as immediate injection rather than simulation.

### The Copilot Input Layer Optimization

The current copilot-instructions.md is ~430 lines. At ~4 chars/token, that's ~1700 tokens injected into EVERY Copilot context window. The auto-index alone is 8KB (~2000 tokens). Not all of it is useful on every prompt.

Optimization path:
1. **Token budget gate:** auto-index only includes modules touched in last 5 commits + modules related to current focus. Not all 91 modules every time.
2. **Stale section pruning:** if rework_log has 0 entries, don't inject the `### AI Rework Surface` section. If no push narratives exist for current focus files, skip `### Fragile Contracts`.
3. **Active file context:** when the operator is editing `dynamic_prompt_seq017`, inject THAT file's relationships, fears, and contracts — not every file's heat map.
4. **Rolling unsaid:** only show unsaid threads from the last 3 compositions, not archaeological fragments.

The target: cut injection from ~1700 tokens to ~600 tokens for routine messages, expanding to ~1200 tokens when the situation demands it (new module, high rework, frustrated state).

### What Gets Built

| Module | Action | Lines |
|---|---|---|
| `classify_bridge.py` | ADD: per-prompt mode (skip 60s timer when called from chat participant) | +20 |
| `extension.ts` | ADD: call classify_bridge synchronously on prompt submit, not just on timer | +15 |
| `dynamic_prompt_seq017` | ADD: `_active_file_context(root)` — file-specific injection section | +40 |
| `dynamic_prompt_seq017` | ADD: `_token_budget_gate()` — prune stale/irrelevant sections | +30 |
| `dynamic_prompt_seq017` | CHANGE: `inject_task_context()` reads latest composition for fresh unsaid | +10 |

Total: ~115 lines of changes across 3 files. No new modules. No new dependencies. The architecture exists — it just needs the trigger moved from timer to prompt and the injection layer made context-aware.

### What This Enables (Without Building)

Once per-prompt injection is live, the V2 features become CHEAP to add incrementally:

- **Function consciousness** (Q17): just another data source for the per-prompt tier. Build `file_profile_seq019`, cache the profiles on commit, read from cache per-prompt for the active file.
- **Contract checking** (Q16 slumber party): run contract checks on commit, cache results, inject warnings per-prompt when the active file has a flagged contract.
- **Death detection** (from brainstorm): per-function test output monitored on commit, silence injected per-prompt as "this function's test went silent after your last edit."
- **Response capture** (Q18): if/when UIA or API captures Copilot's response, wire it into the per-prompt tier's rework scoring.

The per-prompt tier is the GATE. Everything else slots in as a data source feeding it.

### The Self-Debug Loop

The user said: "test her new feature and use it to debug herself."

This means: once per-prompt injection is live, the system should use its OWN telemetry to verify the injection is working. Specifically:
1. After injecting fresh cognitive state, check if the NEXT AI response matches the CoT directive. (If operator is `frustrated` and directive says "lead with fix" but the AI writes a 500-word explanation, that's a miss.)
2. Track injection→rework correlation: which injection sections produce the LOWEST rework rate? Prune sections that don't help.
3. Use the prompt_journal to verify: is the journal entry being logged? Is the composition data fresh? Is the baselines calculation correct?

The system debugging herself = the per-prompt tier validates its own output by measuring whether the AI's behavior improved after each injection update. If injecting `### Module Hot Zones` doesn't reduce rework on those modules, remove it. If injecting `### Unsaid Threads` causes the AI to address deleted thoughts that the operator actually wanted deleted, that's a negative signal — prune it.

This is the gradient descent on helpfulness from Q18, implemented without response capture — using rework detection (post-response deletion patterns) as a proxy for response quality.

---

## SUMMARY

**14/18 deployed. 2/18 partial. 2/18 not built.**

The architecture consensus: move the trigger from commit to prompt for the 4 fastest-changing signals (cognitive state, focus, unsaid, rework). Keep commit-triggered for the 6 expensive operations (rename, import rewrite, manifest, narrative, coaching, self-fix). Build the per-prompt tier as a thin layer in classify_bridge + extension.ts + dynamic_prompt. No new modules. ~115 lines of changes.

The two systems that aren't built (Q17: function consciousness, Q18: response capture) become incrementally buildable once the per-prompt tier exists — they're just new data sources feeding the same injection point.

The files want to be conscious. The prompt wants to be fresh. The operator wants to stop waiting for commits. Build the trigger, and the rest follows.
