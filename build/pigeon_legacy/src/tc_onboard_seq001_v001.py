"""tc_onboard_seq001_v001 — operator onboarding + write-with-it mode.

Two standalone modes for thought_completer:

  --onboard   10 targeted questions → operator profile, intent heat map,
              intelligence report, then drops into write mode.

  --write     Interactive "write with it" loop. Type freely, get completions
              after each Enter. No VS Code / os_hook dependency.

Both modes update ThoughtBuffer, record_touch (intent_numeric training),
and cross-reference the intent backlog.

Usage:
    py src/thought_completer.py --onboard
    py src/thought_completer.py --write
    py src/thought_completer.py --write --no-gemini   (just heat map, no API call)
"""
from __future__ import annotations

import json
import sys
import os
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]

# ── ANSI colours (degrade gracefully on Windows) ──────────────────────────
_COLOR = sys.stdout.isatty()
def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s

DIM    = lambda s: _c("2", s)
BOLD   = lambda s: _c("1", s)
CYAN   = lambda s: _c("36", s)
GREEN  = lambda s: _c("32", s)
YELLOW = lambda s: _c("33", s)
RED    = lambda s: _c("31", s)
MAGENTA = lambda s: _c("35", s)

# ── 10 onboarding questions ───────────────────────────────────────────────
ONBOARD_QUESTIONS = [
    ("current_build",   "What are you building right now? Describe the feature or fix."),
    ("last_blocker",    "What's the last thing that blocked you or felt broken?"),
    ("hot_files",       "Which files or modules are you touching most this week?"),
    ("gap",             "What's the gap between where you are and where you need to be?"),
    ("patterns",        "What problems or patterns keep coming back in this codebase?"),
    ("10x_vision",      "What would a 10x better version of your current work look like?"),
    ("uncertainty",     "What are you most uncertain about right now?"),
    ("last_push",       "What did your last push or commit change?"),
    ("next_hour",       "What should happen in the next hour?"),
    ("unblock",         "One thing — if it worked perfectly — that would unblock everything?"),
]


# ── helpers ───────────────────────────────────────────────────────────────

def _load_imports():
    """Lazy-load heavy modules. Returns (call_gemini, ThoughtBuffer, record_touch, predict_files)."""
    sys.path.insert(0, str(ROOT))
    from src._resolve import src_import
    call_gemini, ThoughtBuffer = src_import("tc_gemini_seq001", "call_gemini", "ThoughtBuffer")
    record_touch, predict_files = src_import("intent_numeric_seq001", "record_touch", "predict_files")
    return call_gemini, ThoughtBuffer, record_touch, predict_files


def _load_backlog() -> list[dict]:
    bf = ROOT / "logs" / "intent_backlog_latest.json"
    if not bf.exists():
        return []
    try:
        data = json.loads(bf.read_text("utf-8", errors="ignore"))
        return data.get("intents", data) if isinstance(data, dict) else data
    except Exception:
        return []


def _load_op_profile() -> dict:
    pf = ROOT / "logs" / "operator_profile_tc.json"
    if not pf.exists():
        return {}
    try:
        return json.loads(pf.read_text("utf-8", errors="ignore"))
    except Exception:
        return {}


def _show_heat(predictions: list[tuple[str, float]], label: str = "intent heat") -> None:
    if not predictions:
        print(DIM("  (no predictions)"))
        return
    max_score = predictions[0][1] if predictions else 1.0
    for name, score in predictions[:6]:
        bar_len = int((score / max(max_score, 0.001)) * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {CYAN(bar)} {score:.3f}  {name}")


def _build_heat_aggregate(all_predictions: list[list[tuple[str, float]]]) -> list[tuple[str, float]]:
    """Merge predictions from all 10 answers into a single ranked heat map."""
    scores: dict[str, float] = {}
    for preds in all_predictions:
        for name, score in preds:
            scores[name] = scores.get(name, 0) + score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # Normalize
    total = sum(s for _, s in ranked) or 1.0
    return [(name, score / total) for name, score in ranked[:15]]


def _intelligence_report(answers: list[tuple[str, str, list]]) -> None:
    """Print the full intelligence report after onboarding."""
    print()
    print(BOLD("━" * 60))
    print(BOLD("  OPERATOR INTELLIGENCE REPORT"))
    print(BOLD("━" * 60))

    # 1. Intent heat map (aggregate)
    all_preds = [preds for _, _, preds in answers if preds]
    heat = _build_heat_aggregate(all_preds)
    print(BOLD("\n  INTENT HEAT MAP  (10 answers aggregated)"))
    _show_heat(heat, "aggregate")

    # 2. Operator state from profile
    profile = _load_op_profile()
    if profile:
        state = profile.get("shards", {})
        samples = profile.get("samples", 0)
        print(BOLD(f"\n  OPERATOR PROFILE  ({samples} samples)"))
        top_words = state.get("voice", {}).get("top_words", {})
        if top_words:
            top5 = list(top_words.items())[:5]
            print("  voice fingerprint: " + ", ".join(f"{w}({c})" for w, c in top5))
        dom_state = state.get("dominant_state", "unknown")
        print(f"  dominant state:    {YELLOW(dom_state)}")

    # 3. Backlog cross-reference
    backlog = _load_backlog()
    heat_files = {name for name, _ in heat[:8]}
    if backlog:
        matched = [i for i in backlog if any(
            f in str(i.get("text", "")) or f in str(i.get("module", ""))
            for f in heat_files
        )]
        print(BOLD(f"\n  BACKLOG MATCH  ({len(matched)}/{len(backlog)} intents touch hot files)"))
        for item in matched[:4]:
            txt = str(item.get("text", item.get("intent", str(item))))[:70]
            print(f"  {RED('●')} {txt}")

    # 4. Key patterns from answers
    print(BOLD("\n  WHAT YOU SAID"))
    for key, answer, _ in answers:
        label = key.replace("_", " ").upper()
        snippet = answer.strip()[:80]
        if snippet:
            print(f"  {DIM(label)}: {snippet}")

    print()
    print(BOLD("━" * 60))


# ── onboard flow ──────────────────────────────────────────────────────────

def run_onboard(use_gemini: bool = True) -> None:
    """10-question onboarding → intelligence report → write mode."""
    print()
    print(BOLD("╔══════════════════════════════════════════════════════════╗"))
    print(BOLD("║    THOUGHT COMPLETER — OPERATOR ONBOARDING               ║"))
    print(BOLD("╚══════════════════════════════════════════════════════════╝"))
    print(DIM("  10 questions to calibrate intent prediction + baseline."))
    print(DIM("  Press Ctrl+C to skip to write mode at any time.\n"))

    call_gemini, ThoughtBuffer, record_touch, predict_files = _load_imports()
    tb = ThoughtBuffer()

    answers: list[tuple[str, str, list]] = []

    for i, (key, question) in enumerate(ONBOARD_QUESTIONS, 1):
        print(f"\n{BOLD(f'[{i:02d}/10]')} {YELLOW(question)}")
        try:
            answer = input("  > ").strip()
        except (KeyboardInterrupt, EOFError):
            print(DIM("\n  (skipping remaining questions)"))
            break

        if not answer:
            answers.append((key, "", []))
            continue

        # Record to intent_numeric
        try:
            changed = _infer_touched_files(answer)
            record_touch(answer, changed)
        except Exception as e:
            print(DIM(f"  [touch recording failed: {e}]"))

        # Predict files
        preds = []
        try:
            preds = predict_files(answer, top_n=6) or []
        except Exception:
            pass

        # Show mini heat
        if preds:
            print(DIM("  predicted:"))
            _show_heat(preds)

        # Get a quick completion if gemini is on
        if use_gemini and answer:
            try:
                completion, _ = call_gemini(answer, tb)
                if completion:
                    tb.record(answer, completion, "accepted")
                    print(f"  {GREEN('→')} {DIM(completion[:120])}")
            except Exception as e:
                print(DIM(f"  [completion skipped: {e}]"))

        answers.append((key, answer, preds))

    # Full intelligence report
    _intelligence_report(answers)

    # Drop into write mode
    print(f"\n  {CYAN('Dropping into write mode...')} {DIM('(Ctrl+C to exit)')}\n")
    run_write(use_gemini=use_gemini, thought_buffer=tb)


def _infer_touched_files(text: str) -> list[str]:
    """Best-effort: extract file/module names from a natural-language answer."""
    import re
    # Match things that look like module names: snake_case words with underscores
    tokens = re.findall(r'\b[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}\b', text.lower())
    # Filter very generic words
    STOPWORDS = {"that", "this", "with", "from", "into", "about", "what", "when"}
    return [t for t in tokens if t not in STOPWORDS][:8]


# ── write mode ────────────────────────────────────────────────────────────

def run_write(use_gemini: bool = True, thought_buffer=None) -> None:
    """Interactive write-with-it loop. Type → Enter → completion shown."""
    call_gemini, ThoughtBuffer, record_touch, predict_files = _load_imports()
    tb = thought_buffer or ThoughtBuffer()

    print(BOLD("╔══════════════════════════════════════════════════════════╗"))
    print(BOLD("║    THOUGHT COMPLETER — WRITE MODE                        ║"))
    print(BOLD("╚══════════════════════════════════════════════════════════╝"))
    print(DIM("  Type anything. Press Enter for a completion."))
    print(DIM("  Commands:  .heat   .report   .clear   .quit\n"))

    history: list[str] = []
    all_preds: list[list] = []

    while True:
        try:
            raw = input(f"{BOLD('write')} {CYAN('❯')} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM('  exiting write mode.')}")
            break

        if not raw:
            continue

        cmd = raw.lstrip(".")
        if raw.startswith("."):
            if cmd == "quit" or cmd == "q":
                print(DIM("  goodbye"))
                break
            elif cmd == "heat":
                if all_preds:
                    heat = _build_heat_aggregate(all_preds)
                    print(BOLD("  INTENT HEAT (this session)"))
                    _show_heat(heat)
                else:
                    print(DIM("  no predictions yet"))
                continue
            elif cmd == "report":
                _intelligence_report([(f"input_{i}", h, p) for i, (h, p) in enumerate(zip(history, all_preds or [[] for _ in history]))])
                continue
            elif cmd == "clear":
                history.clear()
                all_preds.clear()
                print(DIM("  session cleared"))
                continue
            else:
                print(DIM(f"  unknown command: {raw}"))
                continue

        history.append(raw)

        # Intent heat
        preds = []
        try:
            preds = predict_files(raw, top_n=5) or []
            all_preds.append(preds)
        except Exception:
            all_preds.append([])

        # Completion
        if use_gemini:
            print(DIM("  completing..."), end="\r")
            try:
                t0 = time.time()
                completion, ctx_files = call_gemini(raw, tb)
                elapsed = time.time() - t0
                if completion:
                    tb.record(raw, completion, "accepted")
                    # Record to intent_numeric
                    try:
                        record_touch(raw, ctx_files or [])
                    except Exception:
                        pass
                    print(f"  {GREEN('→')} {completion[:200]}  {DIM(f'({elapsed:.1f}s)')}")
                    if preds:
                        files_str = "  ".join(f"{name}" for name, _ in preds[:4])
                        print(f"  {DIM('files:')} {CYAN(files_str)}")
                else:
                    print(DIM("  (empty completion)"))
                    if preds:
                        _show_heat(preds)
            except Exception as e:
                print(f"  {RED('error:')} {e}")
                if preds:
                    print(DIM("  heat (no completion):"))
                    _show_heat(preds)
        else:
            # No-gemini mode: just show heat
            if preds:
                _show_heat(preds)
            else:
                print(DIM("  (no predictions)"))

        print()


# ── entry point ───────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="tc_onboard — onboarding + write mode")
    p.add_argument("--onboard", action="store_true", help="10-question onboarding flow")
    p.add_argument("--write", action="store_true", help="interactive write-with-it loop")
    p.add_argument("--no-gemini", action="store_true", help="skip Gemini API calls (heat map only)")
    args = p.parse_args(argv)

    use_gemini = not args.no_gemini

    if args.onboard:
        run_onboard(use_gemini=use_gemini)
    elif args.write:
        run_write(use_gemini=use_gemini)
    else:
        p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
