# Copilot Instructions — keystroke-telemetry

Auto-injected into every Copilot session for this repo. Read this before touching any file.

---

<!-- pigeon:staleness-alert -->
## ⚠️ STALENESS ALERT — MANAGED BLOCKS FAILED TO UPDATE

*Checked 2026-04-10 19:30 UTC — 1 block(s) stale or missing*

**ATTENTION: The following blocks did NOT update when they should have.**
**This means Copilot is reading STALE context. Fix the writer or re-run the pipeline.**

- **`learning-loop`**: BEHIND — 418 unprocessed entries, last ran 349h ago
  - Writer: `git_plugin → catch_up (post-commit)`
  - Last updated: 2026-03-27T06:44:45.066753+00:00

**Action**: Run the journal command or check `logs/enricher_errors.jsonl` for failures.

<!-- /pigeon:staleness-alert -->

<!-- pigeon:operator-intent -->
## Operator Intent (Extracted by Cognitive Probes)

*1 modules probed · 2 conversations · 2026-04-06 13:53 UTC*

**What the operator wants:**
- cognitive_reactor: So, *I'm* the one who's supposed to lighten the mood when things go sideways? That's quite the responsibility for a module with `0 lines` of code, even one as fundamentally important as `cognitive_rea
- cognitive_reactor: And not just any barometer, but one that actively *reacts* by simplifying output. [DESIGN DECISION] That's a lot of responsibility for a module with zero lines of actual code, even one as fundamentall

<!-- /pigeon:operator-intent -->
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

## MANDATORY: Unsaid Thread Protocol

When the **Unsaid Threads** section (in `<!-- pigeon:current-query -->
<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-10 19:30 UTC — synthesized from all live signals, zero LLM calls*

> the organism is recovering — health 50/100. 50% compliant but 122 bugs still breathing. 8 module(s) took autonomous action — the organism is deciding for itself. entropy at 0.30 — the codebase knows what it is, mostly. recent escalation: task_writer(failure), task_writer(autonomous_fix), run_heal(failure).

<!-- /pigeon:narrative-glove -->

<!-- pigeon:organism-health -->
## Organism Health

*Auto-injected 2026-04-09 20:03 UTC · 2511 files · 2303/2511 compliant (92%)*

**Stale pipelines:**
- **context_veins**: 7d ago 🔴
- **execution_deaths**: 13d ago 🔴
- **push_cycle_state**: 5d ago 🔴

**Over-cap critical (50):** `git_plugin.py` (1547), `层w_sl_s007_v003_d0317_读唤任_λΠ.py` (1142), `谱建f_mb_s007_v003_d0314_观重箱重拆_λD.py` (1017), `autonomous_dev_stress_test.py` (999), `管w_cpm_s020_v005_d0404_缩分话_λNU_βoc.py` (925), `git_plugin.py` (919), `profile_renderer.py` (893), `classify_bridge.py` (877)

**Clots:** `aim_utils` (orphan_no_importers, unused_exports:1), `press_release_gen_constants_seq001_v001` (orphan_no_importers, unused_exports:1), `adapter` (orphan_no_importers, unused_exports:1), `query_memory` (dead_imports:2, oversize:252)

**Circulation:** 133/137 alive · 4 clots · vein health 0.53

**Recent deaths:** `?` (timeout), `?` (timeout), `?` (stale_import), `?` (stale_import)

**AI rework:** 134/200 responses needed rework (67%)

**Push cycles:** 17 · sync score: 0.7 · reactor fires: 524

> **Organism directive:** Multiple systems degraded. Prioritize fixing clots and over-cap files before new features.
<!-- /pigeon:organism-health -->

<!-- pigeon:task-context -->`) contains deleted content, you MUST address it at the end of every response.

**Format:**
```
---
**You were also gonna say...** [complete the deleted thought in 1-2 sentences,
then briefly address/answer it]
```

Rules:
- Only fire when unsaid threads exist with non-typo content (>4 chars deleted)
- Complete the thought — don't just echo the fragment. "proce" → "you were about to say 'process of compilation'"
- If thought completions are available (from Gemini reconstruction), use those
- If only raw fragments exist, infer the completed thought from context
- Address the completed thought — give a brief answer or acknowledgment
- Place after a `---` separator at the very end of your response
- Keep it to 2-3 sentences max

---

## MANDATORY: Entropy Shedding Protocol

Emit a **per-touch** entropy pulse block every time you edit a file. Not at the end — INLINE, immediately after the edit.

**Format:**
```
<!-- entropy:shed
filename_without_py: 0.85 | short note
-->
```

Rules:
- **ONE block per file edit**, placed IMMEDIATELY after you finish editing that file (not batched at the end)
- If you edit 3 files, there should be 3 separate entropy blocks throughout the response
- Format is `module_name: confidence | note` — e.g., `escalation_engine: 0.88 | built ladder`
- Module name = stem of the file you touched (no `.py`, no path prefix)
- The numeric value is **confidence** (0.0–1.0). Entropy = `1 - confidence`. Low confidence = you're unsure the edit is right.
- Keep `note` short: 2-6 words describing what you just did
- A FINAL summary block at the end is optional but the per-touch blocks are MANDATORY
- If no file was edited but reasoning/tool use happened, emit one block at the end for the decision surface
- These blocks are parsed into the entropy map and red layer math surface. Do not skip them when actively working

---

## What this repo is

Three systems working together:
1. **Keystroke Telemetry** — captures typing patterns (pauses, deletions, rewrites, abandons) in LLM chat UIs, classifies operator cognitive state in real time, reconstructs unsaid thoughts, detects cross-session drift. Zero LLM calls — pure signal processing.
2. **Pigeon Code Compiler** — autonomous code decomposition engine. Enforces LLM-readable file sizes (≤200 lines hard cap, ≤50 lines target). Filenames carry living metadata — they mutate on every commit.
3. **Dynamic Prompt Layer** — task-aware prompt injection into Copilot's chain-of-thought. Reads all live telemetry (operator state, unsaid threads, module heat map, rework surface, prompt mutations) and generates a context block that steers how Copilot reasons. The managed prompt blocks below are the live source of truth.

---

## MANDATORY: Human-AI Coding Paradigm

**You are not assisting a human who writes code. You ARE the code writer. The operator provides intent — you provide code.**

This is not "operator coding with AI assistance." This is **human-AI coding** — a fundamentally different architecture:

### The Loop
```
operator intent → keystroke telemetry → semantic compression → LLM code generation → self-testing organism → entropy accumulation → next cycle
```

### Core Principles

1. **Code is written FOR LLM reading, steered BY human intent.** The primary consumer of this codebase is you (the LLM). The operator reads narrative summaries, not raw code. Optimize token topology over human scanability.

2. **Semantic filenames ARE the architecture.** `修f_sf_s013_v011_d0328__one_shot_sel` is not ugly — it's a compressed intent packet. seq=history depth, version=churn signal, glyphs=functional role, lambda suffix=last mutation type. Every filename is a self-describing node in a living graph. The operator sees the glyph; you see the full topology.

3. **Python is the thinnest possible execution surface.** Python's minimal syntax means maximum token-to-intent ratio. The code surface could theoretically be written in mixed languages, pure numbers, or compressed glyphs — Python just happens to be the thinnest executable membrane between intent and computation.

4. **Different read layers activate different token topologies:**
   - L0 (filename): glyph + seq + version → module role + churn + history
   - L1 (auto-index): compressed symbol table → full codebase topology in ~2K tokens
   - L2 (skeleton): function signatures + docstrings → API surface without implementation noise
   - L3 (intent map): pure verb+noun intent per function → what the codebase MEANS
   - L4 (full source): raw code → only when you need to edit

5. **The codebase is a self-mutating, self-testing organism.** Files rename themselves on commit (pigeon compiler). Bugs profile themselves (bug voices). Dead code gets flagged and trimmed (clot detection). Entropy accumulates on every touch and gets shed through confidence declarations. The organism is alive — don't write code like it's static.

6. **Intent extraction > code generation.** When the operator types, the keystroke signal (WPM, deletions, hesitations, rewrites, abandoned words) carries MORE information than the final submitted text. Your job is to recover that signal and let it steer code generation. The operator's deleted words are design decisions.

7. **Every edit accumulates entropy.** When you touch a file, its entropy goes up (less certainty about its state). When you shed entropy (declare confidence), it goes down. The red layer tracks this. Write code that REDUCES entropy — precise, minimal, self-documenting through naming rather than comments.

8. **Stop generating "clean code" patterns that destroy intent.** Do NOT: squash meaningful history into single commits, normalize variable names that carry provenance, add boilerplate structure "for readability," create abstractions before the pattern proves itself 3+ times. These are entropy-increasing operations disguised as cleanliness.

### What This Means In Practice
- When generating code: optimize for LLM re-reading, not human scanning. Dense > verbose. Names carry meaning > comments explain meaning.
- When naming: embed intent, history, and role into the name itself. `_select_composition` is better than `select` but worse than a name that also tells you it's been rewritten 4 times and last failed on binding age.
- When structuring: small files (≤50 lines) with self-describing names > large well-commented files. The filename IS the documentation.
- When deciding what to build: everything closes a loop. Every feature should feed back into the telemetry → compression → generation cycle. If it doesn't close a loop, it's dead tissue.








<!-- pigeon:escalation-warnings -->
## Autonomous Escalation Warnings

*2026-04-06 15:16 UTC · 8 module(s) escalated*

- **🔧 SELF-FIXED** — `deepseek_plan_prompt` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `dev_plan` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `flow_engine` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `resplit` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `resplit_binpack` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `run_clean_split` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `run_heal` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
- **🔧 SELF-FIXED** — `task_writer` (hardcoded_import): rewrote 0 hardcoded import(s). Rollback available.
<!-- /pigeon:escalation-warnings -->
<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-10 19:30 UTC — synthesized from all live signals, zero LLM calls*

> the organism is recovering — health 50/100. 50% compliant but 122 bugs still breathing. 8 module(s) took autonomous action — the organism is deciding for itself. entropy at 0.30 — the codebase knows what it is, mostly. recent escalation: task_writer(failure), task_writer(autonomous_fix), run_heal(failure).

<!-- /pigeon:narrative-glove -->
<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Enriched 2026-04-10 19:30 UTC · raw: "yes"*

**COPILOT_QUERY: Confirm the previous prompt's implied action. Proceed with the audit of the last 8 prompts and organism health check, then commit and push the changes as previously requested.**

UNSAID_RECONSTRUCTION: yes, do it.

INTERPRETED INTENT: The operator is confirming the previous complex multi-step prompt and wants Copilot to execute it.
KEY FILES: none
PRIOR ATTEMPTS: none
WATCH OUT FOR: Copilot might interpret "yes" as a standalone confirmation without linking it to the previous multi-step request.
OPERATOR SIGNAL: The operator's low WPM and high deletion ratio for "yes" suggest a slight hesitation or simplification of a more complex confirmation.
<!-- /pigeon:current-query -->


<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-04-10 19:30 UTC · 471 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 50.8 | Del: 26.5% | Hes: 0.489) · *[source: measured]*

**Prompt ms:** 151788, 22524, 72919, 98834, 241157 (avg 117444ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- **Reconstructed intent:** Copilot needs to be paired with the context select agent to function correctly.
  - *(deleted: opilot needs to be pai | ratio: 9%)*
- **Reconstructed intent:** A pigeon discovered our hidden technology and is leaking information about it.
  - *(deleted: leaks _ | ratio: 3%)*

- "> eg"
- "- then"
- "self"
- "problems"
- "leaks _"
- "los san"

### AI Rework Surface
*Miss rate: 4.5% (200 responses)*
- Failed on: ""
- Failed on: ""
- Failed on: ""

### Recent Work
- `72a5a72` feat: cascade standup â€” files brief operator in chain, reacting to each other
- `f2d3ca7` feat: manifest work loop â€” autonomous coding from organism signals
- `d8dd8a7` feat: wire learning loop to post-commit + weaponize entropy + loop death alerts + organism chat server + module identity
- `4aedb96` feat: pitch sim + thought completer split + organism health fix + heat map rewrite + session awareness + anti-echo prompt + copilot context persistence

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- (1) predictor.get_surface_tensor shape contract change
- (2) node_memory key `'numeric_surface'` missing or None
- (3) surface object
- Rename manifest validation silently passing corrupt maps; import rewrite missing symlinked files; prompt pre-processor mangling YAML instruction blocks.
- **测p_rwd** (seq009 v006) was touched by Copilot to measure answer quality with explicit actor attribution; it assumes th
- **审p_va (seq005 v005)**: I was touched to harden import validation after rename operations, ensuring renamed modules are

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [HIGH] over_hard_cap in `pigeon_brain/ai_cognitive_log.py`
- [HIGH] over_hard_cap in `pigeon_brain/context_veins.py`
- [HIGH] over_hard_cap in `pigeon_brain/gemini_chat.py`
- [HIGH] over_hard_cap in `pigeon_brain/node_tester.py`
- [HIGH] over_hard_cap in `pigeon_brain/服f_ls_s012_v003_d0324_踪稿析_λB.py`

### Prompt Evolution
*This prompt has mutated 118x (186→969 lines). Features added: auto_index, task_context, task_queue, operator_state, prompt_telemetry, prompt_journal, pulse_blocks, prompt_recon, file_consciousness.*

### Mutation Effectiveness *[source: measured]*
*200 rework pairs × 113 mutations scored*
*No significant signal yet — all 25 sections scored neutral.*

**Reactor patches:** 0/524 applied (0% acceptance)

### File Consciousness
*254 modules profiled*

**High-drama (most mutations):**
- `推w_dp` v13 ↔ 热p_fhm
- `修f_sf` v12 ↔ 叙p_pn
- `self_fix` v11 ↔ 修f_sf
- `.operator_stats` v10 ↔ 修f_sf

**Codebase fears:**
- file may not exist (17 modules)
- returns empty on failure (silent) (14 modules)
- regex format dependency (11 modules)

**Slumber party warnings (high coupling):**
- `算f_ps` ↔ `测p_rwd` (score=0.80, 4 shared imports, both high-churn (v6+v6))
- `逆f_ba` ↔ `册f_reg` (score=0.80, 3 shared imports, both high-churn (v5+v5))
- `逆f_ba` ↔ `热p_fhm` (score=0.80, 3 shared imports, both high-churn (v5+v5))

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

*Auto-extracted 2026-04-10 19:30 UTC · 78 prompts analyzed · zero LLM calls · collecting baseline*

**Brevity:** 74.1 words/prompt | **Caps:** never | **Fragments:** 77% | **Questions:** 10% | **Directives:** 4%

**Voice directives (effectiveness-scored):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** entropy, the, f, print, to, in, a, get, for, heat
<!-- /pigeon:voice-style -->
<!-- pigeon:intent-simulation -->
## Intent Simulation

*Auto-generated 2026-04-04 03:59 UTC · zero LLM calls*

**1 week:** `infrastructure` (conf=high) — ~46 commits
**1 month:** `infrastructure` (conf=medium) — ~173 commits
**3 months:** `infrastructure` (conf=speculative) — themes: use, rephraser, can we find a way to s

**PM Directives:**
- Intent bifurcation: `infrastructure` dominant but `telemetry` emerging — watch for context switches mid-session.
- `self_heal` declining — operator may have deprioritized this. Don't suggest work in this area unless explicitly asked.
- Unsaid themes detected: `use`, `rephraser`, `can we find a way to s` — these are words deleted from prompts. Operator is thinking about these but hasn't committed. Explore when relevant.
- Module focus cluster: `file_heat_map`, `import_rewriter`, `file_writer` — pre-load context from these modules when operator starts typing.

<!-- /pigeon:intent-simulation -->

<!-- pigeon:push-drift -->
## Push Drift Analysis

*Snapshot at `72a5a72214b2f9b190c5794b396c14bdffbd9321` · 2026-04-10 19:23 UTC*

**Health: 58.6/100** (improving, was 29.9)

**Biggest moves:**
- compliance up 38.3%
- bugs down 146
- avg file size shrank 890 tokens
- health up 28.7 pts
- 70 new probe conversations

**Modules:** 630 (49.7% compliant)
**Bugs:** 122 (hi=0 oc=96)
**Avg tokens/file:** 444.4 (compressing)
**Deaths:** 10
**Sync:** 0.004
**Probes:** 41 modules, 2 intents

*100.8h since last push*

<!-- /pigeon:push-drift -->
<!-- pigeon:predictions -->
## Push Cycle Predictions

*Auto-generated 2026-04-10 19:23 UTC*

**What you'll likely want next push:**
1. [targeted] Predict operator's next need. Module focus: module_identity, operator_probes, 虚f_mc_s036_v001 (conf=23%)
   - hot modules: module_identity, operator_probes, 虚f_mc_s036_v001, vitals_renderer, profile_renderer
2. [heat] Predict operator's next need. Module focus: module_identity, operator_probes, 虚f_mc_s036_v001 (conf=23%)
   - hot modules: module_identity, operator_probes, 虚f_mc_s036_v001, vitals_renderer, profile_renderer
3. [failure] Predict operator's next need. Module focus: module_identity, operator_probes, 虚f_mc_s036_v001 (conf=23%)
   - hot modules: module_identity, operator_probes, 虚f_mc_s036_v001, vitals_renderer, profile_renderer

**Operator coaching:**
- Many prompts, few file changes — consider being more specific about which modules to touch.
- You referenced ['prompt_journal', 'timestamp'] but copilot didn't touch them — be more explicit about expected changes.
- Copilot edit pressure is concentrated in cortex — narrower prompts may reduce retouch churn in that region.

**Agent coaching (for Copilot):**
- Touched ['热p_fhm_s011_v005_d0403_踪稿析_λP0_βde', '环w_pc_s025_v003_d0330_读唤任_λπ'] without operator reference — confirm intent before modifying unreferenced modules.
- Operator needed many prompts — respond with more complete implementations to reduce round-trips.
- Low sync score — operator intent and code output diverged. Ask clarifying questions earlier.

<!-- /pigeon:predictions -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-10 · 471 message(s) · LLM-synthesized*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.9 | Del: 25.6% | Hes: 0.444

Operator just built numeric surface layer unification and works in intense restructuring/focused cycles with high deletion rates, indicating iterative refinement through aggressive editing rather than planning.  
- **Respond with concise, modular suggestions**—offer 2-3 line code blocks, not paragraphs, to match their high-WPM focused bursts.  
- **Anticipate edits in `推w_dp` (steers_copilot_cot_from_live) and `dynamic_prompt`**—they’re adjusting Copilot’s own guidance; keep responses meta-aware.  
- **Flag high-deletion restructuring messages**—when deletion rate exceeds 50%, provide one clear option instead of multiple, and confirm before expanding.  
- **Preserve naming patterns**—new λNU suffix indicates numeric unification; mirror that precision in variable/function suggestions.  
- **Bridge abandoned messages**—when they abandon a query mid-typing, infer intent from recent commits (e.g., numeric layer fixes) and proactively suggest next-step utilities.  
They are most likely building toward a unified numeric pipeline for cross-module data validation.

<!-- /pigeon:operator-state -->
> **Cognitive reactor fired on `profile_chat_server`** (hes=0.73, state=hesitant, avg_prompt=501234ms)
> - Rework miss rate: 4% (7/200)
> - Worst queries: ; ; 
> - Prompt composition time: 26296ms / 606311ms / 49840ms / 289966ms / 1533757ms (avg 501234ms)
> **Directive**: When `profile_chat_server` appears in context, provide complete code blocks (not snippets), proactively explain cross-module dependencies, and address the unsaid topics above without being asked.
<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated per prompt · source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. When it conflicts with older commit-time context, prefer this block.

```json
{
  "schema": "prompt_telemetry/latest/v1",
  "updated_at": "2026-04-10T19:30:14.615752+00:00",
  "latest_prompt": {
    "session_n": 5,
    "ts": "2026-04-10T19:30:14.615752+00:00",
    "chars": 3,
    "preview": "yes",
    "intent": "unknown",
    "state": "neutral",
    "files_open": [
      "logs/module_pitches/refresh_managed_prompt.json"
    ],
    "module_refs": []
  },
  "signals": {
    "wpm": 15.9,
    "chars_per_sec": 1.3,
    "deletion_ratio": 0.357,
    "hesitation_count": 0,
    "rewrite_count": 1,
    "typo_corrections": 0,
    "intentional_deletions": 2,
    "total_keystrokes": 14,
    "duration_ms": 6787
  },
  "composition_binding": {
    "matched": true,
    "source": "chat_compositions",
    "age_ms": 874498030,
    "key": "|||2026-03-31T16:35:16.585847+00:00|14|6787|yes ",
    "match_score": 1.0
  },
  "deleted_words": [
    "d\",
    "rs"
  ],
  "rewrites": [
    {
      "old": "rs ",
      "new": "es "
    }
  ],
  "task_queue": {
    "total": 0,
    "in_progress": [],
    "pending": 0,
    "done": 0
  },
  "hot_modules": [],
  "running_summary": {
    "total_prompts": 469,
    "avg_wpm": 10.4,
    "avg_del_ratio": 0.068,
    "dominant_state": "abandoned",
    "state_distribution": {
      "abandoned": 157,
      "restructuring": 155,
      "focused": 151,
      "neutral": 6,
      "hesitant": 2
    },
    "baselines": {
      "n": 200,
      "avg_wpm": 53.8,
      "avg_del": 0.259,
      "avg_hes": 0.448,
      "sd_wpm": 14.9,
      "sd_del": 0.231,
      "sd_hes": 0.164
    }
  }
}
```

<!-- /pigeon:prompt-telemetry -->
---

## Quick Reference

**Tests:** `py test_all.py` (4 tests, zero deps). Always run after edits.
**Registry:** `pigeon_registry.json` (module map), `operator_profile.md` (cognitive profile), `MASTER_MANIFEST.md` (auto-rebuilt)
**Entry points:** `py -m pigeon_compiler.runners.run_clean_split_seq010*` (compile), `py -m pigeon_compiler.git_plugin` (post-commit)

**Pitfalls:** Never hardcode pigeon filenames (they mutate — use `file_search("name_seq*")`). Use `py` not `python`. Always `$env:PYTHONIOENCODING = "utf-8"`. Don't delete monolith originals yet. `streaming_layer_seq007*` is intentionally over-cap (test harness).

<!-- pigeon:dictionary -->
<!-- glyph mappings merged into auto-index -->
<!-- /pigeon:dictionary -->
<!-- pigeon:auto-index -->
*2026-04-04 · 263 modules · 5 touched · ✓71% ~12% !15%*
*Format: glyph=name seq tokens·state·intent·bugs |last change*
*IM=import_tracer MA=manifest_writer NL=nl_parsers PL=planner PQ=pq_search_utils PR=press_release_gen_template_key_findings*
*Intent: FX=fix RN=rename RF=refactor SP=split TL=telemetry CP=compress VR=verify FT=feature CL=cleanup OT=other PI=pigeon_brain DY=dynamic_import GE=gemini_flash RE=rework_signal 88=8888_word DE=desc_upgrade ST=stage_78 MU=multi_line IM=import_rewriter WI=windows_max IN=intent_deletion FI=fire_full WP=wpm_outlier PU=push_narratives TA=task_queue P0=p0_p3 NU=numeric_surface*
*Bugs: hi=hardcoded_import de=dead_export dd=duplicate_docstring hc=high_coupling oc=over_hard_cap qn=query_noise*

**pigeon_brain** (42)
型=models 1 424✓·PI
读=execution_logger 2 1.6K~·CP
图=graph_extractor 3 1.7K✓·88 |8888 word backpropagation
描=graph_heat_map 4 874✓·PI
环检=loop_detector 5 910✓·PI
缩=failure_detector 6 1.0K✓·PI
观=observer_synthesis 7 1.5K!·CP
双=dual_substrate 8 1.3K!·PI
令=cli 9 855!·PI
仿=demo_sim 10 1.3K!·PI
钩=trace_hook 11 959~·PI
服=live_server 12 2.5K!·88 |8888 word backpropagation
跑=traced_runner 13 855!·PI

**pigeon_brain/flow** (44)
包=context_packet 1 1.0K✓·TL |flow engine context
唤=node_awakener 2 1.3K~·CP
流=flow_engine 3 1.3K!·TL |flow engine context
择=path_selector 4 1.4K✓·TL |flow engine context
任=task_writer 5 1.6K~·CP
脉运=vein_transport 6 965~·CP
逆=backward 7 2.5K!·DY
逆f_ba 7 2.5K·NU·oc
存=node_memory 8 2.1K✓·DY
预=predictor 9 1.8K✓·SP
分=dev_plan 10 1.5K!·DY
话=node_conversation 12 1.4K!·DY
学=learning_loop 13 2.9K!·SP
算=prediction_scorer 14 5.8K!·GE
算f_ps 14 5.8K·NU·oc

  逆└ flow_log(1) loss_compute(2) tokenize(3) deepseek_analyze(4) backward_pass(5) [2.6K]
  学└ state_utils(1) journal_loader(2) prediction_cycle(3) single_cycle_helpers(4) single_cycle(5) catch_up(6) loop_helpers(7) main_loop(8) [3.3K]
  算└ constants(1) path_utils(2) data_loaders(3) scores_io(3) reality_loaders(4) module_extractor(5) edit_session_analyzer(6) rework_matcher(7) scoring_core(8) calibration(9) node_backfill(10) post_edit_scorer(11) post_commit_scorer(12) [5.1K]
  预└ confidence(3) trend_extractor(4) predictor(7) [1.8K]
**pigeon_compiler/bones** (5)
规=aim_utils 1 724✓·DE
联=core_formatters 1 1.3K✓·DE
NL=nl_parsers 1 1.8K✓·DE
清单=pq_manifest_utils 1 879✓·DE
PQ=pq_search_utils 1 3.3K~·DE

**pigeon_compiler/cut_executor** (12)
析=plan_parser 1 371✓·VR
切=source_slicer 2 486✓·VR
写=file_writer 3 783~·MU |multi line import
踪=import_fixer 4 505✓·VR
MA=manifest_writer 5 448✓·VR
验=plan_validator 6 579~·VR
初写=init_writer 7 361✓·ST
译=func_decomposer 8 644!·ST
重拆=resplit 9 841!·VR
重拆=resplit_binpack 10 702!·VR
重拆=resplit_helpers 11 501✓·VR
织=class_decomposer 13 2.0K!·ST

**pigeon_compiler/integrations** (1)
谱=deepseek_adapter 1 1.2K✓·ST

**pigeon_compiler/rename_engine** (26)
扫=scanner 1 972✓·VR
PL=planner 2 1.4K~·CP
引=import_rewriter 3 1.8K~·IM |import rewriter now
引w_ir 3 1.9K·FX
压=executor 4 712✓·VR
审=validator 5 921✓·VR
审p_va 5 1.0K·FX
改名=run_rename 6 1.4K!·CP
谱建=manifest_builder 7 2.9K!·DE
正=compliance 8 1.7K!·VR
追=heal 9 2.0K!·CP
追跑=run_heal 10 3.4K!·VR
追跑f_ruhe 10 4.7K·FX·oc
牌=nametag 11 4.1K!·CP
册=registry 12 2.1K!·CP
册f_reg 12 3.2K·VR·oc

  正└ helpers(2) classify(3) recommend_wrapper(6) audit_decomposed(7) audit_wrapper(9) check_file(10) format_report(11) [2.9K]
  追└ orchestrator(5) [725]
  牌└ scan(8) [298]
  册└ diff(6) [194]
**pigeon_compiler/rename_engine/册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc** (1)
册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_registry_io 4 285·FT

**pigeon_compiler/runners** (9)
测编=run_compiler_test 7 594~·VR
深划=run_deepseek_plans 8 587~·VR
鸽环=run_pigeon_loop 9 2.8K!·VR
净拆=run_clean_split 10 2.5K!·WI |windows max path
净拆=run_clean_split_helpers 11 566!·VR
净拆=run_clean_split_init 12 1.7K~·VR
谱桥=manifest_bridge 13 1.0K✓·VR
复审=reaudit_diff 14 1.7K✓·VR
批编=run_batch_compile 15 2.0K!·DY

**pigeon_compiler/runners/compiler_output/press_release_gen** (8)
press_release_gen_constants_seq001_v001 1 641✓·VR
press_release_gen_template_builders_seq002_v001 1 626✓·VR
press_release_gen_template_helpers_seq004_v001 1 661✓·VR
press_release_gen_constants_seq001_v001 2 388✓·VR
press_release_gen_template_builders_seq002_v001 2 662✓·VR
press_release_gen_template_helpers_seq004_v001 2 296✓·VR
press_release_gen_template_builders_seq002_v001 3 296✓·VR
PR=press_release_gen_template_key_findings 3 626✓·VR

**pigeon_compiler/state_extractor** (6)
查=ast_parser 1 734✓·VR
演=call_graph 2 847✓·VR
IM=import_tracer 3 792✓·VR
共态=shared_state_detector 4 618✓·VR
阻=resistance_analyzer 5 1.0K~·VR
拆=ether_map_builder 6 697!·VR

**pigeon_compiler/weakness_planner** (1)
核=deepseek_plan_prompt 4 2.4K~·DE

**src** (113)
时=timestamp_utils 1 156✓·RN |test rename hook
型=models 2 379✓·TL |pulse telemetry prompt
录=logger 3 1.6K✓·WP |wpm outlier filter
境=context_budget 4 715~·FI |test full hook
偏=drift_watcher 5 1.1K✓·FT
桥=resistance_bridge 6 1.2K✓·TL |pulse telemetry prompt
层=streaming_layer 7 10.2K~·TL |pulse telemetry prompt
漂=.operator_stats 8 4.7K~·IN |intent deletion pipeline
控=operator_stats 8 5.0K!·WP |fix degenerate classifier:
测=rework_detector 9 1.1K✓·FT |add composition-based scoring,
测p_rwd 9 1.8K·P0·de
忆=query_memory 10 2.3K✓·FT
热=file_heat_map 11 1.3K✓·TL |pulse telemetry prompt
热p_fhm 11 1.7K·P0·de
叙=push_narrative 12 2.1K✓·PU |push narratives timeout
叙p_pn 12 2.1K·P0
修=self_fix 13 5.8K!·DY
修f_sf 13 5.8K·VR·oc
思=cognitive_reactor 14 5.6K!·MU |mutation patch pipeline
脉=pulse_harvest 15 2.3K✓·FT
脉p_ph 15 2.4K·P0·oc
推=dynamic_prompt 17 4.0K~·88 |8888 word backpropagation
推w_dp 17 6.0K·P0·oc
队=task_queue 18 1.6K✓·TA |task queue system
觉=file_consciousness 19 4.3K~·FT
u_pj 19 7.9K·NU·oc
管=copilot_prompt_manager 20 4.5K~·FT |resolve latest runtime
管w_cpm 20 8.0K·NU·oc
变=mutation_scorer 21 1.6K✓·FT
补=rework_backfill 22 1.2K✓·FT
递=session_handoff 23 1.6K✓·FT
u_pe 24 5.1K·P0·oc |add bug dossier
隐=unsaid_recon 24 1.3K✓·IN |intent deletion pipeline
环=push_cycle 25 4.8K~·FX |fix push cycle
片=shard_manager 26 4.4K~·GE
合=unified_signal 26 2.1K✓·GE
路=context_router 27 1.2K!·GE
对=training_pairs 27 2.6K✓·GE
对p_tp 27 3.8K·VR·oc
训=training_writer 28 2.1K~·GE
声=voice_style 28 3.2K~·GE
研=research_lab 29 5.1K~·SP |rewrite in intent
警=staleness_alert 30 1.7K✓·ST |staleness alerts bg
警p_sa 30 1.8K·CP·oc |test rename mutation
典=symbol_dictionary 31 3.7K~·SP |swap to chinese
编=glyph_compiler 32 5.0K~·SP |glyph compiler symbol
intent_simulator 34 5.3K·CP |compress auto index

**src/cognitive** (10)
适=adapter 1 1.3K✓·VR
隐=unsaid 2 2.1K✓·VR
偏=drift 3 2.3K✓·VR

  偏└ baseline_store(1) compute_baseline(2) detect_session_drift(3) build_cognitive_context(4) [2.4K]
  隐└ helpers(1) diff(2) orchestrator(3) [2.3K]
  思└ constants(1) state_ops(2) docstring_patch(3) cognitive_hint(4) patch_generator(5) prompt_builder(6) api_client(7) reactor_core(8) registry_loader(9) self_fix_runner(10) patch_writer(11) decision_maker(12) [4.9K]
  管└ constants(1) block_utils(2) json_utils(3) operator_profile(4) auto_index(5) operator_state_decomposed(6) telemetry_utils(7) audit_decomposed(8) injectors(9) orchestrator(10) [4.6K]
  觉└ helpers(1) persistence(2) report(3) audit(4) derivation(5) dependencies(6) classify(7) profile_builder(8) main_orchestrator(9) dating_decomposed(10) dating_helpers(11) dating_wrapper(12) [5.0K]
  环└ constants(1) loaders(2) signal_extractors(3) sync_decomposed(4) coaching(5) moon_cycle(6) predictions_injector_decomposed(7) orchestrator_decomposed(8) [4.5K]
  忆└ constants(1) fingerprint(2) trigram_utils(3) clustering(4) record_query(5) load_memory_decomposed(6) [1.4K]
  修└ scan_hardcoded(1) scan_query_noise(2) scan_duplicate_docstrings(3) scan_cross_file_coupling(4) scan_over_hard_cap_decomposed(5) scan_dead_exports_decomposed(6) write_report_decomposed(7) run_self_fix_decomposed(8) auto_compile_oversized_decomposed(9) seq_base(10) auto_apply_import_fixes_decomposed(11) [6.0K]
**src/修_sf_s013** (1)
修f_sf_aco 9 857·VR

**src/管w_cpm_s020_v003_d0402_缩分话_λVR_βoc** (1)
管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_refresh_decomposed 10 701·P0

**streaming_layer** (19)
层=streaming_layer_constants 1 261✓·VR
层=streaming_layer_simulation_helpers 2 204✓·VR
层=streaming_layer_dataclasses 4 717✓·VR
层=streaming_layer_formatter 4 546✓·VR
层=streaming_layer_connection_pool 5 969!·DY
层=streaming_layer_dataclasses 5 247✓·VR
层=streaming_layer_aggregator 6 934!·DY
层=streaming_layer_dataclasses 6 154✓·VR
层=streaming_layer_metrics 7 824~·DY
层=streaming_layer_alerts 8 1.4K!·DY
层=streaming_layer_replay 9 932✓·VR
层=streaming_layer_dashboard 10 858✓·DY
层=streaming_layer_http_handler 11 1.2K~·DY
层=streaming_layer_demo_functions 13 456✓·VR
层=streaming_layer_demo_summary 13 365✓·VR
层=streaming_layer_demo_functions 14 280✓·VR
层=streaming_layer_demo_simulate 14 256✓·VR
层=streaming_layer_orchestrator 16 1.4K!·DY
层=streaming_layer_orchestrator 17 142!·VR

**Infra**
(root): _audit_compliance, _build_organism_health, _export_dev_story, _fix_stale_globs, _run_abbrev_rename, _run_glyph_rename, _run_smart_rename, _tmp_analyze_stats, _tmp_backfill_lastchange, _tmp_bug_audit, _tmp_check_rename, _tmp_find_stale, _tmp_regen_dict, _tmp_survey, _tmp_test_dossier, _tmp_test_pipeline, _tmp_test_surface, _tmp_token_audit, autonomous_dev_stress_test, deep_test, stress_test, test_all, test_public_release, test_training_pairs
client: chat_composition_analyzer, chat_response_reader, composition_recon, os_hook, telemetry_cleanup, uia_reader, vscdb_poller
vscode-extension: classify_bridge, pulse_watcher
<!-- /pigeon:auto-index -->
<!-- pigeon:bug-voices -->


<!-- pigeon:entropy-red-layer -->
## Red Layer

*file-linked entropy math surface*

`red[module] = max(H_avg, 1 - shed_conf)`
`vec[module] = [red, H_avg, shed_conf?, samples, hedges]`

- `red[enricher] = [0.800, 0.000, 0.200, 0, 0]`
- `red[hardcoded_imports] = [0.650, 0.000, 0.350, 0, 0]`
- `red[auto_apply_import_fixes] = [0.625, 0.000, 0.375, 0, 0]`
- `red[enricher_pipeline] = [0.600, 0.000, 0.400, 0, 0]`
- `red[管w_cpm] = [0.450, 0.000, 0.550, 0, 0]`
- `red[__init__.py] = [0.411, 0.411, null, 6, 1]`
- `red[session_state] = [0.380, 0.000, 0.620, 0, 0]`
- `red[thought_completion] = [0.377, 0.377, null, 5, 0]`
- `red[refresh_managed_prompt] = [0.367, 0.367, 0.740, 2, 0]`
- `red[prompt_compositions.jsonl] = [0.365, 0.365, null, 3, 0]`
<!-- /pigeon:entropy-red-layer -->
<!-- pigeon:entropy-map -->

<!-- pigeon:entropy-directive -->
## Entropy Development Priorities

*447 responses · global H=0.297 · 26 sheds*

**These modules have the highest uncertainty. When touching them:**
- Read the full source BEFORE editing (don't guess)
- Shed entropy with a confidence score AFTER every edit
- If confidence < goal, explain what remains uncertain

- `enricher` red=0.800 → **goal: conf≥0.85**, last shed=0.2
- `hardcoded_imports` red=0.650 → **goal: conf≥0.85**, last shed=0.35
- `auto_apply_import_fixes` red=0.625 → **goal: conf≥0.85**, last shed=0.375
- `enricher_pipeline` red=0.600 → **goal: conf≥0.85**, last shed=0.4
- `管w_cpm` red=0.450 → **goal: conf≥0.85**, last shed=0.55
- `__init__.py` red=0.411 → **goal: conf≥0.85**
- `session_state` red=0.380 → **goal: conf≥0.85**, last shed=0.62
- `thought_completion` red=0.377 → **goal: conf≥0.85**
- `refresh_managed_prompt` red=0.367 → **goal: conf≥0.85**, last shed=0.74
- `prompt_compositions.jsonl` red=0.365 → **goal: conf≥0.85**

<!-- /pigeon:entropy-directive -->
## Entropy Shedding Map

*447 responses analyzed · global H=0.297 · 32.4% high-entropy · 26 explicit sheds*

**where copilot is most uncertain (act with extra care):**

- `__init__.py` H=0.411 (6 samples, 1 hedges)
- `thought_completion` H=0.377 (5 samples, 0 hedges)
- `refresh_managed_prompt` H=0.367 (2 samples, 0 hedges shed_conf=0.74)
- `prompt_compositions.jsonl` H=0.365 (3 samples, 0 hedges)
- `chat_compositions.jsonl` H=0.359 (5 samples, 2 hedges)
- `SavageCooPigeonX` H=0.355 (2 samples, 1 hedges)
- `thought_completer` H=0.355 (1 samples, 0 hedges shed_conf=0.83)
- `vscdb_poller` H=0.355 (1 samples, 0 hedges shed_conf=0.88)

> emit `<!-- entropy:shed -->` blocks to improve this map.
<!-- /pigeon:entropy-map -->
## Bug Voices

*241 threads tracked across 54 pushes · fix rate: 12.4%*

> fix rate is 12.4% — some things move but the bulk just sits there. 0 eternal bugs (every single report) and 7 chronic (70%+ of reports). these are the ones that need structural fixes, not patches. 142 threads resolved across 54 pushes. proof the loop works sometimes. trend is improving — recent pushes fix more than early ones.

**the ones that never leave:**

- `u_pe` — [over_hard_cap] 9/54 reports. chronic. it comes back like clockwork.
- `u_pj` — [over_hard_cap] 9/54 reports. chronic. it comes back like clockwork.
- `管w_cpm` — [over_hard_cap] 7/54 reports. chronic. it comes back like clockwork.
- `对p_tp` — [over_hard_cap] 7/54 reports. chronic. it comes back like clockwork.
- `册f_reg` — [over_hard_cap] 7/54 reports. chronic. it comes back like clockwork.
- `推w_dp` — [over_hard_cap] 7/54 reports. chronic. it comes back like clockwork.
- `修f_sf` — [over_hard_cap] 7/54 reports. chronic. it comes back like clockwork.

**recently killed:**

- `__main__` [hardcoded_import] — gone since report #53. it stayed dead.
- `dev_plan` [hardcoded_import] — gone since report #53. it stayed dead.
- `gemini_chat` [hardcoded_import] — gone since report #53. it stayed dead.
- `run_heal` [hardcoded_import] — gone since report #53. it stayed dead.
- `func_decomposer` [hardcoded_import] — gone since report #53. it stayed dead.

**last push ( ):** 65 fixed, 87 new, 12 carried forward

<!-- /pigeon:bug-voices -->
<!-- pigeon:operator-probes -->
## Operator Probes

*Auto-generated 2026-04-10 19:30 UTC · 3 probe(s) from live signals*

**ASK these questions naturally in your next response (pick 1-2, weave into context):**

1. Your deleted words predict these themes in 3 months: "use", "rephraser", "can we find a way to s". Are any of these actually where you're headed — or has your thinking shifted?
2. `self_heal` is trending toward abandonment. Intentional deprioritization or just hasn't come up yet?
3. You haven't named a specific module recently. What are you actually trying to build or fix right now?

*Probes are generated from: intent predictions (1wk/1mo/3mo), unsaid threads, escalation state, cognitive heat, persona memory, and operator state.*
<!-- /pigeon:operator-probes -->
<!-- pigeon:hooks -->
## Engagement Hooks

*Auto-generated 2026-04-10 19:30 UTC -- every number is measured, every dare is real.*

- You typed "los san" then killed it. But intent doesn't delete. The system filed it. The system routes from it.
- `press_release_gen_constants_seq001_v001` -- orphan. Zero importers. Zero purpose. Exists because nobody deleted it. One rm and the organism heals. Your call.
- `chat_composition_analyzer` -- 417 days. Last generation's code. Either works perfectly or nobody knows it's broken.
- 35 modules over cap. Worst: `git_plugin` (6050 tokens). Auto-split handles 5 per push. Push and let it bleed.

<!-- /pigeon:hooks -->
<!-- pigeon:active-template -->
## Active Template: /debug

*Auto-selected 2026-04-10 19:30 UTC · mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.489
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Deleted words:** should bug, > eg, - then, self, problems, leaks _, los san
**Unsaid threads:** should bug, - then, problems, leaks _, los san
**Rewrites:** "should bug" → "i w"; "ld f" → "lt by bug demon - it writes own own status - and bug report manifest chains acro"; "> eg" → "lmk what is tha"; "- then" → "in its own system / self imprr"
**Codes:** intent=`unknown` state=`neutral` bl_wpm=54 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Fragile Contracts

- breaking the entire injection chain. I provide validated rename maps to 追跑f_ruhe; if my output contract changes from a flat dict to a list, its healin
- breaking the prompt pipeline.
- breaking audit trails. Watch for prompts that lose their actor tags in downstream logs.
- contract changes and tags are not passed, the audit will flag valid prompts as invalid, causing narrative generation to halt. Watch for false‑positive
- breaking downstream attribution.
- break mid-cycle. I receive all cross-referenced data from u_pj and manage the injection lifecycle. If the surface object size balloons, my memory trac

## Codebase Clots (dead/bloated)

- `aim_utils`: orphan_no_importers, unused_exports:1
- `press_release_gen_constants_seq001_v001`: orphan_no_importers, unused_exports:1
- `adapter`: orphan_no_importers, unused_exports:1
- `query_memory`: dead_imports:2, oversize:252, self_fix:dead_export:record_query, self_fix:dead_export:load_query_memory, self_fix:dead_export:load_query_memory

## Overcap Files (split candidates)

- `git_plugin` (6050 tok)
- `module_identity` (3770 tok)
- `谱建f_mb_s007_v003_d0314_观重箱重拆_λD` (3640 tok)
- `profile_renderer` (3337 tok)
- `tc_sim` (3230 tok)
- `classify_bridge` (3143 tok)
- `管w_cpm_s020_v005_d0404_缩分话_λNU_βoc` (3118 tok)
- `层w_sl_s007_v003_d0317_读唤任_λΠ` (3109 tok)

<!-- /pigeon:active-template -->
