---
description: "Build-focused context: module map, file consciousness, coupling, commits"
---

# /build

*Hydrated 2026-04-22 05:37 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`unknown` bl_wpm=52 bl_del=26%
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

- 1c96713 feat: conversational gate in run_sim â€” skip DeepSeek grader on non-coding prompts
- 3e7147b chore: ignore *.tmp_overwrite and *.py.bak artifacts
- 1ddcbc4 chore: remove stale .tmp_overwrite artifact
- 40acdc7 fix: overwriter atomic write WinError 183 (os.replace) + grader priority deepseek > gemini
- f944b28 feat: auto-overwrite on by default + regression TDD (syntax + test rollback)
- 3f2ffa8 feat: file overwriter (surgical search-replace) + GRADES tab + file cortex + _trigger_overwriter_async
- 045f718 fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- 84b73b5 fix: copilot prompt assembly - doubled _seq001_v001 module imports
