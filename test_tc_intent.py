"""test_tc_intent.py — 10-completion intent accuracy test.

Runs real operator-style buffers through call_gemini() and scores each
completion on: topic anchoring, voice match, specificity, and unsaid alignment.

Usage: py test_tc_intent.py
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── test buffers — real operator fragments from prompt_journal ──
TEST_CASES = [
    # (buffer, expected_theme, expected_keywords)
    ("close the loop between thought completer and unsaid recon",
     "integration", ["unsaid", "thought", "completer", "recon", "loop"]),

    ("it just feels like maybe its not reasoning about the",
     "diagnosis", ["reasoning", "context", "signal"]),

    ("yeah but not only that its supposed to be injected with bug profiles dynamic",
     "dynamic injection", ["bug", "profile", "inject", "dynamic"]),

    ("run push cycle and make sure that rename engine",
     "verification", ["rename", "push", "cycle", "plan"]),

    ("where is thought completer building memory",
     "memory", ["memory", "profile", "shard", "tc_profile_seq001_v001"]),

    ("close the intent reconstruction from thought completer check if its",
     "gap closing", ["intent", "reconstruction", "unsaid", "tc"]),

    ("are you hallucinating the last 10 fixes - audit",
     "audit", ["audit", "prompts", "fix", "verify"]),

    ("if i had to diagnose my own problem i would say",
     "self-diagnosis", ["deletion", "signal", "intent", "pattern"]),

    ("why is organism health still so low",
     "health", ["organism", "health", "clot", "compliance", "over_hard_cap"]),

    ("should i close the loop by merging logic into one agent or them debating",
     "architecture", ["agent", "debate", "loop", "merge", "unsaid"]),
]

# ── scoring ──
def score_completion(buffer: str, completion: str, expected_keywords: list[str]) -> dict:
    if not completion or not completion.strip():
        return {"score": 0, "reason": "empty completion", "hit_keywords": []}

    comp_lower = completion.lower()
    buf_words = set(buffer.lower().split())
    comp_words = set(comp_lower.split())

    # 1. topic anchor — does completion share words with buffer?
    overlap = len(buf_words & comp_words) / max(len(buf_words), 1)

    # 2. keyword hit — does completion mention expected domain terms?
    hits = [kw for kw in expected_keywords if kw in comp_lower]
    kw_score = len(hits) / max(len(expected_keywords), 1)

    # 3. specificity — named modules, numbers, file refs
    import re
    specifics = re.findall(r'[a-z][a-z_]{4,}|[0-9]+', completion)
    specificity = min(len(specifics) / 5, 1.0)

    # 4. voice — lowercase, no "I think"/"we should" corporate filler
    voice_fail = any(p in comp_lower for p in ["i think", "we should", "let's", "you should"])
    caps_fail = completion[0].isupper() if completion else False
    voice_score = 1.0 - (0.4 if voice_fail else 0) - (0.2 if caps_fail else 0)

    # 5. not echo — use same threshold as tc_gemini_seq001_v001._is_buffer_echo
    buf_clean = buffer.lower().strip()
    # Only flag as echo if completion is basically the buffer repeated, not if
    # it shares topic words (which is CORRECT behaviour for a continuation)
    echo = (buf_clean in comp_lower and len(comp_lower) - len(buf_clean) < 20) or overlap > 0.85
    echo_penalty = -0.3 if echo else 0

    total = (overlap * 0.2 + kw_score * 0.4 + specificity * 0.2 + voice_score * 0.2) + echo_penalty
    total = max(0, min(1, total))

    return {
        "score": round(total, 2),
        "overlap": round(overlap, 2),
        "kw_hits": hits,
        "kw_score": round(kw_score, 2),
        "specificity": round(specificity, 2),
        "voice_ok": not voice_fail and not caps_fail,
        "echo": echo,
    }


def run():
    print("=" * 65)
    print("TC INTENT TEST — 10 completions vs real operator buffers")
    print("=" * 65)

    try:
        from src.tc_gemini_seq001_v001_seq001_v001 import call_gemini, ThoughtBuffer
        tb = ThoughtBuffer()
    except Exception as e:
        print(f"IMPORT FAILED: {e}")
        sys.exit(1)

    results = []
    total_score = 0

    for i, (buf, theme, kw) in enumerate(TEST_CASES, 1):
        print(f"\n[{i:02d}] {theme.upper()}")
        print(f"  BUFFER: {buf[:70]}")
        t0 = time.time()
        try:
            completion, ctx_files = call_gemini(buf, tb)
            latency = int((time.time() - t0) * 1000)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"case": i, "theme": theme, "score": 0, "error": str(e)})
            continue

        sc = score_completion(buf, completion, kw)
        total_score += sc["score"]

        comp_preview = (completion[:120] + "...") if len(completion) > 120 else completion
        score_bar = "█" * int(sc["score"] * 10) + "░" * (10 - int(sc["score"] * 10))
        if not completion.strip():
            print(f"  COMPLETION: (empty)")
            print(f"  SCORE: [{score_bar}] 0.00 | reason={sc.get('reason','?')} | {latency}ms")
        else:
            print(f"  COMPLETION: {comp_preview}")
            print(f"  SCORE: [{score_bar}] {sc['score']:.2f} | "
                  f"kw={sc.get('kw_score',0):.2f} hits={sc.get('kw_hits',[])} | "
                  f"voice={'ok' if sc.get('voice_ok') else 'fail'} | "
                  f"echo={'yes' if sc.get('echo') else 'no'} | "
                  f"{latency}ms")

        tb.record(buf, completion, "accepted")
        results.append({"case": i, "theme": theme, **sc})

    avg = total_score / len(TEST_CASES)
    bar = "█" * int(avg * 20) + "░" * (20 - int(avg * 20))
    print("\n" + "=" * 65)
    print(f"OVERALL: [{bar}] {avg:.2f}/1.00  ({avg*100:.0f}%)")

    passing = sum(1 for r in results if r.get("score", 0) >= 0.5)
    print(f"PASSING (≥0.5): {passing}/{len(TEST_CASES)}")

    if avg >= 0.7:
        print("VERDICT: nailing intent ✓")
    elif avg >= 0.5:
        print("VERDICT: decent — context is landing but specificity low")
    else:
        print("VERDICT: missing — check if Gemini key is live and unsaid_recon is feeding context")

    # write results
    out = ROOT / "logs" / "tc_intent_test_results.json"
    out.write_text(json.dumps({"avg": avg, "passing": passing, "cases": results}, indent=2), "utf-8")
    print(f"\nresults → {out}")


if __name__ == "__main__":
    run()
