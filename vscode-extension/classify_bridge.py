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
         "post_response_events": [...], "query_text": str,
         "response_text": str}
Argv:   <repo_root>
Stdout: {"state", "hesitation", "wpm", "coaching_updated", "rework_verdict"}
"""
import sys
import json
import os
import hashlib
import importlib.util
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

LLM_REWRITE_EVERY = 8


def _parse_ts(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).timestamp() * 1000
    except ValueError:
        return 0.0


def _normalize_response_text(text: str, limit: int) -> str:
    if not isinstance(text, str):
        text = str(text or '')
    return text.replace('\r\n', '\n').strip()[:limit]


def _response_fingerprint(prompt: str, response: str) -> str:
    payload = f'{_normalize_response_text(prompt, 500)}\n\x1f{_normalize_response_text(response, 5000)}'
    return hashlib.sha1(payload.encode('utf-8', errors='replace')).hexdigest()[:20]


def _normalize_ai_response_entry(entry: dict) -> dict | None:
    prompt = _normalize_response_text(entry.get('prompt', ''), 500)
    response = _normalize_response_text(entry.get('response', ''), 5000)
    if not response:
        return None
    normalized = dict(entry)
    normalized['ts'] = entry.get('ts') or datetime.now(timezone.utc).isoformat()
    normalized['prompt'] = prompt
    normalized['response'] = response
    normalized['source'] = entry.get('source') or 'unknown'
    normalized['capture_surface'] = entry.get('capture_surface') or 'vscode_chat'
    normalized['schema_version'] = entry.get('schema_version', 2)
    session_id = str(entry.get('session_id') or '')
    normalized['session_id'] = session_id
    request_idx = entry.get('request_idx', -1)
    try:
        request_idx = int(request_idx)
    except (TypeError, ValueError):
        request_idx = -1
    normalized['request_idx'] = request_idx
    fingerprint = entry.get('response_fingerprint') or _response_fingerprint(prompt, response)
    normalized['response_fingerprint'] = fingerprint
    response_id = entry.get('response_id')
    if not response_id:
        if session_id and request_idx >= 0:
            response_id = f'chat:{session_id}:{request_idx}'
        else:
            response_id = f"{normalized['source']}:{fingerprint}"
    normalized['response_id'] = response_id
    return normalized


def _response_entry_score(entry: dict) -> tuple:
    source_rank = {
        'pigeon_panel_copilot': 4,
        'pigeon_panel_deepseek': 3,
        'classify_bridge': 2,
        'chat_session_auto': 1,
    }.get(entry.get('source', ''), 0)
    return (
        1 if entry.get('rework_verdict') else 0,
        1 if entry.get('prompt') else 0,
        1 if entry.get('request_idx', -1) != -1 else 0,
        source_rank,
        _parse_ts(entry.get('ts', 0)),
    )


def _dedupe_ai_responses(entries: list[dict], limit: int) -> list[dict]:
    best_by_key = {}
    for entry in entries:
        normalized = _normalize_ai_response_entry(entry)
        if not normalized:
            continue
        key = normalized.get('response_fingerprint') or normalized.get('response_id')
        previous = best_by_key.get(key)
        if previous is None or _response_entry_score(normalized) > _response_entry_score(previous):
            best_by_key[key] = normalized
    ordered = sorted(best_by_key.values(), key=lambda item: _parse_ts(item.get('ts', 0)))
    return ordered[-limit:]


def _read_ai_response_entries(root: Path, limit: int) -> list[dict]:
    resp_log = root / 'logs' / 'ai_responses.jsonl'
    if not resp_log.exists():
        return []
    try:
        lines = resp_log.read_text(encoding='utf-8').strip().splitlines()
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except Exception:
        return []


def _append_ai_response(root: Path, entry: dict) -> None:
    normalized = _normalize_ai_response_entry(entry)
    if not normalized:
        return
    for existing in _dedupe_ai_responses(_read_ai_response_entries(root, limit=40), limit=40):
        if (
            existing.get('response_id') == normalized.get('response_id')
            or existing.get('response_fingerprint') == normalized.get('response_fingerprint')
        ):
            return
    resp_log = root / 'logs' / 'ai_responses.jsonl'
    resp_log.parent.mkdir(parents=True, exist_ok=True)
    with open(resp_log, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(normalized) + '\n')


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
    insert_chars = sum(max(int(e.get('len', 1)), 1) for e in inserts)
    delete_chars = sum(max(int(e.get('len', 1)), 1) for e in deletes)
    total_chars = max(insert_chars + delete_chars, 1)
    pause_ms = [e.get('duration_ms', 0) for e in pauses]
    ts_vals  = [e['ts'] for e in events if 'ts' in e]
    start_ms = min(ts_vals) if ts_vals else 0.0
    end_ms   = max(ts_vals) if ts_vals else 1.0
    dur_ms   = max((end_ms - start_ms) + sum(pause_ms), sum(pause_ms), 1.0)
    del_ratio   = delete_chars / total_chars
    pause_ratio = sum(pause_ms) / dur_ms
    hes  = min(1.0, round(del_ratio * 0.6 + pause_ratio * 0.4, 3))
    wpm  = round((insert_chars / 5) / max(dur_ms / 60_000, 0.001), 1)
    return {
        'total_keystrokes': total_chars,
        'total_inserts':    insert_chars,
        'total_deletions':  delete_chars,
        'typing_pauses':    [{'duration_ms': d} for d in pause_ms],
        'start_time_ms':    int(start_ms),
        'end_time_ms':      int(start_ms + dur_ms),
        'effective_duration_ms': int(dur_ms),
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
                  composition: dict | None = None,
                  recent_responses: list | None = None) -> str:
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

    # Build recent AI responses block for coaching
    resp_block = '  no response data yet'
    if recent_responses:
        resp_lines = []
        for r in recent_responses[-5:]:
            verdict = r.get('rework_verdict', '?')
            prompt_hint = r.get('prompt', '')[:60]
            resp_hint = r.get('response', '')[:80]
            resp_lines.append(f'  [{verdict}] "{prompt_hint}" -> "{resp_hint}..."')
        resp_block = '\n'.join(resp_lines)

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

RECENT AI RESPONSES (prompt→response pairs with rework verdict):
{resp_block}

Write behavioral coaching for Copilot. Requirements:
1. One sentence: operator's dominant pattern + what their rework rate reveals
2. 4\u20136 bullets: precise behavioral instructions for next session
3. Call out persistent gaps by name \u2014 the AI must fix these proactively
4. For each high-miss file: prescribe a different response strategy
5. For abandoned themes: the AI should proactively surface these
6. For deleted words: these reveal what the operator WANTED to say but chose not to \u2014 address the underlying need
7. For responses marked 'miss': identify what went wrong and prescribe how to answer differently next time
8. One sentence: what this operator is building toward

Surgical and specific. Every word changes AI behavior. Max 250 words. Markdown bullets only."""


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


def _load_recent_responses(root: Path, limit: int = 10) -> list:
    """Load recent AI responses — auto-syncs from VS Code chat session first."""
    # Auto-sync: read responses directly from VS Code chatSessions storage
    try:
        reader_path = root / 'client' / 'chat_response_reader.py'
        if reader_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location('chat_response_reader', str(reader_path))
            reader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(reader)
            reader.sync_to_log(str(root), limit=limit)
    except Exception:
        pass

    resp_log = root / 'logs' / 'ai_responses.jsonl'
    if not resp_log.exists():
        return []
    try:
        raw_entries = _read_ai_response_entries(root, limit=max(limit * 8, 40))
        return _dedupe_ai_responses(raw_entries, limit=limit)
    except Exception:
        return []


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
                if evt.get('source') == 'vscode':
                    continue
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
        if analyzer_path.exists():
            spec = importlib.util.spec_from_file_location('_comp_analyzer', analyzer_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.analyze_and_log(root)
            if result:
                return result
    except Exception:
        pass
    # Fallback: read latest entry from chat_compositions.jsonl (already logged)
    try:
        comp_path = root / 'logs' / 'chat_compositions.jsonl'
        if comp_path.exists():
            lines = comp_path.read_text('utf-8').strip().splitlines()
            if lines:
                return json.loads(lines[-1])
    except Exception:
        pass
    return None


def main():
    root      = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    payload   = json.loads(sys.stdin.read())
    events    = payload.get('events', [])
    submitted = payload.get('submitted', True)
    post_evts = payload.get('post_response_events', [])
    query_txt = payload.get('query_text', '')
    resp_text = payload.get('response_text', '')

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
    # Fallback: if chat_comp failed, try composition_recon (fuses OS hook + vscdb + journal)
    if not chat_comp:
        try:
            recon_path = root / 'client' / 'composition_recon.py'
            if recon_path.exists():
                spec = importlib.util.spec_from_file_location('_comp_recon', recon_path)
                recon_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(recon_mod)
                recon_results = recon_mod.reconstruct_composition(str(root))
                # Convert the best result to chat_comp format
                sessions = [r for r in recon_results if r.get('type') == 'os_hook_session']
                if sessions:
                    best = sessions[-1]  # most recent
                    chat_comp = {
                        'total_keystrokes': best.get('total_keystrokes', 0),
                        'deletion_ratio': best.get('deletion_ratio', 0),
                        'deleted_words': [],
                        'rewrites': [],
                        'peak_buffer': best.get('final_buffer', ''),
                        'source': 'composition_recon',
                    }
                    # Merge abandoned drafts as pseudo-deleted-words
                    for r in recon_results:
                        if r.get('type') == 'abandoned_drafts':
                            for d in r.get('drafts', [])[:5]:
                                txt = d.get('abandoned_text', '')
                                if txt:
                                    chat_comp['deleted_words'].append({'word': txt[:60], 'start_ts': 0})
                        if r.get('type') == 'rewrite_sequences':
                            chat_comp['rewrites'] = r.get('rewrites', [])[:5]
        except Exception:
            pass
    chat_state_override = None
    if chat_comp:
        cs = chat_comp.get('chat_state', {})
        if cs.get('confidence', 0) > 0.6:
            chat_state_override = cs

    # â"€â"€ Classify state â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€
    stats_mod = _load_pigeon_module(root, 'src/控w_ops_s008*.py')
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
            # Intent-only deletion ratio (8+ backspace runs) — excludes typo noise
            metrics['intent_deletion_ratio'] = chat_comp.get('intent_deletion_ratio', 0)
            metrics['chat_intent_deleted_words'] = [
                w['word'] for w in chat_comp.get('intent_deleted_words', [])]
        # Only ingest real chat submits — bg: flushes are editor keystroke batches
        # that pollute the cognitive profile (inflated denominator, wrong del ratio)
        if not query_txt.startswith('bg:'):
            try:
                stats_mod.OperatorStats(
                    str(root / 'operator_profile.md'), write_every=1
                ).ingest(metrics)
            except Exception:
                pass

    # ── Rework detection ─────────────────────────────────────────────
    rework_verdict = 'ok'
    try:
        rework_mod = _load_pigeon_module(root, 'src/测p_rwd_s009*.py')
        if rework_mod:
            rw = None
            if chat_comp and chat_comp.get('total_keystrokes', 0) > 5:
                rw_fn = getattr(rework_mod, 'score_rework_from_composition', None)
                if rw_fn:
                    rw = rw_fn(chat_comp)
                else:
                    rw = rework_mod.score_rework(post_evts)
            elif post_evts:
                rw = rework_mod.score_rework(post_evts)
            else:
                # Fallback: score from prompt_telemetry signal data
                try:
                    pt_path = root / 'logs' / 'prompt_telemetry_latest.json'
                    if pt_path.exists():
                        pt = json.loads(pt_path.read_text('utf-8'))
                        sig = pt.get('signals', {})
                        dr = sig.get('deletion_ratio', 0)
                        kc = sig.get('total_keystrokes', 0)
                        dur = sig.get('duration_ms', 1)
                        rw_count = len(pt.get('rewrites', []))
                        if kc > 5 or dr > 0:
                            rw_fn = getattr(rework_mod, 'score_rework_from_composition', None)
                            if rw_fn:
                                rw = rw_fn({
                                    'deletion_ratio': dr,
                                    'total_keystrokes': max(kc, 1),
                                    'duration_ms': max(dur, 1),
                                    'rewrites': pt.get('rewrites', []),
                                    'deleted_words': pt.get('deleted_words', []),
                                })
                except Exception:
                    pass
            if rw:
                rework_verdict = rw['verdict']
                rework_mod.record_rework(root, rw, query_txt, resp_text)
    except Exception:
        pass

    # ── Unsaid analysis (composition-enriched) ─────────────────────────
    unsaid = None
    try:
        unsaid_mod = _load_pigeon_module(root, 'src/cognitive/隐p_un_s002*.py')
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

    # ── Unsaid reconstruction via Gemini (intent deletions OR moderate uncertainty) ──
    try:
        recon_comp = chat_comp
        if not recon_comp:
            # Build minimal composition from prompt_telemetry
            pt_path = root / 'logs' / 'prompt_telemetry_latest.json'
            if pt_path.exists():
                pt = json.loads(pt_path.read_text('utf-8'))
                sig = pt.get('signals', {})
                recon_comp = {
                    'deletion_ratio': sig.get('deletion_ratio', 0),
                    'deleted_words': pt.get('deleted_words', []),
                    'rewrites': pt.get('rewrites', []),
                    'final_text': query_txt,
                }
        # Let reconstruct_if_needed decide: intent_deleted_words OR deletion_ratio >= 15%
        if recon_comp:
            has_intent = bool(recon_comp.get('intent_deleted_words'))
            has_deletions = bool(recon_comp.get('deleted_words'))
            dr = recon_comp.get('deletion_ratio', 0)
            if has_intent or (dr >= 0.15 and has_deletions):
                unsaid_recon_mod = _load_pigeon_module(root, 'src/探p_ur_s024*.py')
                if unsaid_recon_mod:
                    unsaid_recon_mod.reconstruct_if_needed(root, recon_comp)
    except Exception:
        pass

    # â”€â”€ Query memory + unsaid integration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        qmem_mod = _load_pigeon_module(root, 'src/忆p_qm_s010*.py')
        if qmem_mod:
            qmem_mod.record_query(root, query_txt, submitted, unsaid)
    except Exception:
        pass

    # â”€â”€ File heat map update â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    try:
        heat_mod = _load_pigeon_module(root, 'src/热p_fhm_s011*.py')
        if heat_mod:
            heat_mod.update_heat_map(root, state, metrics['hesitation_score'],
                                     rework_verdict, wpm)
    except Exception:
        pass

    # ── Cognitive reactor: autonomous code modification from telemetry ────
    reactor_result = None
    try:
        reactor_mod = _load_pigeon_module(root, 'src/思f_cr_s014*.py')
        if reactor_mod:
            # Gather active files from all available sources
            active_files = []
            # Source 1: background flush label (bg:filename.py)
            if query_txt.startswith('bg:'):
                bg_file = query_txt[3:]
                if bg_file and bg_file != 'idle':
                    active_files.append(bg_file)
            # Source 2: prompt telemetry files_open (most reliable)
            try:
                pt_path = root / 'logs' / 'prompt_telemetry_latest.json'
                if pt_path.exists():
                    pt = json.loads(pt_path.read_text('utf-8'))
                    for f in pt.get('latest_prompt', {}).get('files_open', []):
                        if f and f not in active_files:
                            active_files.append(f)
            except Exception:
                pass
            # Source 3: file heat map — recently active modules
            try:
                hm_path = root / 'file_heat_map.json'
                if hm_path.exists():
                    hm = json.loads(hm_path.read_text('utf-8'))
                    for entry in hm.get('files', [])[:3]:
                        fname = entry.get('file', '')
                        if fname and fname not in active_files:
                            active_files.append(fname)
            except Exception:
                pass
            reactor_result = reactor_mod.ingest_flush(
                root, state, metrics['hesitation_score'], wpm, active_files)
    except Exception:
        pass

    # ── Log AI response if present ───────────────────────────────────────────
    if resp_text and query_txt and not query_txt.startswith('bg:'):
        resp_log = root / 'logs' / 'ai_responses.jsonl'
        try:
            _append_ai_response(root, {
                'ts': datetime.now(timezone.utc).isoformat(),
                'prompt': query_txt[:500],
                'response': resp_text[:5000],
                'source': 'classify_bridge',
                'capture_surface': 'vscode_chat',
                'schema_version': 2,
                'rework_verdict': rework_verdict,
            })
        except Exception:
            pass

    # -- Auto-sync Copilot responses from VS Code chat session ---------------
    try:
        _reader_path = root / 'client' / 'chat_response_reader.py'
        if _reader_path.exists():
            import importlib.util
            _spec = importlib.util.spec_from_file_location('chat_response_reader', str(_reader_path))
            _reader_mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_reader_mod)
            _reader_mod.sync_to_log(str(root), limit=5)
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
                rework_mod = _load_pigeon_module(root, 'src/测p_rwd_s009*.py')
                qmem_mod   = _load_pigeon_module(root, 'src/忆p_qm_s010*.py')
                heat_mod   = _load_pigeon_module(root, 'src/热p_fhm_s011*.py')
                rw_stats  = rework_mod.load_rework_stats(root) if rework_mod else {}
                q_mem     = qmem_mod.load_query_memory(root) if qmem_mod else {}
                heat      = heat_mod.load_heat_map(root) if heat_mod else {}
                recent_responses = _load_recent_responses(root)
                prose = _call_deepseek(_build_prompt(history, rw_stats, q_mem, heat, chat_comp, recent_responses), api_key)
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
    # Refresh task context (Prompt ms, unsaid, hot modules) on every flush
    try:
        dyn_mod = _load_pigeon_module(root, 'src/推w_dp_s017*.py')
        if dyn_mod and hasattr(dyn_mod, 'inject_task_context'):
            dyn_mod.inject_task_context(root)
    except Exception:
        pass

    # ── Enrich prompt via Gemini Flash (rewrite current-query block) ──────────
    if submitted and query_txt and not query_txt.startswith('bg:'):
        try:
            enricher_mod = _load_pigeon_module(root, 'src/探p_ur_s024*.py')
            if enricher_mod:
                enrich_dw = []
                enrich_cog = {}
                if chat_comp:
                    enrich_dw = chat_comp.get('intent_deleted_words') or chat_comp.get('deleted_words', [])
                    enrich_cog = {
                        'state': state,
                        'wpm': wpm,
                        'del_ratio': chat_comp.get('intent_deletion_ratio', metrics.get('deletion_ratio', 0)),
                        'hes': metrics.get('hesitation_score', 0),
                    }
                enricher_mod.inject_query_block(
                    root, query_txt,
                    deleted_words=enrich_dw,
                    cognitive_state=enrich_cog,
                )
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

    # ── Training pair writer: muxed state per prompt ─────────────────────────
    if submitted and query_txt and not query_txt.startswith('bg:'):
        try:
            tw_mod = _load_pigeon_module(root, 'src/训w_trwr_s028*.py')
            if tw_mod:
                tw_mod.write_training_pair(
                    root,
                    prompt=query_txt[:500],
                    response=resp_text[:1000] if resp_text else '(no response captured)',
                    verdict=rework_verdict,
                )
        except Exception:
            pass

    # ── Shard learning: feed rework verdicts into memory shards ──────────────
    if submitted and query_txt and not query_txt.startswith('bg:'):
        try:
            sm_mod = _load_pigeon_module(root, 'src/片w_sm_s026*.py')
            if sm_mod and hasattr(sm_mod, 'learn_from_rework'):
                rw_score = rw['rework_score'] if rw else 0.0
                sm_mod.learn_from_rework(
                    root, query_txt[:300], rework_verdict,
                    rw_score,
                    response_hint=resp_text[:200] if resp_text else '',
                )
        except Exception:
            pass

    # ── Mutation scorer: correlate prompt mutations with rework on every submit ─
    mutation_scores = None
    if submitted and query_txt and not query_txt.startswith('bg:'):
        try:
            ms_mod = _load_pigeon_module(root, 'src/变p_ms_s021*.py')
            if ms_mod:
                mutation_scores = ms_mod.score_mutations(root)
        except Exception:
            pass

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
