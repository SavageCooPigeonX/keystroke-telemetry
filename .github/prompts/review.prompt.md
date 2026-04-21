---
description: "Review-focused context: rework rate, mutation scores, edit patterns, coaching"
---

# /review

*Hydrated 2026-04-21 23:15 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 51 | Del: 26% | Hes: 0.495
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`unknown` state=`neutral` bl_wpm=53 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Rework Surface

**Rate:** 4% (8/200 needed rework)

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

- 045f718 fix: self-heal broken imports - scanner + auto_fix_broken_imports + 88 healed
- 84b73b5 fix: copilot prompt assembly - doubled _seq001_v001 module imports
- f9a3310 feat: operator_state_daemon + decouple capture from LLM trigger
- 61d32a8 feat: interlink self-debug loop + 10Q test framework + rename-resistant test gen
- 365bde4 chore: pigeon cascade cleanup (hook disabled)
- 93020d4 chore: pigeon cascade cleanup (hook disabled)
- c61fc91 chore: pigeon rename cascade (interrupted hook cleanup)
- a7aacce chore: pigeon rename cascade (v002 bumps)
- 6ae8700 fix: close outcome + sim reinjection feedback loops
- d296d1c chore: gitignore sensitive operator data files
