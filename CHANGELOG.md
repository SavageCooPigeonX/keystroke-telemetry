# Changelog — keystroke-telemetry

---

## [unreleased] 2026-03-17

### feat: dynamic CoT injection fully wired (`d460a7d`, `f989307`, `1f60b21`)

The system now injects **11 live telemetry sections** into Copilot's chain-of-thought on every commit.
`dynamic_prompt_seq017` reads from 10 data sources and writes a self-updating `<!-- pigeon:task-context -->` block directly into `.github/copilot-instructions.md`.

**New injection sections (this session):**

| Section | Data Source | What it surfaces |
|---|---|---|
| Coaching Directives | `operator_coaching.md` | DeepSeek-synthesized behavioral rules per operator state |
| Fragile Contracts | `docs/push_narratives/*.md` | Module assumptions + regression watchlists from last 3 commits |
| Known Issues | `docs/self_fix/*.md` | CRITICAL/HIGH problems with file names from latest self-fix scan |
| Persistent Gaps | `query_memory.json` | Recurring queries asked 2+ times (bg-noise filtered) |

**Previously injected (prior session):**
- Task focus inferred from commit messages
- Cognitive state + per-state CoT directive (frustrated/hesitant/flow/restructuring/abandoned)
- Unsaid threads (deleted prompt words)
- Module hot zones (file_heat_map hesitation scores)
- AI rework surface (miss rate + worst queries)
- Recent commits (non-pigeon-auto only)
- Prompt evolution trajectory (mutation count, line growth, features added)

**Pipeline:**
```
git commit
  → git_plugin._run_post_commit_extras()
      → push_narrative, self_fix, prompt_recon
      → DeepSeek → operator_coaching.md
      → _refresh_operator_state() → <!-- pigeon:operator-state -->
      → dynamic_prompt.inject_task_context() → <!-- pigeon:task-context -->
      → auto-commit [pigeon-auto]
```

---

### fix: operator_stats DATA block never accumulating (`1f60b21`)

`OperatorStats._load_existing()` searched for `"<!-- DATA"` on a single line, but
`_render()` outputs the markers on separate lines:
```
<!--
DATA
{json}
DATA
-->
```
**Fix:** changed to `re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->', ..., re.DOTALL)`.
Every instantiation had been starting with empty history — the profile was never accumulating
beyond 1 message despite 110+ extension flushes. Now accumulates correctly (verified: 5 → 6 entries on re-load).

---

### feat: copilot prompt mutation tracker + auto-recon pipeline (`fa132f9`, `fec3fe0`)

- `prompt_recon_seq016` reconstructs Copilot prompts from commit diffs and tracks how
  `copilot-instructions.md` has evolved across all commits.
- Snapshots stored in `logs/copilot_prompt_mutations.json`. Current state: **24 mutations, 186→434 lines**.
- Features added tracked per-snapshot: `auto_index`, `operator_state`, `prompt_journal`, `pulse_blocks`, `prompt_recon`.
- Wired into post-commit hook: runs on every push.

---

### fix: EXCLUDE_STEM_PATTERNS was silently excluding all src/ files (`8199ccb`)

`is_excluded()` matched files whose intent slug contained `"prompt"` — every `src/` file
at the time had `_lc_pulse_telemetry_prompt` in the name. Push narratives were never
generating for any src/ module changes. Fixed the pattern to require a full stem match.

---

### feat: composition analyzer wired into cognitive pipeline (`7dd8e7b`)

Deleted words from prompt compositions now feed into:
1. `unsaid_seq002` — query memory unsaid thread detection
2. `operator_coaching.md` — DeepSeek sees what the operator wanted to say but deleted
3. `dynamic_prompt_seq017` — injected as "Unsaid Threads" into every Copilot session

---

## Manifest rebuild — 2026-03-17 05:46 UTC

All 17 MANIFEST.md files rebuilt across the project:
`src/`, `src/cognitive/`, `src/cognitive/drift/`, `src/cognitive/unsaid/`,
`src/operator_stats/`, `streaming_layer/`, `pigeon_compiler/`,
`pigeon_compiler/bones/`, `pigeon_compiler/cut_executor/`,
`pigeon_compiler/integrations/`, `pigeon_compiler/rename_engine/`,
`pigeon_compiler/runners/`, `pigeon_compiler/runners/compiler_output/press_release_gen/`,
`pigeon_compiler/state_extractor/`, `pigeon_compiler/weakness_planner/`,
`client/`, `vscode-extension/`

`MASTER_MANIFEST.md` rebuilt from scratch (was blank).

---

## Known outstanding issues (from self-fix scanner)

| Severity | Type | Files |
|---|---|---|
| CRITICAL | hardcoded_import | `stress_test.py`, `test_all.py`, `vscode-extension/pulse_watcher.py` |
| HIGH | query_noise | 76 `(background)` queries in `query_memory.json` — filter in extension flush |
| LOW | dead_export | ~11 functions defined but never called across `src/` |

---

## Module versions as of this session

| Module | Version |
|---|---|
| `dynamic_prompt_seq017` | v003 |
| `operator_stats_seq008` | v004 |
| `push_narrative_seq012` | v005 |
| `prompt_recon_seq016` | v001 |
| `logger_seq003` | v003 |
| `context_budget_seq004` | v007 |
| `drift_watcher_seq005` | v003 |
| `resistance_bridge_seq006` | v003 |
| `rework_detector_seq009` | v004 |
| `query_memory_seq010` | v003 |
| `file_heat_map_seq011` | v004 |
| `self_fix_seq013` | v003 |
| `cognitive_reactor_seq014` | v002 |
| `pulse_harvest_seq015` | v002 |
