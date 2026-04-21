---
description: "Build-focused context: module map, file consciousness, coupling, commits"
---

# /build

*Hydrated 2026-04-21 23:15 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.495
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`neutral` bl_wpm=53 bl_del=26%
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

- 045f718 fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- 84b73b5 fix: copilot prompt assembly - doubled _seq001_v001 module imports
- f9a3310 feat: operator_state_daemon + decouple capture from LLM trigger
- 61d32a8 feat: interlink self-debug loop + 10Q test framework + rename-resistant test gen
- 365bde4 chore: pigeon cascade cleanup (hook disabled)
- 93020d4 chore: pigeon cascade cleanup (hook disabled)
- c61fc91 chore: pigeon rename cascade (interrupted hook cleanup)
- a7aacce chore: pigeon rename cascade (v002 bumps)
