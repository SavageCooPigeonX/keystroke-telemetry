---
description: "Review-focused context: rework rate, mutation scores, edit patterns, coaching"
---

# /review

*Hydrated 2026-04-23 16:28 UTC · detected mode: debug*

## Live Signals

**Cognitive:** `abandoned` | WPM: 48 | Del: 26% | Hes: 0.490
**CoT:** Operator abandoned previous attempt. Re-anchor with crisp summary of last context, then be direct.
**Active bugs:** `intent_numeric` (oc+de), `file_sim` (oc+de), `tc_context_agent` (oc+de), `tc_gemini` (oc)
**Codes:** intent=`debugging` state=`unknown` bl_wpm=52 bl_del=26%
**Voice:** Operator is semi-casual — use contractions, skip formalities, but keep technical precision.; Operator never capitalizes — you don't need to either in casual responses, but keep code accurate.

---

## Rework Surface

**Rate:** 29% (58/200 needed rework)

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

- 1ddbb0b feat: SIMS browser tab in observatory + run_assembly on every Copilot prompt
- 42e5d68 fix: context_select_agent _predict key=len crash (silent empty results)
- 1bc3c83 feat: high-deletion sim trigger in popup (50%+ buffer shrink in 4s fires sim)
- 940690c feat: inject deleted words + UNSAID_RECONSTRUCTION into pigeon:current-query on every prompt
- 8944b1e feat: tc_file_encoder + baseline collector button in popup + push-cycle intent dropoff
- b8bbe0f chore: advance shrink baseline (+5 tokens from src_import fixes)
- 8943f6a fix: replace hardcoded pigeon imports with src_import() across scripts + tests
- d001534 fix: pigeon compiler indent errors in tc_sim + thought_completer + 42 intent test stubs + reseal master_test
- b03dfde chore: refresh task-context block (inject_task_context)
- f54db83 feat: stable journal alias validation + key_stability scorer + audit registry
