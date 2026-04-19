"""tc_sim_seq001_v001.py — replay typed sessions through the thought completer pipeline.

Extracts complete typing sessions from os_keystrokes.jsonl, replays them
through Gemini at the exact pause points, and scores prediction accuracy
against what was actually typed.

Usage:
    py -m src.tc_sim_seq001_v001                    # replay last 5 sessions
    py -m src.tc_sim_seq001_v001 --n 20             # replay last 20 sessions
    py -m src.tc_sim_seq001_v001 --live             # replay + call Gemini (costs API)
    py -m src.tc_sim_seq001_v001 --session 42       # replay specific session index
    py -m src.tc_sim_seq001_v001 --min-len 20       # only sessions with 20+ char buffer
    py -m src.tc_sim_seq001_v001 --pause-ms 1200    # custom pause threshold
    py -m src.tc_sim_seq001_v001 --export sim.jsonl # export results
    py -m src.tc_sim_seq001_v001 --transcript       # comedy narrative transcript
    py -m src.tc_sim_seq001_v001 --fix              # identify + apply fixes from sim data
    py -m src.tc_sim_seq001_v001 --narrate          # plain english explanation of everything

Modes:
    dry (default): extracts sessions, finds pause points, shows what WOULD
                   have been sent to Gemini. Zero API calls.
    live:          actually calls Gemini at each pause point. Compares
                   prediction to what the operator actually typed next.
    transcript:    narrative comedy version — the sim reads like a story.
    fix:           uses sim results to identify bugs and patches them.
    narrate:       the system explains itself to you in plain language.
"""
from __future__ import annotations
import json
import sys
import os
import time
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.tc_constants_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT


@dataclass
class TypingSession:
    """One complete typing session: first keystroke → submit/discard."""
    index: int
    events: list[dict] = field(default_factory=list)
    final_buffer: str = ''
    context: str = 'editor'
    start_ts: int = 0
    end_ts: int = 0
    duration_ms: int = 0
    keystroke_count: int = 0
    backspace_count: int = 0
    pause_points: list[dict] = field(default_factory=list)

    @property
    def deletion_ratio(self) -> float:
        if self.keystroke_count == 0:
            return 0.0
        return self.backspace_count / self.keystroke_count


@dataclass
class PausePoint:
    """A moment where the operator paused long enough to trigger completion."""
    ts: int
    buffer: str
    pause_ms: int
    buffer_after: str  # what the buffer looked like after they resumed typing
    final_text: str    # what was ultimately submitted
    position_pct: float  # how far into the session (0.0-1.0)


@dataclass
class SimResult:
    """Result of replaying one pause point through Gemini."""
    pause: PausePoint
    prediction: str = ''
    latency_ms: int = 0
    # Accuracy metrics
    exact_match: bool = False
    prefix_match_len: int = 0
    word_overlap: float = 0.0
    continuation_captured: str = ''  # what they actually typed after the pause
    context_files: list[str] = field(default_factory=list)


# ── Session extraction ──────────────────────────────────────────────────────

def extract_sessions(log_path: Path = KEYSTROKE_LOG,
                     min_buffer_len: int = 8) -> list[TypingSession]:
    """Extract complete typing sessions from os_keystrokes.jsonl.

    A session = all events between buffer-empty and submit/discard.
    """
    sessions: list[TypingSession] = []
    current: list[dict] = []
    idx = 0

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            evt_type = evt.get('type', '')
            current.append(evt)

            if evt_type in ('submit', 'discard'):
                buf = evt.get('buffer', '')
                if len(buf) >= min_buffer_len:
                    sess = TypingSession(
                        index=idx,
                        events=current[:],
                        final_buffer=buf,
                        context=evt.get('context', 'editor'),
                        start_ts=current[0].get('ts', 0),
                        end_ts=evt.get('ts', 0),
                    )
                    sess.duration_ms = sess.end_ts - sess.start_ts
                    sess.keystroke_count = len(current)
                    sess.backspace_count = sum(
                        1 for e in current if e.get('type') == 'backspace'
                    )
                    idx += 1
                    sessions.append(sess)
                current = []
            elif evt_type == 'discard' or (evt_type == 'insert' and not current):
                current = [evt]

    return sessions


# ── Pause detection ─────────────────────────────────────────────────────────

def find_pause_points(session: TypingSession,
                      pause_ms: int = DEFAULT_PAUSE_MS,
                      min_buffer_len: int = 4) -> list[PausePoint]:
    """Find moments where the operator paused long enough to trigger completion.

    Returns pauses with the buffer state AT the pause and AFTER resumption.
    """
    pauses: list[PausePoint] = []
    events = session.events
    if len(events) < 3:
        return pauses

    for i in range(1, len(events) - 1):
        prev_ts = events[i - 1].get('ts', 0)
        curr_ts = events[i].get('ts', 0)
        gap = curr_ts - prev_ts

        if gap >= pause_ms:
            # Buffer at the pause = last event before the gap
            buf_at_pause = events[i - 1].get('buffer', '')
            if len(buf_at_pause) < min_buffer_len:
                continue

            # Buffer after resumption — scan ahead to find the NEXT stable point.
            # Use the buffer ~10 events later, or at the next pause/submit.
            # This gives us what they actually typed RIGHT AFTER this pause,
            # not what was ultimately submitted (which could be a total rewrite).
            lookahead = min(i + 15, len(events) - 1)
            buf_after = events[lookahead].get('buffer', '')
            # If the buffer shrunk (backspace cycle), use 5-event lookahead
            if len(buf_after) < len(buf_at_pause):
                buf_after = events[min(i + 5, len(events) - 1)].get('buffer', '')

            # Position in session timeline
            if session.duration_ms > 0:
                pos = (prev_ts - session.start_ts) / session.duration_ms
            else:
                pos = 0.5

            pauses.append(PausePoint(
                ts=prev_ts,
                buffer=buf_at_pause,
                pause_ms=gap,
                buffer_after=buf_after,
                final_text=session.final_buffer,
                position_pct=round(pos, 2),
            ))

    session.pause_points = [{'ts': p.ts, 'buffer': p.buffer[:60],
                             'pause_ms': p.pause_ms} for p in pauses]
    return pauses


# ── Accuracy scoring ────────────────────────────────────────────────────────

def _extract_continuation(buffer_at_pause: str, final_text: str) -> str:
    """What the operator typed AFTER the pause point."""
    if final_text.startswith(buffer_at_pause):
        return final_text[len(buffer_at_pause):]
    # Fuzzy: find best alignment
    for i in range(min(len(buffer_at_pause), len(final_text)), 0, -1):
        if final_text[:i] == buffer_at_pause[:i]:
            return final_text[i:]
    return final_text


def _word_overlap(prediction: str, actual: str) -> float:
    """Jaccard similarity of word sets."""
    pred_words = set(re.findall(r'\w+', prediction.lower()))
    actual_words = set(re.findall(r'\w+', actual.lower()))
    if not pred_words or not actual_words:
        return 0.0
    intersection = pred_words & actual_words
    union = pred_words | actual_words
    return len(intersection) / len(union)


def _prefix_match(prediction: str, actual: str) -> int:
    """How many characters match from the start."""
    n = 0
    for a, b in zip(prediction, actual):
        if a == b:
            n += 1
        else:
            break
    return n


def score_prediction(pause: PausePoint, prediction: str) -> SimResult:
    """Score a prediction against what was actually typed.
    
    Uses buffer_after (what they typed immediately after this pause) as
    primary ground truth. Falls back to final_text only when buffer_after
    extends the buffer naturally (no rewrite detected).
    """
    # Primary: what they typed right after this pause
    local_cont = _extract_continuation(pause.buffer, pause.buffer_after)
    # Fallback: what was ultimately submitted
    final_cont = _extract_continuation(pause.buffer, pause.final_text)
    
    # Use local continuation if it exists and is different from final
    # (meaning the operator rewrote after this pause)
    if local_cont and local_cont != final_cont:
        continuation = local_cont  # rewrite detected — use local ground truth
    elif local_cont:
        continuation = local_cont
    else:
        continuation = final_cont
    
    result = SimResult(
        pause=pause,
        prediction=prediction,
        continuation_captured=continuation,
    )
    if not prediction or not continuation:
        return result

    pred_clean = prediction.strip().lower()
    cont_clean = continuation.strip().lower()

    result.exact_match = pred_clean == cont_clean
    result.prefix_match_len = _prefix_match(pred_clean, cont_clean)
    result.word_overlap = round(_word_overlap(pred_clean, cont_clean), 3)
    return result


# ── Live replay ─────────────────────────────────────────────────────────────

def _build_historical_context(pause: PausePoint) -> tuple[dict, dict]:
    """Reconstruct context AND trajectory from the pause point's time period.
    
    The current bug: replay uses LIVE context (today's conversation) when
    simulating a pause from days ago. This makes predictions meaningless.
    
    Fix: search chat_compositions for entries around this pause's timestamp.
    
    Returns: (context_dict, trajectory_dict)
    """
    from datetime import datetime, timezone
    import json
    
    compositions_path = ROOT / 'logs' / 'chat_compositions.jsonl'
    if not compositions_path.exists():
        return {}, {}
    
    # Convert pause timestamp (unix ms) to datetime
    pause_dt = datetime.fromtimestamp(pause.ts / 1000, tz=timezone.utc)
    
    # Load compositions from the same session (within 2 hours before pause)
    comps_before = []
    try:
        for line in compositions_path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            ts_str = raw.get('ts', '')
            if not ts_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            except Exception:
                continue
            # Keep entries within 2 hours BEFORE the pause
            delta = (pause_dt - entry_dt).total_seconds()
            if 0 < delta < 7200:  # 0-2 hours before
                cs = raw.get('chat_state', {})
                signals = cs.get('signals', {}) if isinstance(cs, dict) else {}
                comps_before.append({
                    'ts': ts_str,
                    'text': raw.get('final_text', '')[:500],
                    'state': cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown',
                    'wpm': signals.get('wpm', 0),
                    'del_ratio': raw.get('deletion_ratio', 0),
                    'deleted_words': [
                        d.get('word', '') if isinstance(d, dict) else str(d)
                        for d in raw.get('deleted_words', [])[-6:]
                    ],
                    'rewrites': [
                        f"{r.get('old', '')}→{r.get('new', '')}"[:80]
                        if isinstance(r, dict) else str(r)[:80]
                        for r in raw.get('rewrites', [])[-4:]
                    ],
                    'hesitations': len(raw.get('hesitation_windows', [])),
                    'duration_ms': raw.get('duration_ms', 0),
                })
    except Exception:
        return {}, {}
    
    # Take last 5 compositions before the pause
    comps_before = sorted(comps_before, key=lambda x: x['ts'])[-5:]
    
    if not comps_before:
        return {}, {}
    
    # Build context
    ctx = {
        'session_messages': [
            {'text': c['text'], 'intent': 'unknown'}
            for c in comps_before
        ],
        'session_info': {
            'intent': 'unknown',
            'cognitive_state': comps_before[-1].get('state', 'unknown'),
            'session_n': len(comps_before),
        },
    }
    
    # Build trajectory in the format expected by format_trajectory_for_prompt
    trajectory = {
        'turns': [
            {
                'prompt': c['text'],
                'state': c['state'],
                'wpm': c['wpm'],
                'del_ratio': c['del_ratio'],
                'deleted_words': c['deleted_words'],
                'rewrites': c['rewrites'],
                'hesitations': c['hesitations'],
                'duration_ms': c['duration_ms'],
                'response': '',  # no response capture for historical
            }
            for c in comps_before
        ],
        'phase': 'iterating',  # default
        'suppressed': [],
        'recent_states': [c['state'] for c in comps_before[-3:]],
    }
    
    # Collect all deleted words for suppressed intent
    all_deleted = []
    for c in comps_before:
        all_deleted.extend(c.get('deleted_words', []))
    trajectory['suppressed_intent'] = list(set(all_deleted))[-10:]
    
    return ctx, trajectory


def replay_pause_live(pause: PausePoint, use_historical_ctx: bool = False) -> SimResult:
    """Actually call Gemini for one pause point and score the result.
    
    Args:
        use_historical_ctx: If True, reconstruct context from the pause's time
                           instead of using live context. This fixes the major
                           bug where sim uses today's conversation to predict
                           a pause from last week.
    """
    from src.tc_gemini_seq001_v001 import call_gemini, _build_user_prompt, SYSTEM_PROMPT
    from src.tc_trajectory_seq001_v001 import format_trajectory_for_prompt
    import json, urllib.request
    from src.tc_constants_seq001_v001 import GEMINI_MODEL, GEMINI_TIMEOUT
    from src.tc_gemini_seq001_v001 import _load_api_key, _strip_signal_echo
    
    t0 = time.time()
    
    if use_historical_ctx:
        # Build context AND trajectory from the pause's time period, not live
        ctx, trajectory = _build_historical_context(pause)
        turns_n = len(trajectory.get('turns', []))
        print(f'[historical] {turns_n} turns in trajectory')
        if turns_n > 0:
            for i, t in enumerate(trajectory['turns'][:3]):
                print(f'  turn {i+1}: {t["prompt"][:50]}...')
        if not trajectory.get('turns'):
            # Fall back to live if no historical data
            prediction, ctx_files = call_gemini(pause.buffer)
        else:
            # Call Gemini with historical context + trajectory
            api_key = _load_api_key()
            if not api_key:
                return SimResult(pause=pause)
            
            # Build prompt with historical trajectory (the key fix!)
            user_prompt = _build_user_prompt(pause.buffer, ctx, None, trajectory=trajectory)
            url = (
                f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
                f':generateContent?key={api_key}'
            )
            body = json.dumps({
                'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
                'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 150, 'topP': 0.9},
            }).encode('utf-8')
            try:
                req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    parts_resp = data['candidates'][0]['content']['parts']
                    prediction = ''
                    for part in parts_resp:
                        if 'text' in part:
                            prediction = part['text'].strip()
                            break
                    prediction = _strip_signal_echo(prediction, pause.buffer)
            except Exception as e:
                print(f'[sim] gemini error: {e}')
                prediction = ''
            ctx_files = []
    else:
        prediction, ctx_files = call_gemini(pause.buffer)
    
    latency = int((time.time() - t0) * 1000)
    result = score_prediction(pause, prediction)
    result.latency_ms = latency
    result.context_files = ctx_files
    return result


# ── Reporting ───────────────────────────────────────────────────────────────

def _print_session(sess: TypingSession, pauses: list[PausePoint]):
    """Print a compact session summary."""
    del_pct = f'{sess.deletion_ratio:.0%}'
    print(f'\n{"="*70}')
    print(f'SESSION {sess.index} | {sess.context} | '
          f'{sess.keystroke_count} keys | del={del_pct} | '
          f'{sess.duration_ms}ms')
    print(f'  final: "{sess.final_buffer[:70]}"')
    if not pauses:
        print(f'  (no pauses >= threshold)')
    for i, p in enumerate(pauses):
        cont = _extract_continuation(p.buffer, p.final_text)
        print(f'  pause {i+1}: {p.pause_ms}ms @ {p.position_pct:.0%} '
              f'| buf="{p.buffer[:50]}"')
        if cont:
            print(f'    → typed after: "{cont[:60]}"')


def _print_result(result: SimResult, idx: int):
    """Print one sim result with accuracy."""
    p = result.pause
    print(f'\n  ── pause {idx} ({p.pause_ms}ms @ {p.position_pct:.0%}) ──')
    print(f'  buffer:     "{p.buffer[:60]}"')
    print(f'  predicted:  "{result.prediction[:60]}"')
    print(f'  actual:     "{result.continuation_captured[:60]}"')
    print(f'  overlap:    {result.word_overlap:.0%} | '
          f'prefix: {result.prefix_match_len} chars | '
          f'exact: {result.exact_match} | '
          f'{result.latency_ms}ms')
    if result.context_files:
        print(f'  files:      {", ".join(result.context_files[:4])}')


def _print_summary(results: list[SimResult]):
    """Print aggregate accuracy stats."""
    if not results:
        print('\nno results to summarize')
        return
    overlaps = [r.word_overlap for r in results]
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    prefixes = [r.prefix_match_len for r in results]
    exact = sum(1 for r in results if r.exact_match)

    print(f'\n{"="*70}')
    print(f'SIMULATION SUMMARY — {len(results)} pause points replayed')
    print(f'  word overlap:   avg={sum(overlaps)/len(overlaps):.1%} '
          f'| max={max(overlaps):.1%} | min={min(overlaps):.1%}')
    print(f'  prefix match:   avg={sum(prefixes)/len(prefixes):.1f} chars '
          f'| max={max(prefixes)}')
    print(f'  exact matches:  {exact}/{len(results)} ({exact/len(results):.0%})')
    if latencies:
        print(f'  latency:        avg={sum(latencies)/len(latencies):.0f}ms '
              f'| max={max(latencies)}ms | min={min(latencies)}ms')

    # Best and worst predictions
    by_overlap = sorted(results, key=lambda r: r.word_overlap, reverse=True)
    if by_overlap:
        best = by_overlap[0]
        print(f'\n  BEST:  "{best.pause.buffer[:40]}" → '
              f'overlap={best.word_overlap:.0%}')
        worst = by_overlap[-1]
        print(f'  WORST: "{worst.pause.buffer[:40]}" → '
              f'overlap={worst.word_overlap:.0%}')


# ── Export ──────────────────────────────────────────────────────────────────

def export_results(results: list[SimResult], path: Path):
    """Export sim results to JSONL for analysis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for r in results:
            entry = {
                'buffer': r.pause.buffer,
                'prediction': r.prediction,
                'actual': r.continuation_captured,
                'word_overlap': r.word_overlap,
                'prefix_match': r.prefix_match_len,
                'exact': r.exact_match,
                'latency_ms': r.latency_ms,
                'pause_ms': r.pause.pause_ms,
                'position_pct': r.pause.position_pct,
                'context_files': r.context_files,
                'final_text': r.pause.final_text[:200],
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f'\nexported {len(results)} results to {path}')


# ── Sim memory — per-file learning ─────────────────────────────────────────

SIM_MEMORY_PATH = ROOT / 'logs' / 'sim_memory.json'


def _load_sim_memory() -> dict:
    if SIM_MEMORY_PATH.exists():
        try:
            return json.loads(SIM_MEMORY_PATH.read_text('utf-8', errors='ignore'))
        except Exception:
            pass
    return {'files': {}, 'bugs_found': [], 'bugs_fixed': [], 'runs': 0}


def _save_sim_memory(mem: dict):
    SIM_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    mem['updated'] = datetime.now(timezone.utc).isoformat()
    SIM_MEMORY_PATH.write_text(json.dumps(mem, ensure_ascii=False, indent=1),
                                encoding='utf-8')


def update_sim_memory(results: list[SimResult]):
    """Each sim run teaches the system. Per-file accuracy accumulates."""
    mem = _load_sim_memory()
    mem['runs'] = mem.get('runs', 0) + 1
    files = mem.get('files', {})
    for r in results:
        for f in r.context_files:
            if f not in files:
                files[f] = {'times_selected': 0, 'avg_overlap': 0,
                            'best_overlap': 0, 'worst_overlap': 1.0,
                            'total_overlap': 0, 'learnings': []}
            fm = files[f]
            fm['times_selected'] = fm.get('times_selected', 0) + 1
            fm['total_overlap'] = fm.get('total_overlap', 0) + r.word_overlap
            fm['avg_overlap'] = fm['total_overlap'] / fm['times_selected']
            if r.word_overlap > fm.get('best_overlap', 0):
                fm['best_overlap'] = r.word_overlap
            if r.word_overlap < fm.get('worst_overlap', 1.0):
                fm['worst_overlap'] = r.word_overlap
    mem['files'] = files
    _save_sim_memory(mem)
    return mem


def record_bug_found(mem: dict, bug_id: str, description: str, file: str):
    """Record a bug discovered by sim analysis."""
    mem.setdefault('bugs_found', []).append({
        'id': bug_id, 'desc': description, 'file': file,
        'ts': datetime.now(timezone.utc).isoformat(), 'fixed': False,
    })
    _save_sim_memory(mem)


def record_bug_fixed(mem: dict, bug_id: str, fix_description: str):
    """Record that a sim-discovered bug was fixed."""
    for b in mem.get('bugs_found', []):
        if b['id'] == bug_id:
            b['fixed'] = True
            b['fix'] = fix_description
            b['fixed_ts'] = datetime.now(timezone.utc).isoformat()
    mem.setdefault('bugs_fixed', []).append({
        'id': bug_id, 'fix': fix_description,
        'ts': datetime.now(timezone.utc).isoformat(),
    })
    _save_sim_memory(mem)


# ── Narrate mode — the system explains itself ──────────────────────────────

def _narrate_context_signals() -> dict:
    """Load context signals for the narrative."""
    from src.tc_context_seq001_v001 import load_context
    return load_context(ROOT)


def _narrate_sim_memory() -> dict:
    """Load sim memory for learning stats."""
    return _load_sim_memory()


def _narrate_profile() -> dict | None:
    """Load operator profile if it exists."""
    prof_path = ROOT / 'logs' / 'operator_profile_tc.json'
    if prof_path.exists():
        try:
            return json.loads(prof_path.read_text('utf-8', errors='ignore'))
        except Exception:
            pass
    return None


def print_narrate(sessions: list[TypingSession],
                  results: list[SimResult] | None = None):
    """The system explains itself to you. Plain english, no jargon."""

    ctx = _narrate_context_signals()
    mem = _narrate_sim_memory()
    profile = _narrate_profile()

    print()
    print('═' * 70)
    print('  WHAT THIS SYSTEM IS AND WHAT IT KNOWS ABOUT YOU')
    print('  (the files are talking now)')
    print('═' * 70)

    # ── Chapter 1: What this actually is ──
    print('\n┌─── CHAPTER 1: WHAT AM I? ───┐\n')
    print('  i watch you type.')
    print()
    print('  every keystroke, every pause, every backspace, every word you')
    print('  delete before hitting enter — i see all of it. when you stop')
    print('  typing for a second or two, i try to guess what you\'re about')
    print('  to say next. i use gemini (a fast AI model) to make that guess.')
    print()
    print('  the goal: finish your thought before you finish typing it.')
    print('  a popup appears with what i think you\'ll say next.')
    print()
    print('  right now i\'m not great at it. but i\'m learning.')

    # ── Chapter 2: What I know about you ──
    print('\n┌─── CHAPTER 2: WHAT I KNOW ABOUT YOU ───┐\n')

    si = ctx.get('session_info', {})
    if si:
        cog = si.get('cognitive_state', 'unknown')
        intent = si.get('intent', 'unknown')
        sn = si.get('session_n', '?')
        print(f'  last time you talked to copilot, it was prompt #{sn}.')
        print(f'  your cognitive state was: {cog}')
        print(f'  your intent was: {intent}')
        print()

    op = ctx.get('operator_state', {})
    if op:
        dom = op.get('dominant', 'unknown')
        wpm = op.get('avg_wpm', 0)
        bl = op.get('baselines', {})
        bl_wpm = bl.get('avg_wpm', 0)
        bl_del = bl.get('avg_del', 0)
        print(f'  your dominant state across all sessions: {dom}')
        if bl_wpm:
            print(f'  you type at ~{bl_wpm:.0f} words per minute on average.')
        if bl_del:
            print(f'  you delete {bl_del:.0%} of what you type. that\'s your inner editor.')
        print()

    states = op.get('states', {}) if op else {}
    if states:
        total_states = sum(states.values())
        if total_states > 0:
            print('  how you\'ve been feeling (across all prompts):')
            for state, count in sorted(states.items(), key=lambda x: -x[1]):
                bar = '█' * max(1, int(count / total_states * 30))
                print(f'    {state:12s} {bar} ({count}x)')
            print()

    # Profile shards
    if profile and profile.get('samples', 0) > 0:
        v = profile.get('shards', {}).get('voice', {})
        if v.get('top_words'):
            top5 = list(v['top_words'].keys())[:7]
            print(f'  your most used words: {", ".join(top5)}')
        if v.get('catchphrases'):
            print(f'  your catchphrases: {", ".join(v["catchphrases"][:3])}')
        r = profile.get('shards', {}).get('rhythm', {})
        if r.get('avg_wpm'):
            print(f'  your measured typing speed: {r["avg_wpm"]:.0f} wpm')
        d = profile.get('shards', {}).get('deletions', {})
        if d.get('top_deleted_words'):
            tdw = list(d['top_deleted_words'].keys())[:5]
            print(f'  words you delete most: {", ".join(tdw)}')
        print()

    # Unsaid threads
    unsaid = ctx.get('unsaid_threads', [])
    if unsaid:
        real_unsaid = [u for u in unsaid if u.strip()]
        if real_unsaid:
            print('  things you typed then deleted (i still saw them):')
            for u in real_unsaid[:5]:
                print(f'    - "{u[:80]}"')
            print()

    # ── Chapter 3: What is "organism health"? ──
    print('┌─── CHAPTER 3: WHAT IS "ORGANISM HEALTH"? ───┐\n')
    print('  the codebase — all these python files — is treated like a')
    print('  living organism. each file is an organ. here\'s the metaphor:')
    print()
    print('  • HEAT MAP      = which files are getting edited the most')
    print('                     (hot = lots of attention, cold = stable)')
    print('  • ENTROPY        = uncertainty. when a file gets edited, entropy')
    print('                     goes up (we\'re less sure it\'s correct).')
    print('                     when it\'s tested and confirmed, entropy goes down.')
    print('  • BUG DEMONS     = bugs that won\'t die. each bug gets a name and')
    print('                     a personality. if it keeps coming back, it\'s "chronic"')
    print('  • CLOTS          = dead code. files nobody imports. bloated modules.')
    print('                     like cholesterol in arteries — slows the whole thing.')
    print('  • COGNITIVE STATE = YOUR state. frustrated? focused? hesitant?')
    print('                     the system reads this from how you type.')
    print()

    org = ctx.get('organism_narrative', '')
    if org:
        print(f'  the organism\'s own words:')
        print(f'  "{org}"')
        print()

    # Heat
    heat = ctx.get('heat_map', [])
    if heat:
        print('  right now, the hottest files (most actively edited):')
        for h in heat[:5]:
            bar = '🔥' * max(1, min(5, int(h['heat'] * 5)))
            print(f'    {h["mod"]:35s} {bar} (heat={h["heat"]:.2f})')
        print()

    # Entropy
    ent = ctx.get('entropy', {})
    if ent:
        g = ent.get('global', 0)
        hp = ent.get('high_pct', 0)
        hp_display = hp if hp <= 1 else hp / 100  # normalize if stored as raw pct
        print(f'  global entropy: {g:.2f} (0=certain, 1=chaos)')
        print(f'  {hp_display:.0%} of modules are high-entropy (uncertain)')
        hotspots = ent.get('hotspots', [])
        if hotspots:
            print('  most uncertain modules:')
            for h in hotspots[:4]:
                print(f'    {h["mod"]:35s} H={h["H"]:.3f}')
        print()

    # Bug demons
    bugs = ctx.get('bug_demons', [])
    if bugs:
        print('  active bug demons:')
        for b in bugs[:5]:
            print(f'    🐛 {b["demon"]} — haunting {b["host"]}')
        print()

    # Critical bugs
    crits = ctx.get('critical_bugs', [])
    if crits:
        print('  critical issues:')
        for c in crits[:4]:
            print(f'    🔴 {c["type"]} in {c["file"]}')
        print()

    # ── Chapter 4: What the sim found ──
    print('┌─── CHAPTER 4: WHAT I LEARNED FROM REPLAYING YOUR TYPING ───┐\n')

    total_sess = len(sessions)
    total_keys = sum(s.keystroke_count for s in sessions)
    total_bs = sum(s.backspace_count for s in sessions)
    total_pauses = sum(len(find_pause_points(s)) for s in sessions)

    print(f'  i replayed {total_sess} of your typing sessions.')
    print(f'  you pressed {total_keys} keys total. {total_bs} of those were backspace.')
    if total_keys > 0:
        print(f'  that\'s a {total_bs/total_keys:.0%} deletion rate.')
    print(f'  you paused long enough to trigger prediction {total_pauses} times.')
    print()

    # Session personality snapshots
    if sessions:
        longest = max(sessions, key=lambda s: s.duration_ms)
        most_del = max(sessions, key=lambda s: s.deletion_ratio)
        print(f'  your longest session: #{longest.index} '
              f'({longest.duration_ms/1000:.0f}s) — "{longest.final_buffer[:50]}"')
        print(f'  your most edited session: #{most_del.index} '
              f'({most_del.deletion_ratio:.0%} deleted) — "{most_del.final_buffer[:50]}"')
        print()

    if results:
        overlaps = [r.word_overlap for r in results]
        avg_ov = sum(overlaps) / len(overlaps)
        best = max(results, key=lambda r: r.word_overlap)
        worst = min(results, key=lambda r: r.word_overlap)
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]

        print(f'  i made {len(results)} predictions. here\'s how they went:')
        print(f'    average accuracy (word overlap): {avg_ov:.1%}')
        print(f'    best:  {best.word_overlap:.0%} — "{best.pause.buffer[-40:]}"')
        print(f'    worst: {worst.word_overlap:.0%} — "{worst.pause.buffer[-40:]}"')
        if latencies:
            print(f'    average response time: {sum(latencies)/len(latencies):.0f}ms')
        print()

        good = sum(1 for r in results if r.word_overlap > 0.15)
        mid = sum(1 for r in results if 0.05 <= r.word_overlap <= 0.15)
        bad = sum(1 for r in results if r.word_overlap < 0.05)
        print(f'    {good} good guesses (>15% overlap)')
        print(f'    {mid} okay guesses (5-15%)')
        print(f'    {bad} bad guesses (<5%)')
        print()

        # What the context agent keeps selecting
        ctx_counts: dict[str, int] = {}
        for r in results:
            for f in r.context_files:
                ctx_counts[f] = ctx_counts.get(f, 0) + 1
        if ctx_counts:
            top_ctx = sorted(ctx_counts.items(), key=lambda x: -x[1])[:3]
            print('  the AI kept looking at these files for context:')
            for name, cnt in top_ctx:
                short = name.split('_seq')[0] if '_seq' in name else name
                print(f'    {short}: {cnt}x')
            print()
    else:
        print('  (no live predictions yet — run with --live to actually test)')
        print()

    # Sim memory learnings
    files = mem.get('files', {})
    runs = mem.get('runs', 0)
    bugs_found = mem.get('bugs_found', [])
    bugs_fixed = mem.get('bugs_fixed', [])
    if files:
        print(f'  sim has run {runs} time(s). tracking {len(files)} files.')
        # Most selected files
        by_sel = sorted(files.items(), key=lambda x: -x[1].get('times_selected', 0))
        if by_sel:
            top = by_sel[0]
            short_name = top[0].split('_seq')[0] if '_seq' in top[0] else top[0]
            print(f'  most selected context file: {short_name} '
                  f'({top[1]["times_selected"]}x, {top[1]["avg_overlap"]:.1%} avg accuracy)')
            if top[1]['avg_overlap'] < 0.05:
                print(f'    ^ that file is selected a LOT but barely helps. '
                      f'context agent might be fixated.')
        print()

    if bugs_found:
        fixed_ids = {b['id'] for b in bugs_fixed}
        unfixed = [b for b in bugs_found if b['id'] not in fixed_ids and not b.get('fixed')]
        print(f'  bugs found by the sim: {len(bugs_found)}')
        print(f'  bugs fixed: {len(bugs_fixed)}')
        if unfixed:
            print(f'  still unfixed:')
            for b in unfixed[:3]:
                print(f'    - {b["desc"][:70]}')
        print()

    # ── Chapter 5: The bottom line ──
    print('┌─── CHAPTER 5: SO WHAT DOES ALL THIS MEAN? ───┐\n')
    print('  you type, pause, delete, rewrite, and eventually hit enter.')
    print('  this system sees ALL of that. it builds a model of how you think.')
    print()
    print('  "organism health" = how well the CODEBASE is doing.')
    print('  "operator state"  = how well YOU are doing.')
    print()
    print('  when the organism is sick (lots of bugs, high entropy, dead code),')
    print('  the AI should be more careful — more precise, less creative.')
    print('  when you\'re frustrated (high deletion, lots of rewrites),')
    print('  the AI should be more direct — shorter answers, less fluff.')
    print()
    print('  the thought completer uses ALL of this to guess your next words.')
    print('  your cognitive state, the codebase health, what files are hot,')
    print('  what you deleted, what you almost said — it\'s all signal.')
    print()

    # File profiles — personality
    fprofs = ctx.get('file_profiles', [])
    if fprofs:
        print('  some files even have personalities:')
        for fp in fprofs[:4]:
            fears = ', '.join(fp['fears'][:2]) if fp['fears'] else 'nothing'
            print(f'    {fp["mod"]}: {fp["personality"]} '
                  f'(hesitation={fp["hes"]:.0%}, fears: {fears})')
        print()

    print('  that\'s it. that\'s the system. it watches you type and tries')
    print('  to read your mind. sometimes it works. usually it doesn\'t.')
    print('  but it\'s getting better, one sim run at a time.')

    print('\n' + '═' * 70)
    print('  END OF NARRATION')
    print('═' * 70)


# ── Narrative transcript ────────────────────────────────────────────────────

def _load_journal_arc(n: int = 10) -> list[dict]:
    """Load last n prompt journal entries for narrative context."""
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return []
    entries = []
    with open(journal, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-n:]


_COG_EMOJI = {
    'frustrated': '😤', 'hesitant': '🤔', 'focused': '🎯',
    'abandoned': '💨', 'unknown': '🌀', 'neutral': '😐',
}
_INTENT_VERB = {
    'debugging': 'hunting bugs in', 'building': 'constructing',
    'exploring': 'poking around', 'unknown': 'staring at',
    'fixing': 'patching up',
}


def print_transcript(sessions: list[TypingSession],
                     results: list[SimResult] | None = None):
    """Print the sim as a comedy narrative transcript."""
    journal = _load_journal_arc(15)

    print('\n' + '═' * 70)
    print('  THE THOUGHT COMPLETER TAPES')
    print('  a tragicomedy in keystrokes')
    print('═' * 70)

    # Act 1 — the journal arc (what the operator was going through)
    if journal:
        print('\n╔══ ACT 1: THE OPERATOR\'S DESCENT ══╗\n')
        for e in journal[-8:]:
            n = e.get('session_n', '?')
            cog = e.get('cognitive_state', 'unknown')
            intent = e.get('intent', 'unknown')
            emoji = _COG_EMOJI.get(cog, '❓')
            msg = e.get('msg', '')[:70]
            dels = e.get('deleted_words', [])
            sig = e.get('signals', {})
            del_r = sig.get('deletion_ratio', 0)

            print(f'  {emoji} prompt #{n} — {intent}, {cog}')
            print(f'     "{msg}"')
            if dels:
                print(f'     [whispered then swallowed: "{", ".join(dels)}"]')
            if del_r > 0.3:
                print(f'     [REWROTE {del_r:.0%} of this — the inner editor was fighting]')
            print()

    # Act 2 — the sessions themselves
    print('╔══ ACT 2: THE REPLAY ══╗\n')

    for sess in sessions:
        del_pct = f'{sess.deletion_ratio:.0%}'
        dur_s = sess.duration_ms / 1000
        drama = ''
        if sess.deletion_ratio > 0.3:
            drama = ' [THE BACKSPACE WAS DOING OVERTIME]'
        elif dur_s > 600:
            drama = f' [sat there for {dur_s/60:.0f} minutes]'
        elif sess.keystroke_count < 15:
            drama = ' [barely typed anything]'

        print(f'  ┌─ SESSION {sess.index} ─{drama}')
        print(f'  │ {sess.keystroke_count} keys, {del_pct} deleted, '
              f'{dur_s:.0f}s in the chair')
        print(f'  │ final: "{sess.final_buffer[:65]}"')

        pauses = find_pause_points(sess)
        if not pauses:
            print(f'  │ (typed without pausing. a rare confident moment.)')
        else:
            for i, p in enumerate(pauses):
                pause_s = p.pause_ms / 1000
                cont = _extract_continuation(p.buffer, p.final_text)
                if pause_s > 30:
                    pause_note = f'stared at screen for {pause_s:.0f}s'
                elif pause_s > 5:
                    pause_note = f'{pause_s:.1f}s pause (thinking)'
                else:
                    pause_note = f'{pause_s:.1f}s hesitation'
                print(f'  │')
                print(f'  │  ⏸  {pause_note} at "{p.buffer[-40:]}"')
                if cont:
                    print(f'  │  ▶  then typed: "{cont[:50]}"')
        print(f'  └─────\n')

    # Act 3 — the predictions (if we have live results)
    if results:
        print('╔══ ACT 3: THE AI TRIES TO READ MINDS ══╗\n')
        good = [r for r in results if r.word_overlap > 0.15]
        bad = [r for r in results if r.word_overlap < 0.05]
        ok = [r for r in results if 0.05 <= r.word_overlap <= 0.15]

        for r in results:
            buf_short = r.pause.buffer[-45:]
            pred_short = r.prediction[:50]
            actual_short = r.continuation_captured[:50]
            ov = r.word_overlap

            if ov > 0.2:
                verdict = '✨ ALMOST READ THEIR MIND'
            elif ov > 0.1:
                verdict = '🤷 wrong words, right vibe'
            elif ov > 0.03:
                verdict = '😬 technically english'
            else:
                verdict = '💀 completely wrong planet'

            # duplicate context file comedy
            unique_ctx = list(dict.fromkeys(r.context_files))
            if len(r.context_files) != len(unique_ctx):
                ctx_note = f' [selected {r.context_files[0]} TWICE — thats the bug]'
            elif len(set(r.context_files)) == 1 and len(r.context_files) > 1:
                ctx_note = f' [all {len(r.context_files)} context files are the SAME file]'
            else:
                ctx_note = ''

            print(f'  operator: "...{buf_short}"')
            print(f'  AI said:  "{pred_short}"')
            print(f'  reality:  "{actual_short}"')
            print(f'  {verdict} ({ov:.0%} overlap, {r.latency_ms}ms){ctx_note}')
            print()

        # Epilogue
        avg_ov = sum(r.word_overlap for r in results) / len(results) if results else 0
        print('╔══ EPILOGUE ══╗\n')
        print(f'  {len(results)} predictions attempted')
        print(f'  {len(good)} had a clue, {len(ok)} were vibing, {len(bad)} were fiction')
        print(f'  average overlap: {avg_ov:.1%}')
        if avg_ov < 0.1:
            print(f'  verdict: the AI is writing fanfiction, not predictions')
        elif avg_ov < 0.2:
            print(f'  verdict: occasionally psychic, mostly just chatty')
        else:
            print(f'  verdict: getting there — the signal is real')

        # The bugs found
        ctx_counts = {}
        for r in results:
            for f in r.context_files:
                ctx_counts[f] = ctx_counts.get(f, 0) + 1
        if ctx_counts:
            top = sorted(ctx_counts.items(), key=lambda x: x[1], reverse=True)
            if top[0][1] > len(results) * 0.5:
                print(f'\n  🐛 BUG SPOTTED: context agent selected "{top[0][0]}" '
                      f'in {top[0][1]}/{len(results)} predictions')
                print(f'     thats not context selection — thats a fixation')

    print('\n' + '═' * 70)
    print('  END OF TAPES')
    print('═' * 70)


# ── Fix engine — sim identifies and patches bugs ───────────────────────────

def diagnose_from_results(results: list[SimResult]) -> list[dict]:
    """Analyze sim results to identify patchable bugs."""
    bugs = []

    # Bug: context agent always selects same files
    ctx_counts: dict[str, int] = {}
    for r in results:
        for f in r.context_files:
            ctx_counts[f] = ctx_counts.get(f, 0) + 1
    total = len(results) or 1
    for f, count in ctx_counts.items():
        if count > total * 0.5:
            bugs.append({
                'id': f'static_context_{f.split("_seq")[0]}',
                'severity': 'high',
                'file': 'src/tc_context_seq001_v001_agent_seq001_v001.py',
                'desc': f'context agent selected "{f}" in {count}/{total} '
                        f'({count/total:.0%}) predictions — not adapting to buffer',
                'fix': 'deduplicate_registry_results',
            })

    # Bug: duplicate context files in single prediction
    dup_count = sum(1 for r in results
                    if len(r.context_files) != len(set(r.context_files)))
    if dup_count > 0:
        bugs.append({
            'id': 'duplicate_context',
            'severity': 'high',
            'file': 'src/tc_context_seq001_v001_agent_seq001_v001.py',
            'desc': f'{dup_count}/{total} predictions had duplicate context files '
                    f'— registry has multiple entries with same stem name',
            'fix': 'deduplicate_registry_results',
        })

    # Bug: zero overlap predictions (context completely wrong)
    zero_count = sum(1 for r in results if r.word_overlap == 0)
    if zero_count > total * 0.3:
        bugs.append({
            'id': 'zero_overlap',
            'severity': 'medium',
            'file': 'src/tc_context_seq001_v001_agent_seq001_v001.py',
            'desc': f'{zero_count}/{total} predictions had 0% word overlap '
                    f'— stopwords may be filtering meaningful words',
            'fix': 'reduce_stopwords',
        })

    return bugs


def apply_fix(bug: dict, dry: bool = False) -> str:
    """Apply a code fix for a diagnosed bug. Returns description of fix."""
    fix_type = bug.get('fix', '')

    if fix_type == 'deduplicate_registry_results':
        target = ROOT / 'src' / 'tc_context_seq001_v001_agent_seq001_v001.py'
        code = target.read_text('utf-8')
        old = "    scored.sort(key=lambda x: x['score'], reverse=True)\n    return scored[:max_files]"
        new = ("    scored.sort(key=lambda x: x['score'], reverse=True)\n"
               "    # Deduplicate by stem name — registry has multiple entries per module\n"
               "    seen_names = set()\n"
               "    deduped = []\n"
               "    for s in scored:\n"
               "        stem = s['name'].split('_seq')[0] if '_seq' in s['name'] else s['name']\n"
               "        if stem not in seen_names:\n"
               "            seen_names.add(stem)\n"
               "            deduped.append(s)\n"
               "    return deduped[:max_files]")
        if old not in code:
            return 'SKIP — code already patched or changed'
        if dry:
            return f'WOULD patch: deduplicate context files in select_context_files()'
        target.write_text(code.replace(old, new), 'utf-8')
        return 'PATCHED: added deduplication by stem name in select_context_files()'

    if fix_type == 'reduce_stopwords':
        target = ROOT / 'src' / 'tc_context_seq001_v001_agent_seq001_v001.py'
        code = target.read_text('utf-8')
        # These words are meaningful in this codebase, not generic
        words_to_unblock = ['thought', 'complete', 'completing', 'completion',
                            'select', 'selection', 'profile', 'natural', 'naturally',
                            'context', 'agent', 'prompt']
        removed = []
        for w in words_to_unblock:
            if f"'{w}'" in code or f" {w} " in code:
                removed.append(w)
        # The fix: add an allowlist that overrides stopwords for this codebase
        old_extract = ("def _extract_mentions(buffer: str) -> list[str]:\n"
                       "    \"\"\"Extract module/file names mentioned in the buffer text.\n"
                       "    \n"
                       "    Strongly prefers underscore_names (likely module refs) over single words.\n"
                       "    \"\"\"")
        new_extract = ("# Words that ARE meaningful in this codebase despite looking generic\n"
                       "_CODEBASE_TERMS = frozenset(\n"
                       "    'thought completer completion context select selection agent '\n"
                       "    'profile prompt entropy drift reactor pulse harvest '\n"
                       "    'pigeon compiler rename registry manifest '\n"
                       "    'buffer keyboard keystroke typing pause popup '\n"
                       "    'narrative organism consciousness shard memory '.split()\n"
                       ")\n\n\n"
                       "def _extract_mentions(buffer: str) -> list[str]:\n"
                       "    \"\"\"Extract module/file names mentioned in the buffer text.\n"
                       "    \n"
                       "    Strongly prefers underscore_names (likely module refs) over single words.\n"
                       "    \"\"\"")
        if old_extract not in code:
            return 'SKIP — _extract_mentions signature changed'
        if dry:
            return f'WOULD patch: add codebase-specific term allowlist to bypass stopwords'
        code = code.replace(old_extract, new_extract)
        # Also patch the filter condition to check allowlist
        old_filter = ("        if len(w) > 4 and w not in _STOPWORDS and w not in seen:")
        new_filter = ("        if len(w) > 4 and (w in _CODEBASE_TERMS or w not in _STOPWORDS) and w not in seen:")
        code = code.replace(old_filter, new_filter)
        target.write_text(code, 'utf-8')
        return f'PATCHED: added _CODEBASE_TERMS allowlist — {len(removed)} words unblocked'

    return f'UNKNOWN fix type: {fix_type}'


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer sim — replay & score')
    p.add_argument('--n', type=int, default=5, help='number of recent sessions')
    p.add_argument('--live', action='store_true', help='call Gemini (costs API)')
    p.add_argument('--session', type=int, default=None, help='specific session index')
    p.add_argument('--min-len', type=int, default=8, help='min buffer length')
    p.add_argument('--pause-ms', type=int, default=DEFAULT_PAUSE_MS, help='pause threshold')
    p.add_argument('--export', type=str, default=None, help='export path (.jsonl)')
    p.add_argument('--context', type=str, default=None, help='filter by context (editor/chat)')
    p.add_argument('--transcript', action='store_true', help='comedy narrative transcript')
    p.add_argument('--fix', action='store_true', help='diagnose + apply fixes from sim data')
    p.add_argument('--fix-dry', action='store_true', help='diagnose only, show what would fix')
    p.add_argument('--narrate', action='store_true', help='plain english explanation of everything')
    p.add_argument('--historical', action='store_true', help='use historical context for each pause (fixes context mismatch bug)')
    args = p.parse_args()

    print(f'[sim] extracting sessions from {KEYSTROKE_LOG.name}...')
    sessions = extract_sessions(min_buffer_len=args.min_len)
    print(f'[sim] found {len(sessions)} sessions (min {args.min_len} chars)')

    if args.context:
        sessions = [s for s in sessions if s.context == args.context]
        print(f'[sim] filtered to {len(sessions)} {args.context} sessions')

    if args.session is not None:
        sessions = [s for s in sessions if s.index == args.session]
        if not sessions:
            print(f'[sim] session {args.session} not found')
            return
    else:
        sessions = sessions[-args.n:]

    all_results: list[SimResult] = []

    for sess in sessions:
        pauses = find_pause_points(sess, pause_ms=args.pause_ms)
        if not args.transcript:
            _print_session(sess, pauses)

        if args.live and pauses:
            for i, pause in enumerate(pauses):
                try:
                    result = replay_pause_live(pause, use_historical_ctx=args.historical)
                    if not args.transcript:
                        _print_result(result, i + 1)
                    all_results.append(result)
                except Exception as e:
                    print(f'  pause {i+1} error: {e}')
                # Rate limit: 200ms between API calls
                if i < len(pauses) - 1:
                    time.sleep(0.2)

    # Transcript mode — comedy narrative
    if args.transcript:
        print_transcript(sessions, all_results if all_results else None)

    # Narrate mode — plain english explanation
    if args.narrate:
        print_narrate(sessions, all_results if all_results else None)

    if all_results:
        if not args.transcript:
            _print_summary(all_results)
        if args.export:
            export_results(all_results, Path(args.export))
        # Update sim memory — each file learns
        mem = update_sim_memory(all_results)
        file_count = len(mem.get('files', {}))
        print(f'[sim-memory] updated — {file_count} files tracked, '
              f'run #{mem.get("runs", 0)}')

    # Fix mode — diagnose and patch
    if args.fix or args.fix_dry:
        # Load previous results if we didn't just run live
        if not all_results:
            result_path = ROOT / 'logs' / 'sim_results.jsonl'
            if result_path.exists():
                print(f'[fix] loading previous results from {result_path.name}...')
                with open(result_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                d = json.loads(line)
                                pp = PausePoint(ts=0, buffer=d['buffer'],
                                                pause_ms=d.get('pause_ms', 0),
                                                buffer_after='',
                                                final_text=d.get('final_text', ''),
                                                position_pct=d.get('position_pct', 0))
                                sr = SimResult(pause=pp,
                                               prediction=d.get('prediction', ''),
                                               word_overlap=d.get('word_overlap', 0),
                                               prefix_match_len=d.get('prefix_match', 0),
                                               exact_match=d.get('exact', False),
                                               latency_ms=d.get('latency_ms', 0),
                                               context_files=d.get('context_files', []))
                                all_results.append(sr)
                            except Exception:
                                pass
                print(f'[fix] loaded {len(all_results)} previous results')

        if not all_results:
            print('[fix] no results to analyze — run with --live first')
            return

        bugs = diagnose_from_results(all_results)
        mem = _load_sim_memory()
        if not bugs:
            print('[fix] no bugs found — predictions are... fine? somehow?')
        else:
            print(f'\n[fix] {len(bugs)} bug(s) diagnosed:\n')
            for bug in bugs:
                sev = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                    bug['severity'], '⚪')
                print(f'  {sev} [{bug["id"]}] {bug["desc"]}')
                print(f'     file: {bug["file"]}')
                record_bug_found(mem, bug['id'], bug['desc'], bug['file'])
                result = apply_fix(bug, dry=args.fix_dry)
                prefix = 'DRY' if args.fix_dry else 'FIX'
                print(f'     {prefix}: {result}')
                if not args.fix_dry and 'PATCHED' in result:
                    record_bug_fixed(mem, bug['id'], result)
                print()

    if not args.live and not args.fix and not args.fix_dry:
        total_pauses = sum(len(find_pause_points(s, args.pause_ms)) for s in sessions)
        print(f'\n[sim] dry run complete — {total_pauses} pause points found')
        print(f'[sim] add --live to replay through Gemini and score accuracy')
        print(f'[sim] add --transcript for the comedy version')
        print(f'[sim] add --fix to diagnose and patch bugs from sim data')


if __name__ == '__main__':
    main()
