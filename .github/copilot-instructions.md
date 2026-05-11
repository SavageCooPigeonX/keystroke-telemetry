

---

<!-- pigeon:staleness-alert -->
## Staleness Alert

*Checked 2026-05-10T21:09:25.297249+00:00 - Codex live context refreshed*

**Live replacements active:** `pigeon:current-query`, `pigeon:prompt-telemetry`, `codex:dynamic-context-pack`, DeepSeek V4 prompt queue.

**Legacy stale blocks still reported:** organism-health, task-queue, operator-state

**Rule:** Prefer the Codex live blocks below over older commit-time or daemon-time sections.
<!-- /pigeon:staleness-alert -->

---

<!-- codex:manifest-execution-contract -->
## Manifest Execution Contract

Before Codex/Copilot executes code work, it must read manifest state:

- read `logs/prompt_context_packet_latest.json`
- read `logs/copilot_prompt_box_latest.md`
- read `MANIFEST.md`
- read every selected folder manifest listed in `manifest_state_protocol.read_set`

Execution is cleared only when `manifest_state_protocol.status` is `manifest_context_loaded`.

Hard cannon gate:

- before code work, `logs/opus_micro_pulse_latest.json` must exist
- before code work, `logs/prompt_cannon_job_latest.json` must exist
- before code work, `logs/opus_executor_prompt_latest.md` must exist and be treated as the primary prompt
- before code work, `logs/cannon_execution_gate_latest.json` must report `status=cleared`
- if the cannon gate is missing, blocked, stale, or hash-mismatched, stop and run `py scripts/build_prompt_context_packet.py --source codex` or `py scripts/check_cannon_gate.py --prompt "<operator prompt>"`
- Codex/Copilot is not allowed to start mutation work from a cold prompt; Opus micro-pulse must first produce the cannon payload
- Raw operator prompts are fallback evidence only after the generated Opus executor prompt is loaded.

State storage is unified markdown:

- root `MANIFEST.md` is the master persistent project state and project-structure index
- each folder writes one local `MANIFEST.md`
- file-sim state, learned syntax triggers, local intent queues, and local write queues belong in that folder's `MANIFEST.md`
- logs are evidence trails; manifests are the inspectable state surface

Opus/master manifest manages master intent keys across folder manifests. Prompt intent is shattered into `shattered_intent_keys`, numerically encoded, then matched to files through context selection, syntax triggers, and file sim orchestration.

Files may write learned state only to their own folder `MANIFEST.md`. Files may read other selected folder manifests during cross-folder simulation, but cross-folder reads do not grant cross-folder write authority.
<!-- /codex:manifest-execution-contract -->

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---

---
<!-- pigeon:bug-voices -->


<!-- pigeon:entropy-red-layer -->
## Red Layer

*file-linked entropy math surface*

`red[module] = max(H_avg, 1 - shed_conf)`
`vec[module] = [red, H_avg, shed_conf?, samples, hedges]`

- `red[enricher] = [0.560, 0.000, 0.200, 0, 0]`
- `red[hardcoded_imports] = [0.455, 0.000, 0.350, 0, 0]`
- `red[auto_apply_import_fixes] = [0.438, 0.000, 0.375, 0, 0]`
- `red[context_router] = [0.428, 0.428, null, 2, 0]`
- `red[engagement_hooks] = [0.428, 0.428, null, 2, 0]`
- `red[glyph_compiler] = [0.428, 0.428, null, 3, 0]`
- `red[operator_probes] = [0.428, 0.428, null, 2, 0]`
- `red[prompt_enricher] = [0.428, 0.428, null, 4, 0]`
- `red[research_lab] = [0.428, 0.428, null, 4, 0]`
- `red[shard_manager] = [0.428, 0.428, null, 2, 0]`
<!-- /pigeon:entropy-red-layer -->
<!-- pigeon:entropy-map -->

<!-- pigeon:entropy-directive -->
## Entropy Development Priorities

*822 responses · global H=0.298 · 79 sheds*

**These modules have the highest uncertainty. When touching them:**
- Read the full source BEFORE editing (don't guess)
- Shed entropy with a confidence score AFTER every edit
- If confidence < goal, explain what remains uncertain

- `enricher` red=0.560 → **goal: conf≥0.85**, last shed=0.2
- `hardcoded_imports` red=0.455 → **goal: conf≥0.85**, last shed=0.35
- `auto_apply_import_fixes` red=0.438 → **goal: conf≥0.85**, last shed=0.375
- `context_router` red=0.428 → **goal: conf≥0.85**
- `engagement_hooks` red=0.428 → **goal: conf≥0.85**
- `glyph_compiler` red=0.428 → **goal: conf≥0.85**
- `operator_probes` red=0.428 → **goal: conf≥0.85**
- `prompt_enricher` red=0.428 → **goal: conf≥0.85**
- `research_lab` red=0.428 → **goal: conf≥0.85**
- `shard_manager` red=0.428 → **goal: conf≥0.85**

<!-- /pigeon:entropy-directive -->
## Entropy Shedding Map

*822 responses analyzed · global H=0.298 · 33.7% high-entropy · 79 explicit sheds*

**where copilot is most uncertain (act with extra care):**

- `prompt_enricher` H=0.428 (4 samples, 0 hedges)
- `shard_manager` H=0.428 (2 samples, 0 hedges)
- `context_router` H=0.428 (2 samples, 0 hedges)
- `research_lab` H=0.428 (4 samples, 0 hedges)
- `glyph_compiler` H=0.428 (3 samples, 0 hedges)
- `警p_sa` H=0.428 (2 samples, 0 hedges)
- `engagement_hooks` H=0.428 (2 samples, 0 hedges)
- `operator_probes` H=0.428 (2 samples, 0 hedges)

**recently shed (this session):**
- `push_cycle` red=0.248 conf=0.80
- `tc_context_agent` red=0.207 conf=0.82
- `dynamic_prompt` red=0.172 conf=0.88
- `intent_numeric` red=0.143 conf=0.92
- `entropy_shedding` red=0.095 conf=0.90

> emit `<!-- entropy:shed -->` blocks to improve this map.
<!-- /pigeon:entropy-map -->
## Bug Voices

*302 threads tracked across 68 pushes · fix rate: 15.2%*

> fix rate is 15.2% — decent churn. bugs are dying and being born. 0 eternal bugs (every single report) and 1 chronic (70%+ of reports). these are the ones that need structural fixes, not patches. 284 threads resolved across 68 pushes. proof the loop works sometimes. trend is improving — recent pushes fix more than early ones.

**the ones that never leave:**

- `w_gpmo` — [over_hard_cap] 9/68 reports. chronic. it comes back like clockwork.

**recently killed:**

- `tc_gemini` [high_coupling] — gone since report #66. it stayed dead.
- `test_numeric_surface_normalization` [hardcoded_import] — gone since report #66. it stayed dead.
- `_seed_intent_numeric` [hardcoded_import] — gone since report #66. it stayed dead.
- `stress_test_architecture` [hardcoded_import] — gone since report #66. it stayed dead.
- `thought_completer` [hardcoded_import] — gone since report #66. it stayed dead.

**last push (2026-04-21 f9a3310):** 0 fixed, 17 new, 1 carried forward

<!-- /pigeon:bug-voices -->
<!-- pigeon:operator-probes -->
## Operator Probes

*Auto-generated 2026-04-22 05:37 UTC · 3 probe(s) from live signals*

**ASK these questions naturally in your next response (pick 1-2, weave into context):**

1. Your deleted words predict these themes in 3 months: "gggrararadddeeerrr", "ttt", "000". Are any of these actually where you're headed — or has your thinking shifted?
2. `unclassified` is trending toward abandonment. Intentional deprioritization or just hasn't come up yet?
3. You haven't named a specific module recently. What are you actually trying to build or fix right now?

*Probes are generated from: intent predictions (1wk/1mo/3mo), unsaid threads, escalation state, cognitive heat, persona memory, and operator state.*
<!-- /pigeon:operator-probes -->
<!-- pigeon:hooks -->
## Engagement Hooks

*Auto-generated 2026-04-22 06:35 UTC -- every number is measured, every dare is real.*

- You were also gonna say: "the drift watcher should track module renames after pigeon splits". That thought didn't delete. It filed itself. Name it or I will.
- `p_gpip` -- 417 days. Last generation's code. Either works perfectly or nobody knows it's broken.
- `intent_numeric` has 4 unresolved `oc/de` marks. Every push it survives makes the next fix harder.
- `tc_sim_engine` v4: "I carry the oc curse. Fix me and the beta falls off my name. Leave me and it scars deeper."

<!-- /pigeon:hooks -->
<!-- pigeon:active-template -->
## Active Template: /debug

*Auto-selected 2026-04-22 05:37 UTC · mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`unknown` bl_wpm=52 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Known Issues (from self-fix scanner)

- [CRITICAL] hardcoded_import in `scripts/bug_probe_hardcoded_import.py`
- [CRITICAL] hardcoded_import in `scripts/verify_loop_2.py`

## Fragile Contracts

- contracts. If a renamed module’s function signature changed silently, my imports will break at runtime.
- contract breaks, my API calls may send invalid parameters.
- contract, import statements in all renamed dependents, test suite import failures. This push standardizes the core word-number mapping filename across
- assumption breaks—for instance, if downstream consumers expect the old module name in dynamic imports—the entire import chain will fail silently. Watc
- contract with the pigeon registry’s naming schema; if that schema changes or the compiler’s extraction heuristic misinterprets the rename as a split, 
- assumption is that the orchestrator fires on every state change; if the daemon's event emission is throttled or batched, I may miss transitions. Watch

## Codebase Clots (dead/bloated)

- `classify_bridge`: orphan_no_importers, unused_exports:1, oversize:877
- `逆f_ba_bp_s005_v003_d0328_λR`: orphan_no_importers, unused_exports:1
- `学f_ll_cu_s006_v003_d0327_λγ`: orphan_no_importers, unused_exports:1
- `算f_ps_ca_s009_v002_d0327_λS`: orphan_no_importers, unused_exports:1
- `预p_pr_co_s001_v001`: orphan_no_importers, unused_exports:1

## Overcap Files (split candidates)

- `tc_sim` (14095 tok)
- `tc_gemini` (11314 tok)
- `tc_observatory` (11262 tok)
- `u_pj` (10995 tok)
- `tc_popup` (6993 tok)
- `w_gpmo` (6982 tok)
- `w_gpmo` (6980 tok)
- `tc_popup` (6892 tok)

## Active Bug Dossier

**Focus modules:** micro_sim_engine_prompt_file, word_number_file_mapping_for, picks_relevant_source_files_based, gemini_api_call_system_prompt, intent_simulation_on_typing_pause
**Focus bugs:** de, oc

<!-- /pigeon:active-template -->

---

<!-- pigeon:narrative-glove -->
## Organism Consciousness

*2026-04-22 05:37 UTC — synthesized from all live signals, zero LLM calls*

> the organism is sick — health 0/100. only 0% compliant, 0 bugs across 0 modules. entropy at 0.30 — the codebase knows what it is, mostly.

<!-- /pigeon:narrative-glove -->
<!-- pigeon:current-query -->
## What You Actually Mean Right Now

*Assembled 2026-05-10 21:21 UTC · context_select_agent · zero LLM calls*

**INTENT KEYS:** `its still bot selecting files / writing file comments when i talk to codexes about linkrouter ai repo - why -`

**FILES:** tc_intent_file_memory, maif_auditor_tests_manifest, maif_auditor_examples_manifest, tc_intent_keys, maif_auditor_maif_auditor_manifest

**STALE BLOCKS:** current-query, organism-health, task-queue, operator-state, prompt-telemetry

**DELETED WORDS (reconstructed):** 2 intentional deletion(s) (5% of keystrokes)

**UNSAID_RECONSTRUCTION:** stress test prompt lifecycle emails stale date audit os hook path... (also considered: dragonfruit)
<!-- /pigeon:current-query -->
<!-- pigeon:intent-backlog -->
## Intent Backlog Verification

*Strict verification over last 100 operator prompts*

**Status:** BLOCKED — 13 unresolved intent(s) remain.
**Directive:** Keep working. Do not treat the task as complete while this backlog is non-zero.
**Verification:** scanned=22 | created=4 | reopened=0 | verified=0 | resolved=0
**Rule:** An intent counts as done only when recent file activity clears it or the synced backlog task is verified done.

**Resolution Artifact:** `intent_backlog_resolutions.json`

### Unresolved
- [abandoned] `tq-001` conf=0.59 | submit Codex edits, make deletion analytics work here, and push the handoff to i... (also consid
  → refs: none | reason: high_deletion_ratio
- [abandoned] `tq-002` conf=0.65 | test numeric prompt encoding per query and decide repo focus around file intent ... (also consid
  → refs: none | reason: high_deletion_ratio
- [partial] `tq-003` conf=0.73 | capture deletion inject before prompt reaches model... (also considered: deletion thought raw de
  → refs: none | reason: deleted_words_left_unresolved
- [partial] `tq-004` conf=0.79 | hesitation should trigger thought completer before copilot prompt handoff... (also considered: h
  → refs: none | reason: deleted_words_left_unresolved
- [abandoned] `tq-005` conf=0.56 | capture deletion and inject dynamic state before Copilot prompt handoff... (also considered: del
  → refs: none | reason: high_deletion_ratio
- [abandoned] `tq-006` conf=0.67 | use thought completer popup as the place to write prompts so injection happens b... (also consid
  → refs: none | reason: high_deletion_ratio
- [abandoned] `tq-007` conf=0.63 | launch thought completer composer paired with observatory, keep it always front,... (also consid
  → refs: none | reason: high_deletion_ratio
- [partial] `tq-008` conf=0.79 | thought completer composer should fire on pause with cooldown and separate rewar... (also consid
  → refs: none | reason: deleted_words_left_unresolved

<!-- /pigeon:intent-backlog -->

<!-- pigeon:organism-health -->
## Organism Health

*Auto-injected 2026-05-02 21:11 UTC · 1624 files · 1461/1624 compliant (90%)*

**Stale pipelines:**
- **paste_events**: 2d ago 🔴
- **context_veins_seq001_v001**: 2d ago 🔴
- **execution_deaths**: MISSING
- **push_cycle_state**: MISSING

**Over-cap critical (72):** `codex_compat.py` (2634), `file_email_plugin_seq001_v001.py` (2361), `file_self_sim_learning_seq001_v001.py` (1900), `tc_observatory_seq001_v002_d0420__primar` (1745), `batch_rewrite_sim_seq001_v001.py` (1609), `tc_profile_seq001_v001.py` (1592), `irt_field_profile_seq001_v001.py` (1394), `tc_sim_seq001_v002_d0420__replay_typed_s` (1355)

**Clots:** `p_tcsr` (isolated, dead_imports:3), `context_select_agent` (orphan_no_importers, dead_imports:1), `p_tcm` (isolated, unused_exports:1), `p_gpip` (orphan_no_importers, unused_exports:1), `file_sim` (dead_imports:3, oversize:1344)

**Circulation:** 19/24 alive · 5 clots · vein health 0.49

**Push cycles:** 0 · sync score: ? · reactor fires: 0

> **Organism directive:** Multiple systems degraded. Prioritize fixing clots and over-cap files before new features.
<!-- /pigeon:organism-health -->

<!-- pigeon:task-context -->
## Live Task Context

*Auto-injected 2026-05-10 21:09 UTC · 6 messages profiled · 8 recent commits*

**Current focus:** debugging / fixing
**Cognitive state:** `abandoned` (WPM: 48.7 | Del: 26.5% | Hes: 0.494) · *[source: measured]*

**Prompt ms:** 552741, 598213, 106828, 240803, 162790 (avg 332275ms)

> **CoT directive:** Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.

### Unsaid Threads
*Deleted from prompts — operator wanted this but didn't ask:*
- "also"
- "fingerp"

### Recent Work
- `fa8aab3` chore: refresh prompt telemetry context
- `84ea19b` fix: stabilize compliance training pair lookup
- `d53d5a9` merge: align telemetry branch with master
- `aa29359` chore: refresh operator intent context

### Fragile Contracts *[source: llm_derived]*
*From push narratives (LLM-generated) — treat as hypothesis:*
- Bulk-generated identical stubs causing mass syntax failures; test runner assumptions about sequential filenames; Pigeon's indentation compiler rejecting the Copilot-authored placeholder structure.
- Unthrottled parallel simulation spawns causing resource exhaustion; silent simulation failures due to malformed prompt forms; race conditions in self-healing execution from shared state access. This push introduces a parallel simulation daemon triggered by every operator prompt to enable proactive self-healing.

### Known Issues *[source: measured]*
*From self-fix scanner (AST-verified) — fix when touching nearby code:*
- [CRITICAL] hardcoded_import in `src/file_sim_seq001_v005_d0421__micro_sim_engine_prompt_file_lc_feat_operator_state_daemon.py`
- [CRITICAL] hardcoded_import in `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py`
- [CRITICAL] hardcoded_import in `src/tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer.py`
- [CRITICAL] hardcoded_import in `src/tc_popup_seq001_v004_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade.py`
- [CRITICAL] hardcoded_import in `src/tc_sim_engine_seq001_v004_d0420__intent_simulation_on_typing_pause_lc_chore_pigeon_rename_cascade.py`

### Codebase Health (Veins / Clots)
*19/24 alive, 5 clots, avg vein health 0.49*

**Clots (dead/bloated — trim candidates):**
- `p_tcsr` (score=0.75): isolated, dead_imports:3, unused_exports:1
- `context_select_agent` (score=0.65): orphan_no_importers, dead_imports:1, unused_exports:1, oversize:275
- `p_tcm` (score=0.60): isolated, unused_exports:1
- `p_gpip` (score=0.45): orphan_no_importers, unused_exports:1
- `file_sim` (score=0.40): dead_imports:3, oversize:1344, self_fix:dead_export:apply_undo_penalty, self_fix:dead_export:escalation_sweep

**Self-trim recommendations:**
- [investigate] `p_tcsr`: Isolated module (no imports in/out). May be dead code.
- [investigate] `context_select_agent`: Nobody imports this module. Check if it's an entry point or dead.
- [investigate] `p_tcm`: Isolated module (no imports in/out). May be dead code.
- [investigate] `p_gpip`: Nobody imports this module. Check if it's an entry point or dead.

**Critical arteries (do NOT break):**
- `tc_gemini` (vein=1.00, in=5)
- `tc_sim_engine` (vein=0.80, in=2)

<!-- /pigeon:task-context -->

<!-- pigeon:task-queue -->
## Active Task Queue

*Copilot manages this queue. To complete a task: update the referenced MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*

### Pending
- [ ] `tq-009` **the visualizartion needs to be reworked to be the most optim...** | stage: complete | focus: `.github/copilot-instructions.md`
- [ ] `tq-010` **why is organism health still so low - audit copilot intructi...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-011` **not talk first - when i click on a file throught pgeon brain...** | stage: complete | focus: `.github/copilot-instructions.md`
- [ ] `tq-012` **youre shedding the wrong blocks too - instead of entropy you...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-013` **no no our visualitions are spreadacrpss 3 uis - i need one w...** | stage: verify | focus: `.github/copilot-instructions.md`
- [ ] `tq-014` **<conversation-summary>
<analysis>
[Chronological Review:
- T...** | stage: verify | focus: `.github/copilot-instructions.md`
*…and 36 more in `task_queue.json`*

### Completed (last 3)
- [x] `tq-036` **but only fpr code - documnetation / major docs where operato...** | commit: `verified:intent-backlog`
- [x] `tq-037` ****Reactor patches:** 0/521 applied (0% acceptance)** | commit: `verified:intent-backlog`
- [x] `tq-038` **my gemini api key is set** | commit: `verified:intent-backlog`

<!-- /pigeon:task-queue -->


<!-- pigeon:voice-style -->
## Operator Voice Style

*Auto-extracted 2026-04-22 05:37 UTC · 78 prompts analyzed · zero LLM calls · scoring active*

**Brevity:** 49.5 words/prompt | **Caps:** never | **Fragments:** 68% | **Questions:** 10% | **Directives:** 3%

**Voice directives (effectiveness-scored):**
- Operator is semi-casual — use contractions, skip formalities, but keep technical precision.
- Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.
- Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural. [EFFECTIVE: +31% fewer reworks when active]
- Operator rarely uses punctuation — fragments and run-ons are normal. Don't overcorrect their style in quotes.
- Operator uses plain language — avoid unnecessary jargon in explanations.

**Vocabulary fingerprint:** t, e, s, i, d, n, to, m, a, y
<!-- /pigeon:voice-style -->
<!-- pigeon:operator-state -->
## Live Operator State

*Auto-updated 2026-04-22 - 700 message(s) in profile*

**Dominant: `abandoned`** | Submit: 66% | WPM: 52.8 | Del: 25.5% | Hes: 0.443

**Behavioral tunes for this session:**
- **abandoned** -> welcoming, direct - they re-approached after backing off
- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples
- Active hours: 0:00(30), 1:00(45), 2:00(12), 3:00(9), 4:00(21), 5:00(24), 6:00(15), 7:00(15), 8:00(15), 9:00(18), 10:00(49), 11:00(9), 12:00(15), 13:00(9), 14:00(21), 15:00(39), 16:00(30), 17:00(24), 18:00(21), 19:00(36), 20:00(21), 21:00(60), 22:00(99), 23:00(63)
<!-- /pigeon:operator-state -->

<!-- pigeon:prompt-telemetry -->
## Live Prompt Telemetry

*Auto-updated 2026-05-10T21:09:25.297249+00:00 - source: `logs/prompt_telemetry_latest.json`*

Use this block as the highest-freshness prompt-level telemetry. It is generated from Codex live context, not the stale legacy daemon.

```json
{
  "schema": "prompt_telemetry/latest/v2",
  "updated_at": "2026-05-10T21:09:25.297249+00:00",
  "source": "codex_compat.dynamic_context_pack",
  "latest_prompt": {
    "session_n": null,
    "ts": "2026-05-10T21:07:48.372967+00:00",
    "chars": 381,
    "preview": "we already render intent - so the first step of this migration - all it is is changing how we display intent in consenus - and how we model it - it should pull in past intent data from monthly acumulated profiles - since past audits didnt m",
    "intent": "we already render intent - so the first step of this migration - all it is is changing how we display intent in consenus - and how we model it - it should pull in past intent data from monthly acumulated profiles - since past audits didnt m",
    "state": "frustrated",
    "files_open": [
      "maif_auditor_maif_auditor_templates_ai_model_audit",
      "tc_intent_keys",
      "dev_plan",
      "maif_auditor_examples_politician_audit",
      "intent_loop_closer",
      "maif_auditor_examples_quick_audit",
      "src/file_interlinked_naming_sim_seq001_v001.py",
      "test_file_interlinked_naming_sim.py",
      "src/file_interlinked_naming_policy_seq001_v001.py",
      "src/file_number_key_identity_seq001_v001.py",
      ".github/copilot-instructions.md",
      "MANIFEST.md"
    ],
    "module_refs": [
      "maif_auditor_maif_auditor_templates_ai_model_audit",
      "tc_intent_keys",
      "dev_plan",
      "maif_auditor_examples_politician_audit",
      "intent_loop_closer",
      "maif_auditor_examples_quick_audit"
    ]
  },
  "signals": {
    "wpm": 0,
    "chars_per_sec": 0,
    "deletion_ratio": 0.068,
    "intent_deletion_ratio": 0.054,
    "hesitation_count": 7,
    "rewrite_count": 0,
    "typo_corrections": 0,
    "intentional_deletions": 6,
    "total_keystrokes": 400,
    "duration_ms": 162790
  },
  "composition_binding": {
    "matched": true,
    "source": "os_hook_auto",
    "age_ms": 0,
    "key": "ds4-0a6ed3738659c1d7",
    "match_score": 0.1248
  },
  "deleted_words": [
    "opt",
    "-",
    "also",
    "my",
    "ai",
    "fingerp"
  ],
  "rewrites": [],
  "task_queue": {
    "total": 13,
    "in_progress": [
      "intent_backlog:2026-04-25T07:29:13.010578+00:00",
      "intent_backlog:2026-04-25T15:51:58.609806+00:00",
      "intent_backlog:2026-04-25T16:50:35.069948+00:00",
      "intent_backlog:2026-04-25T18:00:07.521943+00:00",
      "intent_backlog:2026-04-25T18:24:53.199524+00:00",
      "intent_backlog:2026-04-25T18:29:49.256801+00:00",
      "intent_backlog:2026-04-25T18:33:47.523290+00:00",
      "intent_backlog:2026-04-25T18:40:09.762258+00:00"
    ],
    "pending": 13,
    "done": 0
  },
  "hot_modules": [
    "maif_auditor_maif_auditor_templates_ai_model_audit",
    "tc_intent_keys",
    "dev_plan",
    "maif_auditor_examples_politician_audit",
    "intent_loop_closer",
    "maif_auditor_examples_quick_audit",
    "src/file_interlinked_naming_sim_seq001_v001.py",
    "test_file_interlinked_naming_sim.py"
  ],
  "running_summary": {
    "total_prompts": 250,
    "avg_del_ratio": 0.051,
    "dominant_state": "unknown",
    "state_distribution": {
      "unknown": 149,
      "hesitant": 52,
      "frustrated": 49
    }
  },
  "deepseek": {
    "model": "deepseek-v4-pro",
    "job_id": "ds4-0a6ed3738659c1d7",
    "status": "queued",
    "autonomous_write": false
  },
  "staleness": {
    "replaces_legacy_pigeon_prompt_telemetry": true,
    "fresh_source": "logs/dynamic_context_pack.json"
  }
}
```

<!-- /pigeon:prompt-telemetry -->

<!-- pigeon:probe-resolutions -->
## Probe Resolutions

*2 resolved · 2026-04-22 05:37 UTC*

**Read these before editing the referenced modules:**

- **`query_memory`**: operator keeps query_memory as a clot — should it be split, deleted, or repurposed for probe history?
  - → Codebase pattern: 260+ modules, all decomposed by pigeon compiler. Split is the convention. (conf=0.60, via organism_directive)

- **`query_memory`**: operator keeps query_memory as a clot — should it be split, deleted, or repurposed for probe history?
  - → Operator deleted reference to 'delete' — likely intended: The operator was about to specify that the testing should occur after the initial fix has been applied.
---
They likely deleted it because the overall (conf=0.60, via unsaid_recon)

<!-- /pigeon:probe-resolutions -->

<!-- codex:pre-prompt-state -->
## Codex Pre-Prompt State

*Prepared 2026-05-10T21:21:30.074359+00:00 before model handoff*

**PROMPT:** `its still bot selecting files / writing file comments when i talk to codexes about linkrouter ai repo - why -`

**DELETION_RATIO:** `0.0`
**DELETED_WORDS:** none
**HESITATION_COUNT:** `1`

**NUMERIC_CONTEXT:**
- `tc_intent_file_memory` score=0.0608
- `maif_auditor_tests_manifest` score=0.0261
- `maif_auditor_examples_manifest` score=0.0234
- `tc_intent_keys` score=0.0229
- `maif_auditor_maif_auditor_manifest` score=0.0222
- `maif_auditor_maif_auditor_models_manifest` score=0.0201

**HANDOFF_READY:** `True`
**SIM_STATUS:** `skipped`
**FILE_SIM_STATUS:** `fired`
**FILE_SIM_TARGET_STATE:** `interlinked_source_state`
**FILE_SIM_SOURCE_REWRITES:**
- `src/tc_intent_file_memory_seq001_v001.py` interlink=0.455 decision=safe_dry_run
- `src/ai_fingerprint_repo_seq001_v001.py` interlink=0.595 decision=safe_dry_run
- `src/tc_intent_keys_seq001_v001.py` interlink=0.67 decision=safe_dry_run
- `src/__init__.py` interlink=0.65 decision=safe_dry_run
- `src/_resolve.py` interlink=0.67 decision=safe_dry_run
<!-- /codex:pre-prompt-state -->

<!-- codex:dynamic-context-pack -->
## Dynamic Context Pack

*Prepared 2026-05-10T21:07:48.372967+00:00 for os_hook_auto*

**PROMPT:** `we already render intent - so the first step of this migration - all it is is changing how we display intent in consenus - and how we model it - it should pull in past intent data from monthly acumulated profiles - since past audits didnt m`
**DELETION_RATIO:** `0.068`
**INTENT_DELETION_RATIO:** `0.054`
**HESITATION_COUNT:** `7`
**COGNITIVE_STATE:** `frustrated`
**DELETED_WORDS:** opt, -, also, my, ai, fingerp

**FOCUS_FILES:**
- `maif_auditor_maif_auditor_templates_ai_model_audit` via numeric_context score=0.1248
- `tc_intent_keys` via numeric_context score=0.062
- `dev_plan` via numeric_context score=0.0606
- `maif_auditor_examples_politician_audit` via numeric_context score=0.0512
- `intent_loop_closer` via numeric_context score=0.0471
- `maif_auditor_examples_quick_audit` via numeric_context score=0.0455
- `src/file_interlinked_naming_sim_seq001_v001.py` via recent_edit
- `test_file_interlinked_naming_sim.py` via recent_edit
- `src/file_interlinked_naming_policy_seq001_v001.py` via recent_edit
- `src/file_number_key_identity_seq001_v001.py` via recent_edit

**COPILOT_PROBE_PUSH_CYCLE:**
- cycle: `probe-422f20eebdfb8b60`
- read: You are asking the repo to treat intent as routing math: prompts wake files, files simulate consequences, and accepted fixes become memory. Deleted-word residue should be treated as hidden intent pressure: opt, -, also, my, ai, fingerp.
- deepseek context: `logs/copilot_probe_push_cycle_latest.json`
- waking files: `tc_gemini, tc_prompt_brain, resolve, tc_prompt_composer, tc_constants, tc_observatory`

**FILE_SELF_KNOWLEDGE:**
- read: 8 file packet(s) woke. Top file `src/file_interlinked_naming_sim_seq001_v001.py` now carries owns/wakes/context/validation/refusal data for Codex to probe with before any rewrite model drafts. 6 are draft-ready inside rails; 2 are blocked until real validation
- `src/file_interlinked_naming_sim_seq001_v001.py` owns `operator response policy and reward routing, seq001, interlinked, naming, fingerprint, sim, pigeon, manifest` readiness `draft_ready`
  - validates: `py -m py_compile src/file_interlinked_naming_sim_seq001_v001.py`
  - says: file_interlinked_naming_sim_seq001_v001.py: load file_interlinked_naming_policy_seq001_v001.py before you let a rewrite model touch my furniture.
- `src/file_interlinked_naming_policy_seq001_v001.py` owns `operator response policy and reward routing, seq001, fingerprint, pigeon, interlinked, naming, manifest, repo` readiness `draft_ready`
  - validates: `py -m py_compile src/file_interlinked_naming_policy_seq001_v001.py`
  - says: file_interlinked_naming_policy_seq001_v001.py: I have a test receipt; give me a bounded warrant and nobody gets theatrical.
- `src/file_number_key_identity_seq001_v001.py` owns `intent compilation and mutation routing, seq001, fingerprint, pigeon, operator, key, manifest, repo` readiness `blocked`
  - validates: `py -m py_compile src/file_number_key_identity_seq001_v001.py`
  - says: file_number_key_identity_seq001_v001.py: I can help, but first stop asking me to pass imaginary validation.
- `.github/copilot-instructions.md` owns `operator response policy and reward routing, ago, copilot, prompt, keystroke, state, github, instructions` readiness `draft_ready`
  - validates: `py -m pytest test_file_self_knowledge.py -q`
  - says: copilot-instructions.md: I can help, but first stop asking me to pass imaginary validation.
- `MANIFEST.md` owns `context selection and self-clearing file packs, ago, push, cycle, prompt, keystroke, manifest, state` readiness `draft_ready`
  - validates: `py -m pytest test_batch_rewrite_sim.py -q`
  - says: MANIFEST.md: I have a test receipt; give me a bounded warrant and nobody gets theatrical.

**CONTEXT_CONFIDENCE:** `0.1248`
**CONTEXT_STATUS:** `ok`

**UNRESOLVED_INTENTS:**
- `abandoned` submit Codex edits, make deletion analytics work here, and push the handoff to i... (also considered: deletions keystroke keystore telemetry raw)
- `abandoned` test numeric prompt encoding per query and decide repo focus around file intent ... (also considered: numeric observatory comedy neumeric obervatory)
- `partial` capture deletion inject before prompt reaches model... (also considered: deletion thought raw deleted)
- `partial` hesitation should trigger thought completer before copilot prompt handoff... (also considered: hesitation completer stalled half thought)

**PROMPT_BRAIN:**
- intent key: `pigeon_brain/flow:test:already_render_first_step:read`
- semantic: `unknown`
- profile hint: `none`
- prompt box open: `414`

**OPERATOR_RESPONSE_POLICY:**
- active arm: `surgical_engineer`
- operator read: Mutate the repo through a bounded patch, then prove it with tests or a clear validation gate.
- required sections: `Operator read, Next mutation, Validation`
- next mutation: Load `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py` with the top intent move and propose one bounded patch plus validation.
- intent move: `pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX:route:thought_completer:minor`
- intent move: `build/pigeon_legacy/pigeon_brain/flow:route:raw_operator_prompt_fallback:minor`
- intent move: `build/pigeon_legacy/src:patch:promote_bug_notes_quick:minor`
- intent move: `pigeon_compiler/integrations:route:generated_opus_executor_prompt:minor`
- intent move: `root:route:they_are_not_ignored:minor`
- probe file: `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py` via intent:route
- probe file: `src/tc_prompt_composer_seq001_v001.py` via intent:route
- probe file: `src/intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade.py` via intent:route
- probe file: `src/thought_completer.py` via intent:route
- probe file: `src/ai_fingerprint_operator_seq001_v001.py` via intent:route
- probe file: `src/tc_buffer_watcher_seq001_v001.py` via intent:route

**FILE_SIM:**
- status: `fired`
- target state: `interlinked_source_state`
- trigger: `os_hook_auto`
- `src/tc_intent_keys_seq001_v001.py` interlink=0.725 decision=safe_dry_run
- `src/intent_loop_closer_seq001_v001.py` interlink=0.635 decision=safe_dry_run
- `src/autonomous_mutation_audit_seq001_v001.py` interlink=0.41 decision=safe_dry_run
- `src/bug_profiles_seq001_v001.py` interlink=0.725 decision=safe_dry_run
- `src/__init__.py` interlink=0.65 decision=safe_dry_run

**INTENT_LOOP:**
- loop: `loop-100faf706eedb427` status `awaiting_operator_approval`
- intent: `src:route:already_render_intent_first_step:major`
- human: `on_loop` approval_required `True`
- observed edits: `0` responses: `0`
- next: operator approves or narrows the active loop
- next: Copilot executes one bounded proposal against focus files
- next: repo plugin logs edits and validation back onto this loop

**SURFACE_ACTIVITY:**
- latest key surface: `codex`
- latest key context: `chat`
- latest UIA context: `chat`
- latest context switch: `unknown` -> `chat`

**ENTROPY:** global H `0.2689`, tracked `18`

**DEEPSEEK_V4:**
- model: `deepseek-v4-pro`
- job: `ds4-0a6ed3738659c1d7` status `queued`
- autonomous write: `False`

**CAPTURE_BOUNDARY:**
- composer: pre-submit and blocking; pause and submit can inject before handoff
- Codex native chat: composition can be logged by external watcher, but this API path cannot block the already-sent Codex prompt
- screenshot context: not wired yet; UIA context switches are available now, screenshot/OCR can be layered next
<!-- /codex:dynamic-context-pack -->

<!-- codex:intent-key-context -->
## Intent Key Context

**INTENT_KEY:** `pigeon_compiler/integrations:route:its_still_bot_selecting:minor`
**SCOPE:** `pigeon_compiler/integrations`  **CONFIDENCE:** `0.2857`
**VOID:** `False`  **WARNINGS:** none
**SEMANTIC_INTENTS:** `unknown`
**NUMERIC_ENCODING:** `175a08b3d971e92d4c402c80`
**PROFILE_MATCHES:** `none`
**PROFILE_UPDATES:** `none`
**COMPLETION_HINT:** `none`
**MANIFEST:** `pigeon_compiler/integrations/MANIFEST.md`

**MANIFEST_EXCERPT:**
```text
# MANIFEST ? pigeon_compiler/integrations

> pigeon_compiler.integrations ? External AI model adapters.

*Auto-generated by pigeon_compiler manifest_builder | 2026-04-14 03:53 UTC*

## How to read this manifest

This file is **auto-generated** by `manifest_builder` and describes every
Python module in this folder. It is the single source of truth for:
- What each file does (Description)
- What each file exports (Exports) and depends on (Deps)
- Whether the file meets the Pigeon size budget (Status)
- Living operator notes that persist across rebuilds (Notes)

**Status icons:** ? ?200 lines | ?? OVER 200?300 | ? WARN 300?500 | ? CRIT >500

**Columns:** Seq = load order ? Lines = source line count ? Exports = public classes/functions ? Deps = intra-project imports
```
<!-- /codex:intent-key-context -->

<!-- codex:prompt-brain -->
## Prompt Brain

**PROMPT:** `its still bot selecting files / writing file comments when i talk to codexes about linkrouter ai repo - why -`
**TRIGGER:** `os_hook_auto:composition_submit`
**INTENT_KEY:** `pigeon_compiler/integrations:route:its_still_bot_selecting:minor`
**SEMANTIC:** `unknown`
**COMPLETION_HINT:** `none`
**PROFILE_FACTS:** `name=Nikita`
**AI_FINGERPRINT:** `aaf0c1d1bd2f2ff3740e747e93e39eb8`
**CONTEXT_STATUS:** `ok` confidence `0.0608`
**MANIFEST:** `pigeon_compiler/integrations/MANIFEST.md` confidence `0.2857`

**NUMERIC_FILES:**
- `tc_intent_file_memory` score `0.0608`
- `maif_auditor_tests_manifest` score `0.0261`
- `maif_auditor_examples_manifest` score `0.0234`
- `tc_intent_keys` score `0.0229`
- `maif_auditor_maif_auditor_manifest` score `0.0222`
- `maif_auditor_maif_auditor_models_manifest` score `0.0201`

**PROMPT_BOX_OPEN:** `415`
<!-- /codex:prompt-brain -->

<!-- codex:operator-response-policy -->
## Operator Response Policy

ACTIVE_ARM: `surgical_engineer`
POLICY_TS: `2026-05-10T21:09:25.584612+00:00`
OPERATOR_READ: Mutate the repo through a bounded patch, then prove it with tests or a clear validation gate.
PRIORITY: thinking_momentum > intent_extraction > autonomous_code_mutation_readiness > comedy_file_personality

REQUIRED_RESPONSE_SHAPE:
1. Operator read
2. Next mutation
3. Validation

RESPONSE_RULES:
- Act as the probe layer for intent, files, and validation.
- Start with what the prompt is really trying to do.
- Extract 3-5 intent moves when the prompt contains multiple moves.
- Name probe files from intent graph, intent nodes, and self-clearing context.
- Propose a bounded next mutation or explicitly refuse to mutate.
- Add exactly one file quote only when it carries useful state.
- Do not imitate typos unless quoting the operator.

BANNED_BEHAVIORS:
- performative comedy
- long ontology recap
- unverified confidence
- imitating operator typos unless quoting
- fake certainty about mutations not executed
- file quote when it does not carry signal

ACTIVE_INTENT_MOVES:
- `pigeon_compiler/rename_engine/?w_ir_s003_v005_d0403_???_?FX:route:thought_completer:minor` :: segment matched 8 file signal(s); manifest confidence 0.526
- `build/pigeon_legacy/pigeon_brain/flow:route:raw_operator_prompt_fallback:minor` :: segment matched 8 file signal(s); manifest confidence 0.750
- `build/pigeon_legacy/src:patch:promote_bug_notes_quick:minor` :: segment matched 8 file signal(s); manifest confidence 0.571
- `pigeon_compiler/integrations:route:generated_opus_executor_prompt:minor` :: segment matched 8 file signal(s); manifest confidence 0.800
- `root:route:they_are_not_ignored:minor` :: segment matched 8 file signal(s); manifest confidence 0.500

PROBE_FILES:
- `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py` via intent:route
- `src/tc_prompt_composer_seq001_v001.py` via intent:route
- `src/intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade.py` via intent:route
- `src/thought_completer.py` via intent:route
- `src/ai_fingerprint_operator_seq001_v001.py` via intent:route
- `src/tc_buffer_watcher_seq001_v001.py` via intent:route
- `src/opus_micro_pulse_runtime_seq001_v001.py` via self_clearing_context_window
- `pigeon_compiler/cut_executor/?f_cdp_s013_v002_d0322_??????_?7.py` via self_clearing_context_window

RECENT_REWARD: arm `probe_council`, score `0.0`
NEXT_MUTATION: Load `src/tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade.py` with the top intent move and propose one bounded patch plus validation.
<!-- /codex:operator-response-policy -->

<!-- codex:opus-cannon-bootstrap -->
## Opus Cannon Bootstrap

This file is only the bootstrap contract. The generated Opus cannon is the current executor prompt.

- primary_executor_prompt: `logs/opus_executor_prompt_latest.md`
- cannon_packet: `logs/prompt_cannon_job_latest.json`
- pulse_packet: `logs/opus_micro_pulse_latest.json`
- gate_packet: `logs/cannon_execution_gate_latest.json`
- current_prompt_hash: `3d59c2fd6f5265a8`
- current_executor_session: `codex_execution_session`
- current_prompt_class: `debug`

Executor rule: read the primary executor prompt first; use the operator prompt only as fallback evidence.
<!-- /codex:opus-cannon-bootstrap -->
