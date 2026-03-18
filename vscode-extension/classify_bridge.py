"""classify_bridge.py â€” VS Code extension â†” Python classifier bridge.

Reads keystroke events from stdin, computes message metrics, classifies
cognitive state using the existing operator_stats classifiers, updates
operator_profile.md, and refreshes copilot-instructions.md in-place.

Integrates deep operator profiling:
  - Rework detector: score post-response typing â†’ AI miss rate
  - Query memory: fingerprint queries, accumulate unsaid/abandoned
  - File heat map: correlate hesitation with recently-touched modules
  - Unsaid analyzer: reconstruct deleted drafts, topic pivots

Every LLM_REWRITE_EVERY *submitted* messages, calls DeepSeek to synthesize
rich behavioral coaching from all signals, written to operator_coaching.md.

Stdin:  {"events": [...], "submitted": bool,
         "post_response_events": [...], "query_text": str}
Argv:   <repo_root>
Stdout: {"state", "hesitation", "wpm", "coaching_updated", "rework_verdict"}
"""
import sys
import json
import os
import importlib.util
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

LLM_REWRITE_EVERY = 8


def _load_pigeon_module(root: Path, pattern: str):
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location('_pigeonmod', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _compute_metrics(events: list, submitted: bool) -> tuple:
    inserts  = [e for e in events if e.get('type') == 'insert']
    deletes  = [e for e in events if e.get('type') == 'backspace']
    pauses   = [e for e in events if e.get('type') == 'pause']
    total    = max(len(events), 1)
    pause_ms = [e.get('duration_ms', 0) for e in pauses]
    ts_vals  = [e['ts'] for e in events if 'ts' in e]
    start_ms = min(ts_vals) if ts_vals else 0.0
    end_ms   = max(ts_vals) if ts_vals else 1.0
    dur_ms   = max(end_ms - start_ms, 1.0)
    del_ratio   = len(deletes) / total
    pause_ratio = sum(pause_ms) / dur_ms
    hes  = min(1.0, round(del_ratio * 0.6 + pause_ratio * 0.4, 3))
    wpm  = round((len(inserts) / 5) / max(dur_ms / 60_000, 0.001), 1)
    return {
        'total_keystrokes': len(events),
        'total_inserts':    len(inserts),
        'total_deletions':  len(deletes),
        'typing_pauses':    [{'duration_ms': d} for d in pause_ms],
        'start_time_ms':    int(start_ms),
        'end_time_ms':      int(end_ms),
        'hesitation_score': hes,
        'deleted':          not submitted,
        'ts':               datetime.now(timezone.utc).isoformat(),
    }, wpm


def _count_submitted(history: list) -> int:
    return sum(1 for h in history if h.get('submitted', True))


def _parse_history(root: Path) -> list:
    import re
    prof = root / 'operator_profile.md'
    if not prof.exists():
        return []
    try:
        text = prof.read_text(encoding='utf-8')
        m = re.search(r'<!--\s*DATA\s*(.*?)\s*DATA\s*-->', text, re.DOTALL)
        if m:
            return json.loads(m.group(1).strip()).get('history', [])
    except Exception:
        pass
    return []


def _build_prompt(history: list, rework_stats: dict,
                  query_mem: dict, heat_map: dict,
                  composition: dict | None = None) -> str:
    """Build enhanced DeepSeek prompt with all deep profile signals."""
    from collections import Counter
    n = len(history)
    submitted = _count_submitted(history)
    states = [h.get('state', 'neutral') for h in history]
    state_dist = dict(Counter(states).most_common())
    wpms = [h['wpm'] for h in history if 'wpm' in h]
    hess = [h['hesitation'] for h in history if 'hesitation' in h]
    dels = [h['del_ratio'] for h in history if 'del_ratio' in h]
    slots = [h.get('slot', '') for h in history if h.get('slot')]
    avg_wpm = round(sum(wpms)/max(len(wpms),1), 1)
    avg_hes = round(sum(hess)/max(len(hess),1), 3)
    avg_del = round(sum(dels)/max(len(dels),1)*100, 1)
    slot_dist = dict(Counter(slots).most_common(3))
    recent_lines = '\n'.join(
        f'  msg{i+1}: {h.get("state","?")} wpm={h.get("wpm",0)} '
        f'del={round(h.get("del_ratio",0)*100)}% hes={h.get("hesitation",0)} '
        f'sub={h.get("submitted",True)} slot={h.get("slot","?")}'
        for i, h in enumerate(history[-8:])
    )
    rework_block = (
        f'  miss_rate={rework_stats.get("miss_rate","?")} '
        f'({rework_stats.get("miss_count","?")} misses / '
        f'{rework_stats.get("total_responses","?")} responses)\n'
        f'  worst queries: {rework_stats.get("worst_queries", [])}'
    ) if rework_stats else '  no rework data yet'
    gaps_block = '\n'.join(
        f'  [{g["count"]}x] {g["query"]}'
        for g in query_mem.get('persistent_gaps', [])
    ) or '  none yet'
    abandon_block = '\n'.join(
        f'  {a}' for a in query_mem.get('recent_abandons', [])
    ) or '  none'
    complex_block = '\n'.join(
        f'  {c["module"]} avg_hes={c["avg_hes"]} avg_wpm={c["avg_wpm"]} '
        f'misses={c["miss_count"]}/{c["samples"]}'
        for c in heat_map.get('complex_files', [])
    ) or '  no data yet'
    miss_files_block = '\n'.join(
        f'  {m["module"]} miss_rate={m["miss_rate"]}'
        for m in heat_map.get('high_miss_files', [])
    ) or '  none'

    # Chat composition signals from OS-level keystroke reconstruction
    comp_block = '  no composition data yet'
    if composition:
        deleted_words = [w.get('word', '') for w in composition.get('deleted_words', [])]
        rewrites = composition.get('rewrites', [])
        comp_block = (
            f'  deletion_ratio={composition.get("deletion_ratio", 0)} '
            f'peak_buffer="{composition.get("peak_buffer", "")[:80]}"\n'
            f'  deleted_words: {deleted_words[:10]}\n'
            f'  rewrites: {len(rewrites)} '
            f'hesitation_windows: {len(composition.get("hesitation_windows", []))}'
        )

    return f"""You are a behavioral AI coach embedded in a VS Code extension.
Your output is injected DIRECTLY into a Copilot system prompt â€” write INSTRUCTIONS for the AI, not a report.

OPERATOR TYPING HISTORY ({n} messages, {submitted} submitted):
  states: {state_dist} | avg WPM: {avg_wpm} | avg_hes: {avg_hes} | avg_del: {avg_del}%
  active slots: {slot_dist}
  recent 8:
{recent_lines}

AI RESPONSE QUALITY (rework after response):
{rework_block}

PERSISTENT GAPS (same question {8}x+ = AI keeps failing here):
{gaps_block}

ABANDONED/UNSAID (what operator typed then deleted â€” true failure surface):
{abandon_block}

FILE COMPLEXITY DEBT (high hesitation when these modules are in context):
{complex_block}

HIGH AI-MISS FILES (AI responses fail most often around these modules):
{miss_files_block}

CHAT COMPOSITION (OS-level keystroke reconstruction — deleted words are unsaid intent):
{comp_block}

Write behavioral coaching for Copilot. Requirements:
1. One sentence: operator's dominant pattern + what their rework rate reveals
2. 4\u20136 bullets: precise behavioral instructions for next session
3. Call out persistent gaps by name \u2014 the AI must fix these proactively
4. For each high-miss file: prescribe a different response strategy
5. For abandoned themes: the AI should proactively surface these
6. For deleted words: these reveal what the operator WANTED to say but chose not to \u2014 address the underlying need
7. One sentence: what this operator is building toward

Surgical and specific. Every word changes AI behavior. Max 230 words. Markdown bullets only."""


def _call_deepseek(prompt: str, api_key: str) -> str | None:
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 320, 'temperature': 0.35,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions', data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())['choices'][0]['message']['content'].strip()
    except Exception:
        return None


def _should_rewrite(history: list, coaching_path: Path) -> bool:
    import re
    count = _count_submitted(history)
    if count == 0 or count % LLM_REWRITE_EVERY != 0:
        return False
    if coaching_path.exists():
        try:
            m = re.search(r'<!-- coaching:count=(\d+) -->',
                          coaching_path.read_text('utf-8'))
            if m and int(m.group(1)) == count:
                return False
        except Exception:
            pass
    return True


def _load_recent_chat_keystrokes(root: Path, window_ms: int = 120_000) -> list:
    """Read recent chat-context keystrokes from os_keystrokes.jsonl.
    Returns events within the last window_ms that came from chat context.
    These are the keystrokes the TextDocument API can't see.
    """
    log = root / 'logs' / 'os_keystrokes.jsonl'
    if not log.exists():
        return []
    try:
        lines = log.read_text(encoding='utf-8').strip().splitlines()
        if not lines:
            return []
        now_ms = int(__import__('time').time() * 1000)
        cutoff = now_ms - window_ms
        chat_events = []
        # Read from end (most recent) until we pass the window
        for line in reversed(lines):
            try:
                evt = json.loads(line)
                if evt.get('ts', 0) < cutoff:
                    break
                if evt.get('context') == 'chat':
                    chat_events.append(evt)
            except json.JSONDecodeError:
                continue
        chat_events.reverse()
        return chat_events
    except OSError:
        return []


def _load_chat_composition(root: Path) -> dict | None:
    """Load latest chat composition analysis.
    Uses chat_composition_analyzer to reconstruct deleted words, rewrites,
    hesitation from raw OS hook keystrokes — regardless of context tag.
    This is the real signal: the OS hook captures everything, the analyzer
    reconstructs the full composition including what was deleted.
    """
    try:
        analyzer_path = root / 'client' / 'chat_composition_analyzer.py'
        if not analyzer_path.exists():
            return None
        spec = importlib.util.spec_from_file_location('_comp_analyzer', analyzer_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.analyze_and_log(root)
        return result
    except Exception:
        return None


def main():
    root      = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    payload   = json.loads(sys.stdin.read())
    events    = payload.get('events', [])
    submitted = payload.get('submitted', True)
    post_evts = payload.get('post_response_events', [])
    query_txt = payload.get('query_text', '')

    sys.path.insert(0, str(root))

    # ── Merge OS-level chat keystrokes into event stream ──────────────
    chat_keys = _load_recent_chat_keystrokes(root)
    if chat_keys:
        # Convert os_hook format → classify format for unified analysis
        for ck in chat_keys:
            etype = ck.get('type', 'insert')
            if etype in ('insert', 'backspace', 'submit', 'discard'):
                events.append({
                    'ts': ck['ts'],
                    'type': 'backspace' if etype == 'backspace' else 'insert',
                    'context': 'chat',
                    'buffer': ck.get('buffer', ''),
                })

    metrics, wpm = _compute_metrics(events, submitted)

    # ── Chat composition analysis (deleted words, rewrites, hesitation) ──
    chat_comp = _load_chat_composition(root)
    chat_state_override = None
    if chat_comp:
        cs = chat_comp.get('chat_state', {})
        if cs.get('confidence', 0) > 0.6:
            chat_state_override = cs

    # â"€â"€ Classify state â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    stats_mod = _load_pigeon_module(root, 'src/operator_stats_seq008*.py')
    state = 'neutral'
    if stats_mod:
        # Load operator history for self-calibrating baselines
        baselines = {}
        try:
            history = _parse_history(root)
            baselines = stats_mod.compute_baselines(history)
        except Exception:
            pass
        state = stats_mod.classify_state(metrics, baselines)
        # Override with chat composition state if stronger signal
        if chat_state_override and chat_state_override.get('confidence', 0) > 0.65:
            state = chat_state_override['state']
        metrics['state'] = state
        # Enrich metrics with composition data
        if chat_comp:
            metrics['chat_deleted_words'] = [w['word'] for w in chat_comp.get('deleted_words', [])]
            metrics['chat_rewrites'] = len(chat_comp.get('rewrites', []))
            metrics['chat_deletion_ratio'] = chat_comp.get('deletion_ratio', 0)
            metrics['chat_peak_buffer'] = chat_comp.get('peak_buffer', '')
        try:
            stats_mod.OperatorStats(
                str(root / 'operator_profile.md'), write_every=1
            ).ingest(metrics)
        except Exception:
            pass

    # â”€â”€ Rework detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    rework_verdict = 'ok'
    try:
        rework_mod = _load_pigeon_module(root, 'src/rework_detector_seq009*.py')
        if rework_mod:
            rw = rework_mod.score_rework(post_evts)
            rework_verdict = rw['verdict']
            if post_evts:
                rework_mod.record_rework(root, rw, query_txt)
    except Exception:
        pass

    # ── Unsaid analysis (composition-enriched) ─────────────────────────
    unsaid = None
    try:
        unsaid_mod = _load_pigeon_module(root, 'src/cognitive/unsaid_seq002*.py')
        if unsaid_mod:
            # Build enriched events from chat composition (highest fidelity)
            enriched_events = events[:]
            if chat_comp and chat_comp.get('composition_events'):
                for ce in chat_comp['composition_events']:
                    enriched_events.append({
                        'ts': ce.get('ts', 0),
                        'type': 'backspace' if ce.get('action') == 'delete' else 'insert',
                        'context': 'chat',
                        'buffer': ce.get('buffer', ''),
                    })
            elif chat_keys:
                # Fallback to raw OS hook events
                for i, ck in enumerate(chat_keys):
                    if ck.get('type') == 'backspace' and ck.get('buffer'):
                        enriched_events.append({
                            'ts': ck['ts'], 'type': 'backspace',
                            'context': 'chat', 'buffer': ck['buffer'],
                        })
                    elif ck.get('type') == 'discard' and i > 0:
                        prev_buf = chat_keys[i-1].get('buffer', '')
                        if prev_buf:
                            enriched_events.append({
                                'ts': ck['ts'], 'type': 'clear',
                                'context': 'chat', 'buffer': prev_buf,
                                'discarded_text': prev_buf,
                            })
            unsaid = unsaid_mod.extract_unsaid_thoughts(enriched_events, query_txt)
            # Inject composition deleted words as extra fragments
            if chat_comp:
                for dw in chat_comp.get('deleted_words', []):
                    if len(dw.get('word', '')) >= 3:
                        unsaid['deleted_fragments'].append({
                            'text': dw['word'],
                            'position': 'chat_composition',
                            'length': len(dw['word']),
                            'deleted_at_ms': dw.get('start_ts', 0),
                        })
    except Exception:
        pass

    # â”€â”€ Query memory + unsaid integration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        qmem_mod = _load_pigeon_module(root, 'src/query_memory_seq010*.py')
        if qmem_mod:
            qmem_mod.record_query(root, query_txt, submitted, unsaid)
    except Exception:
        pass

    # â”€â”€ File heat map update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        heat_mod = _load_pigeon_module(root, 'src/file_heat_map_seq011*.py')
        if heat_mod:
            heat_mod.update_heat_map(root, state, metrics['hesitation_score'],
                                     rework_verdict, wpm)
    except Exception:
        pass

    # ── Cognitive reactor: autonomous code modification from telemetry ────
    reactor_result = None
    try:
        reactor_mod = _load_pigeon_module(root, 'src/cognitive_reactor_seq014*.py')
        if reactor_mod:
            # Active files = what the operator is currently touching
            active_files = []
            if query_txt.startswith('bg:'):
                active_files = [query_txt[3:]]  # filename from background flush
            reactor_result = reactor_mod.ingest_flush(
                root, state, metrics['hesitation_score'], wpm, active_files)
    except Exception:
        pass

    # â”€â”€ LLM rewrite every 8 submitted â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    coaching_updated = False
    coaching_path = root / 'operator_coaching.md'
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if submitted and api_key:
        history = _parse_history(root)
        if _should_rewrite(history, coaching_path):
            try:
                rework_mod = _load_pigeon_module(root, 'src/rework_detector_seq009*.py')
                qmem_mod   = _load_pigeon_module(root, 'src/query_memory_seq010*.py')
                heat_mod   = _load_pigeon_module(root, 'src/file_heat_map_seq011*.py')
                rw_stats  = rework_mod.load_rework_stats(root) if rework_mod else {}
                q_mem     = qmem_mod.load_query_memory(root) if qmem_mod else {}
                heat      = heat_mod.load_heat_map(root) if heat_mod else {}
                prose = _call_deepseek(_build_prompt(history, rw_stats, q_mem, heat, chat_comp), api_key)
                if prose:
                    count = _count_submitted(history)
                    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
                    coaching_path.write_text(
                        f'<!-- coaching:count={count} -->\n'
                        f'<!-- classify_bridge Â· {today} Â· {count} submitted -->\n'
                        f'{prose}\n<!-- /coaching -->\n', encoding='utf-8')
                    coaching_updated = True
            except Exception:
                pass

    # â”€â”€ Refresh copilot-instructions.md â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        from pigeon_compiler.git_plugin import _refresh_operator_state
        _refresh_operator_state(root)
    except Exception:
        pass

    # Build composition summary for output
    comp_summary = None
    if chat_comp:
        comp_summary = {
            'deleted_words': [w.get('word', '') for w in chat_comp.get('deleted_words', [])],
            'rewrites': len(chat_comp.get('rewrites', [])),
            'deletion_ratio': chat_comp.get('deletion_ratio', 0),
            'peak_buffer': chat_comp.get('peak_buffer', '')[:100],
            'hesitation_windows': len(chat_comp.get('hesitation_windows', [])),
        }

    print(json.dumps({
        'state':            state,
        'hesitation':       metrics['hesitation_score'],
        'wpm':              wpm,
        'coaching_updated': coaching_updated,
        'rework_verdict':   rework_verdict,
        'reactor':          reactor_result,
        'composition':      comp_summary,
    }))


if __name__ == '__main__':
    main()
