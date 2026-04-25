---
description: "Build-focused context: module map, file consciousness, coupling, commits"
---

# /build

*Hydrated 2026-04-23 16:28 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`debugging` state=`unknown` bl_wpm=52 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Module Map (compact)

**pigeon_compiler/git_plugin** (3 modules, 14.4K tok · 1 bugged)
**src** (19 modules, 113.8K tok · 12 bugged)
**src/tc_sim** (1 modules, 959 tok)
**src/tc_web** (1 modules, 707 tok)
**src/thought_completer** (1 modules, 418 tok)
**tests/interlink** (5 modules, 5.7K tok)

## Codebase Fears (from file consciousness)

- file may not exist (13 modules)
- swallowed exception (12 modules)
- regex format dependency (10 modules)
- returns empty on failure (silent) (7 modules)
- bare except hides errors (1 modules)

## Recent Commits

- 1ddbb0b feat: SIMS browser tab in observatory + run_assembly on every Copilot prompt
- 42e5d68 fix: context_select_agent _predict key=len crash (silent empty results)
- 1bc3c83 feat: high-deletion sim trigger in popup (50%+ buffer shrink in 4s fires sim)
- 940690c feat: inject deleted words + UNSAID_RECONSTRUCTION into pigeon:current-query on every prompt
- 8944b1e feat: tc_file_encoder + baseline collector button in popup + push-cycle intent dropoff
- b8bbe0f chore: advance shrink baseline (+5 tokens from src_import fixes)
- 8943f6a fix: replace hardcoded pigeon imports with src_import() across scripts + tests
- d001534 fix: pigeon compiler indent errors in tc_sim + thought_completer + 42 intent test stubs + reseal master_test
