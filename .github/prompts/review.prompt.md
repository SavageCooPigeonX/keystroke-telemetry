---
description: "Review-focused context: rework rate, mutation scores, edit patterns, coaching"
---

# /review

*Hydrated 2026-04-22 05:37 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`unknown` bl_wpm=52 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Rework Surface

**Rate:** 30% (59/200 needed rework)

## Mutation Effectiveness

- `Operator Voice Style`: score=?
- `Data Flow: Keystroke → Cognitive State → LLM`: score=?
- `Fragile Contracts`: score=?
- `Active Template: /build`: score=?
- `MANDATORY: Prompt Journal (execute FIRST on every message)`: score=?
- `Quick Reference`: score=?
- `Active Template: /debug`: score=?
- `What You Actually Mean Right Now`: score=?

## Recent Work

- 1c96713 feat: conversational gate in run_sim â€” skip DeepSeek grader on non-coding prompts
- 3e7147b chore: ignore *.tmp_overwrite and *.py.bak artifacts
- 1ddcbc4 chore: remove stale .tmp_overwrite artifact
- 40acdc7 fix: overwriter atomic write WinError 183 (os.replace) + grader priority deepseek > gemini
- f944b28 feat: auto-overwrite on by default + regression TDD (syntax + test rollback)
- 3f2ffa8 feat: file overwriter (surgical search-replace) + GRADES tab + file cortex + _trigger_overwriter_async
- 045f718 fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- 84b73b5 fix: copilot prompt assembly - doubled _seq001_v001 module imports
- f9a3310 feat: operator_state_daemon + decouple capture from LLM trigger
- 61d32a8 feat: interlink self-debug loop + 10Q test framework + rename-resistant test gen
