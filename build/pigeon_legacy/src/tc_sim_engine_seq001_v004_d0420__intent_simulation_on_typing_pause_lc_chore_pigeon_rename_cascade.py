"""tc_sim_engine_seq001_v004 — intent simulation on typing pause.

On pause (operator stops typing), runs 3 parallel intent sims:
  each sim = different code combo (files) from current task + operator profile
  → produces 3 expanded prompt candidates
  → scores them, picks winner, reinjects into intent compressor log

Pipeline:
  buffer pause → expand_tasks(buffer) → 3 code combos from operator profile
  → call_gemini × 3 with different file selections → score → reinject winner

Reinject output path: logs/tc_sim_results.jsonl  (intent compressor reads this)
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v004 | 273 lines | ~2,627 tokens
# DESC:   intent_simulation_on_typing_pause
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-20T00:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  add intent numeric encoding scoring to sim engine
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──
from __future__ import annotations

import json
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from .tc_constants_seq001_v001 import ROOT, GEMINI_MODEL, GEMINI_TIMEOUT
from .tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import _load_api_key
from .tc_context_seq001_v001 import load_context, invalidate_context_cache
from .tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade import select_context_ensemble
from .tc_profile_seq001_v001 import load_profile

SIM_LOG = ROOT / 'logs' / 'tc_sim_results.jsonl'
SIM_MAILBOX = ROOT / 'logs' / 'sim_mailbox.jsonl'
SIM_LOG.parent.mkdir(parents=True, exist_ok=True)

# ── Sim temperature variants  ─────────────────────────────────────────────────
# Sim 0: grounded  — low temp, task-focused files
# Sim 1: adjacent  — medium temp, profile-biased files
# Sim 2: divergent — high temp, operator's historically-deleted themes
_SIM_CONFIGS = [
    {'name': 'grounded',  'temp': 0.3, 'profile_weight': 0.2},
    {'name': 'adjacent',  'temp': 0.6, 'profile_weight': 0.6},
    {'name': 'divergent', 'temp': 0.9, 'profile_weight': 1.0},
]


class SimResult(NamedTuple):
    name: str
    completion: str
    files: list[str]
    score: float
    temp: float


def _score_completion(completion: str, buffer: str, profile: dict) -> float:
    """Score the sim action path on specificity, interlink signal, and topic alignment."""
    if not completion or len(completion) < 8:
        return 0.0
    ext = completion.strip()
    # specificity: module names, function calls, file paths
    spec = min(1.0, (ext.count('_') + ext.count('.') + ext.count('(') + ext.count('/')) / 6)
    # length utility: action paths sweet spot 40-400 chars
    length = len(ext)
    len_score = 1.0 if 40 <= length <= 400 else (length / 40 if length < 40 else max(0.2, 400 / length))
    # interlink signal: mentions escalation / interlink / patch / fix / compliance / sleep
    interlink_terms = {'interlink', 'escalat', 'patch', 'overwrite', 'compliance',
                       'pigeon', 'fix', 'sleep', 'cortex', 'self_fix', 'vein', 'clot',
                       'rework', 'intent', 'numeric', 'encoding', 'orange'}
    ext_lower = ext.lower()
    interlink_hits = sum(1 for t in interlink_terms if t in ext_lower)
    interlink_score = min(1.0, interlink_hits / 3)
    # intent numeric encoding signal: check if completion mentions intent keys mapping
    intent_encoding_terms = {'intent keys', 'intent key', 'numeric encoding', 'neumeric encoding',
                             'key match', 'map architecture', 'prompt map', 'whole architecture',
                             'fire every prompt', 'supposed to fire'}
    intent_hits = sum(1 for t in intent_encoding_terms if t in ext_lower)
    intent_score = min(1.0, intent_hits / 2)
    # profile alignment
    topics = profile.get('topics', {}).get('top_tokens', [])[:15]
    topic_hits = sum(1 for t in topics if t in ext_lower)
    topic_score = min(1.0, topic_hits / max(1, min(3, len(topics))))
    return round(0.30 * spec + 0.2 * len_score + 0.25 * interlink_score + 0.15 * intent_score + 0.1 * topic_score, 3)


_SIM_SYSTEM_PROMPT = """\
You are a CODEBASE INTERLINK PREDICTOR. You analyse operator intent + active files and output
the CONCRETE ACTION PATH that gets those files interlinked, patched, or promoted to pigeon compliance.

Given: BUFFER (operator intent), SIM MODE, list of activated files with snippets.
You also receive FILE INTELLIGENCE GRAPH context: typed evidence edges between
files, prompts, tests, sims, edit pairs, and validation outcomes.

Your output must be a tight 1-3 sentence action plan:
  - Which specific files need to change and WHY (name the function/section)
  - What graph evidence connects them (imports / tested_by / co_touched_with / sim_requested / prompt_woke)
  - What interlink path connects them (escalation_sweep / self_fix / overwrite / interlink_debugger)
  - What pigeon compliance gap exists (over_hard_cap / orphan / stale_pulse / unused_exports)
  - Whether a file should SLEEP (mark EDIT_STATE: idle) after the patch

RULES:
- Do NOT echo or paraphrase the buffer. Start AFTER the intent.
- Use exact module stems: tc_gemini, file_sim, file_overwriter, intent_numeric, etc.
- Prefer graph-evidenced file sequences over single-file guesses.
- Be concrete: name the fix, the function, the log file.
- grounded = most likely direct path. adjacent = lateral dependency chain. divergent = unexpected coupling.
- Max 3 sentences. No markdown. No bullet lists. Just the action path.
- If nothing needs changing, output: NO_ACTION
"""


def _load_rework_history(root: Path | None = None, max_per_file: int = 4) -> dict[str, list[str]]:
    """Build per-file rework memory from edit_pairs.jsonl.
    Returns {file_stem: ["prompt | edit_why", ...]} for the N most recent reworks.
    """
    _root = root or ROOT
    pairs_path = _root / 'logs' / 'edit_pairs.jsonl'
    if not pairs_path.exists():
        return {}
    hist: dict[str, list[str]] = {}
    try:
        lines = [l for l in pairs_path.read_text('utf-8', errors='ignore').splitlines() if l.strip()]
        for line in lines:
            try:
                r = json.loads(line)
                f = r.get('file', '')
                if not f:
                    continue
                stem = Path(f).stem.split('_seq')[0]
                msg = (r.get('prompt_msg') or '')[:80].strip()
                why = (r.get('edit_why') or '')[:80].strip()
                if stem and (msg or why):
                    hist.setdefault(stem, []).append(
                        f"{msg} → {why}" if msg and why else (msg or why)
                    )
            except Exception:
                continue
    except Exception:
        return {}
    # keep only last N per file
    return {s: v[-max_per_file:] for s, v in hist.items()}


_rework_history_cache: dict[str, list[str]] = {}
_rework_cache_ts: float = 0.0


def _get_rework_history() -> dict[str, list[str]]:
    """Cached rework history — refreshes every 60s."""
    global _rework_history_cache, _rework_cache_ts
    now = time.time()
    if now - _rework_cache_ts > 60:
        _rework_history_cache = _load_rework_history()
        _rework_cache_ts = now
    return _rework_history_cache


def _select_files_for_sim(buffer: str, ctx: dict, profile_weight: float) -> list[dict]:
    """Get file selection biased by profile_weight (0=task-only, 1=profile-driven)."""
    base_files = select_context_ensemble(buffer, ctx, max_files=5)[:5]
    if not base_files:
        base_files = _fallback_context_files(buffer)
    if profile_weight < 0.4:
        return _expand_files_with_graph(buffer, base_files[:3], limit=5)
    # Blend in profile topic files — look up files by topic keywords
    profile = load_profile()
    topic_tokens = profile.get('topics', {}).get('top_tokens', [])[:5]
    files = list(base_files)
    if topic_tokens and profile_weight >= 0.6:
        try:
            from .intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import predict_files
            topic_query = ' '.join(topic_tokens[:3])
            extra = predict_files(topic_query, top_n=3)
            seen = {f['name'] for f in files}
            for e in extra:
                if e['name'] not in seen:
                    files.append(e)
                    seen.add(e['name'])
        except Exception:
            pass
    return _expand_files_with_graph(buffer, files[:4], limit=6)


def _expand_files_with_graph(buffer: str, files: list[dict], limit: int = 6) -> list[dict]:
    """Let file graph neighbors join the sim context."""
    try:
        from .file_intelligence_graph_seq001_v001 import expand_files_with_graph
        expanded = expand_files_with_graph(ROOT, files, prompt=buffer, limit=limit, write=True)
        if expanded:
            return expanded[:limit]
    except Exception as exc:
        print(f'[file-graph] expansion failed: {exc}')
    return files[:limit]


def _train_sim_numeric_surface(buffer: str, files: list[dict]) -> None:
    """Treat sim file selection as a prompt-to-file learning event."""
    names = [str(f.get('name') or '') for f in files if f.get('name')]
    if not names or len(buffer.strip()) < 4:
        return
    try:
        from .intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import record_touch
        record_touch(buffer, names, learning_rate=0.035)
    except Exception as exc:
        print(f'[sim-numeric] train failed: {exc}')


def _fallback_context_files(buffer: str) -> list[dict]:
    """Context fallback for popup sims when the legacy context agent returns no files."""
    lower = buffer.lower()
    rows: list[dict] = []
    hints = [
        (("thought completer", "popup", "pause", "completion", "gemini"), "thought_completer", 0.72),
        (("popup", "pause", "completion"), "tc_popup", 0.68),
        (("gemini", "gemining"), "tc_gemini", 0.66),
        (("buffer", "cut", "cuts off", "typing"), "tc_buffer_watcher", 0.64),
        (("intent", "file", "memory", "key"), "tc_intent_keys", 0.6),
        (("prompt brain", "context"), "tc_prompt_brain", 0.58),
    ]
    for needles, name, score in hints:
        if any(needle in lower for needle in needles):
            rows.append({"name": name, "score": score, "sources": ["sim_fallback"]})
    if rows:
        return rows
    return [{"name": "thought_completer", "score": 0.35, "sources": ["sim_fallback_default"]}]


def _build_sim_prompt(buffer: str, ctx: dict, selected_files: list[dict],
                      sim_name: str, profile: dict) -> str:
    """Build a prompt variant — injects rework history + numeric top files per sim mode."""
    deleted = ctx.get('deleted_words_recent', [])

    # ── Numeric top files for this intent ──────────────────────────────────
    numeric_block = ''
    try:
        from .intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import predict_files
        preds = predict_files(buffer, top_n=6)
        if preds:
            numeric_block = '\nNUMERIC TOP FILES (learned from past touches):\n'
            numeric_block += '\n'.join(
                f"  {p['name']}  score={p.get('score', 0):.3f}"
                for p in preds
            )
    except Exception:
        pass

    # ── Rework history for selected files ──────────────────────────────────
    rework_hist = _get_rework_history()
    rework_block = ''
    rework_lines = []
    for f in selected_files[:5]:
        stem = f.get('name', '').split('_seq')[0]
        hist = rework_hist.get(stem, [])
        if hist:
            for entry in hist[-2:]:
                rework_lines.append(f"  {stem}: {entry}")
    if rework_lines:
        rework_block = '\nPAST REWORK HISTORY (prompt → edit_why for these files):\n' + '\n'.join(rework_lines)

    graph_block = ''
    try:
        from .file_intelligence_graph_seq001_v001 import render_graph_context_for_files
        graph_block = '\n' + render_graph_context_for_files(
            ROOT,
            selected_files,
            prompt=buffer,
            deleted_words=deleted,
            max_packets=6,
        )
    except Exception as exc:
        graph_block = f'\nFILE INTELLIGENCE GRAPH: unavailable ({exc})'

    # ── File snippets ───────────────────────────────────────────────────────
    files_block = ''
    if selected_files:
        lines = []
        for f in selected_files:
            snippet = f.get('snippet', '')[:200]
            lines.append(f"FILE: {f['name']}\n{snippet}")
        files_block = '\n\n'.join(lines)

    deleted_block = ''
    if sim_name == 'divergent' and deleted:
        real_words = [w for w in deleted if len(w) >= 4 and not _is_stutter(w)][:5]
        if real_words:
            deleted_block = f"\nSUPPRESSED THOUGHTS: {', '.join(real_words)}"

    profile_block = ''
    topics = profile.get('topics', {}).get('top_tokens', [])[:8]
    if topics:
        profile_block = f"\nOPERATOR FOCUS TOKENS: {', '.join(topics)}"

    state = ctx.get('cognitive_state', 'unknown')
    return (
        f"INTENT: {buffer}\n"
        f"SIM MODE: {sim_name}\n"
        f"OPERATOR STATE: {state}"
        f"{profile_block}"
        f"{deleted_block}"
        f"{numeric_block}"
        f"{rework_block}\n\n"
        f"{graph_block}\n\n"
        f"CONTEXT FILES:\n{files_block}"
    )


def _is_stutter(word: str) -> bool:
    """True if word looks like keyboard stutter (aaa, ttt, acactut...) not real intent."""
    if len(word) <= 3:
        return True
    # all same char
    if len(set(word.lower())) <= 2:
        return True
    # alternating pair pattern: abab or ababab
    if len(word) >= 6:
        chars = word.lower()
        unit = chars[:2]
        if chars == unit * (len(chars) // 2):
            return True
    return False


# ── Sim message bus ────────────────────────────────────────────────────────────
# When a sim winner fires, its action path is mailed to the files it names.
# When a file builds its next sim prompt, it reads its inbox — chains of sims
# learn off each other without any central coordinator.

_STEM_NOISE = {
    'this', 'that', 'with', 'from', 'into', 'after', 'before', 'when',
    'should', 'also', 'will', 'then', 'patch', 'file', 'code', 'path',
    'func', 'call', 'text', 'data', 'list', 'dict', 'bool', 'true', 'false',
    'none', 'self', 'note', 'next', 'last', 'each', 'both', 'have', 'been',
}


def _extract_stems_from_text(text: str) -> list[str]:
    """Extract plausible module stems (contain underscore, 6+ chars) from action path text."""
    import re as _re
    tokens = _re.findall(r'\b([a-z][a-z_]{5,})\b', text.lower())
    seen: set[str] = set()
    stems: list[str] = []
    for t in tokens:
        if '_' in t and t not in seen and t not in _STEM_NOISE:
            stems.append(t)
            seen.add(t)
    return stems[:8]


def _send_sim_mail(from_stems: list[str], to_stems: list[str],
                   sim_name: str, action_path: str, intent: str,
                   score: float, root: Path) -> int:
    """Deliver sim winner's action path as mail to recipient files.

    Each recipient gets one message: what the sender's sim said, what score it got,
    and what the original intent was. The recipient reads this on its next sim run
    and factors it into its own prompt (cross-file sim chaining).

    Returns number of messages written.
    """
    if not to_stems or not action_path:
        return 0
    ts = datetime.now(timezone.utc).isoformat()
    mailbox = root / 'logs' / 'sim_mailbox.jsonl'
    mailbox.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    try:
        with open(mailbox, 'a', encoding='utf-8') as f:
            for to in to_stems:
                msg = {
                    'ts': ts,
                    'from': from_stems,
                    'to': to,
                    'sim_name': sim_name,
                    'score': round(score, 3),
                    'action_path': action_path[:300],
                    'intent': intent[:120],
                    'read': False,
                }
                f.write(json.dumps(msg, ensure_ascii=False) + '\n')
                written += 1
    except Exception as e:
        print(f'[sim-mail] send failed: {e}')
    return written


def _read_sim_inbox(stem: str, root: Path, max_msgs: int = 4,
                    max_age_hours: float = 24.0) -> list[dict]:
    """Read unread sim mail for this stem (messages sent by other files' sims).

    Marks messages as read atomically so they don't repeat on the next sim run.
    Files learn from their inbox: if file_a's sim mentioned file_b needs to update
    something, file_b sees that in its next prompt and can chain off that signal.
    """
    import datetime as _dt
    import os as _os
    mailbox = root / 'logs' / 'sim_mailbox.jsonl'
    if not mailbox.exists():
        return []
    cutoff = _dt.datetime.now(_dt.timezone.utc).timestamp() - max_age_hours * 3600
    all_msgs: list[dict] = []
    try:
        for line in mailbox.read_text('utf-8', errors='ignore').splitlines():
            if not line.strip():
                continue
            try:
                all_msgs.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        return []

    inbox: list[dict] = []
    updated = False
    for msg in all_msgs:
        if msg.get('to') != stem or msg.get('read'):
            continue
        try:
            msg_ts = _dt.datetime.fromisoformat(
                msg['ts'].replace('Z', '+00:00')).timestamp()
            if msg_ts < cutoff:
                continue
        except Exception:
            pass
        inbox.append(msg)
        msg['read'] = True
        updated = True

    # Atomic rewrite to mark as read
    if updated:
        try:
            tmp = mailbox.with_suffix('.jsonl.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                for msg in all_msgs:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            _os.replace(tmp, mailbox)
        except Exception:
            pass

    return inbox[-max_msgs:]


def _call_gemini_sim(user_prompt: str, temperature: float) -> str:
    """Single Gemini call for one sim variant."""
    api_key = _load_api_key()
    if not api_key:
        _write_sim_gemini_status('local_fallback', 'missing_GEMINI_API_KEY')
        return 'GEMINI_API_KEY missing; local sim selected files only, no model reasoning ran.'
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
           f':generateContent?key={api_key}')
    body = json.dumps({
        'system_instruction': {'parts': [{'text': _SIM_SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': 600,
            'topP': 0.95,
            'thinkingConfig': {'thinkingBudget': 0},
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = (data.get('candidates', [{}])[0]
                     .get('content', {}).get('parts', []))
            text = ''
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    text = part['text'].strip()
                    break
            return text or (parts[-1].get('text', '').strip() if parts else '')
    except Exception as e:
        print(f'[sim] gemini error ({temperature=}): {e}')
        _write_sim_gemini_status('error', str(e)[:300])
        return ''


def _write_sim_gemini_status(status: str, reason: str) -> None:
    try:
        path = ROOT / 'logs' / 'tc_gemini_status.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            'ts': datetime.now(timezone.utc).isoformat(),
            'surface': 'tc_sim_engine',
            'status': status,
            'reason': reason,
            'model': GEMINI_MODEL,
            'api_key_present': bool(_load_api_key()),
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def run_sim(buffer: str) -> SimResult | None:
    """Run 3 parallel sims on pause. Returns the winning SimResult."""
    if not buffer or len(buffer.strip()) < 6:
        return None

    ctx = load_context()
    profile = load_profile()
    results: list[SimResult] = []
    lock = threading.Lock()

    def _run_one(cfg: dict) -> None:
        files = _select_files_for_sim(buffer, ctx, cfg['profile_weight'])
        _train_sim_numeric_surface(buffer, files)
        prompt = _build_sim_prompt(buffer, ctx, files, cfg['name'], profile)
        text = _call_gemini_sim(prompt, cfg['temp'])
        score = _score_completion(text, buffer, profile)
        with lock:
            results.append(SimResult(
                name=cfg['name'],
                completion=text,
                files=[f['name'] for f in files],
                score=score,
                temp=cfg['temp'],
            ))
            print(f"[sim:{cfg['name']}] score={score:.2f} len={len(text)} "
                  f"files={[f['name'] for f in files[:2]]}")

    threads = [threading.Thread(target=_run_one, args=(cfg,), daemon=True)
               for cfg in _SIM_CONFIGS]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=GEMINI_TIMEOUT + 25)

    if not results:
        return None

    winner = max(results, key=lambda r: r.score)
    _persist_sim(buffer, results, winner)
    return winner


def run_sim_all(buffer: str) -> tuple[list[SimResult], SimResult | None]:
    """Run all sim variants and return (full_list, winner). For live display."""
    if not buffer or len(buffer.strip()) < 6:
        return [], None

    ctx = load_context()
    profile = load_profile()
    results: list[SimResult] = []
    lock = threading.Lock()

    def _run_one(cfg: dict) -> None:
        files = _select_files_for_sim(buffer, ctx, cfg['profile_weight'])
        _train_sim_numeric_surface(buffer, files)
        prompt = _build_sim_prompt(buffer, ctx, files, cfg['name'], profile)
        text = _call_gemini_sim(prompt, cfg['temp'])
        score = _score_completion(text, buffer, profile)
        with lock:
            results.append(SimResult(
                name=cfg['name'],
                completion=text,
                files=[f['name'] for f in files],
                score=score,
                temp=cfg['temp'],
            ))
            print(f"[sim:{cfg['name']}] score={score:.2f} len={len(text)} "
                  f"files={[f['name'] for f in files[:5]]}")

    threads = [threading.Thread(target=_run_one, args=(cfg,), daemon=True)
               for cfg in _SIM_CONFIGS]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=GEMINI_TIMEOUT + 25)

    if not results:
        return [], None

    winner = max(results, key=lambda r: r.score)
    _persist_sim(buffer, results, winner)
    # Stable ordering: grounded, adjacent, divergent
    order = {'grounded': 0, 'adjacent': 1, 'divergent': 2}
    results.sort(key=lambda r: order.get(r.name, 99))
    return results, winner


def _persist_sim(buffer: str, results: list[SimResult], winner: SimResult) -> None:
    """Write sim results to log + reinject winner into intent compressor context."""
    ts = datetime.now(timezone.utc).isoformat()
    record = {
        'ts': ts,
        'buffer': buffer,
        'winner': winner.name,
        'winner_completion': winner.completion,
        'winner_files': winner.files,
        'winner_score': winner.score,
        'sims': [
            {'name': r.name, 'completion': r.completion,
             'score': r.score, 'files': r.files}
            for r in results
        ],
    }
    with open(SIM_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

    # ── Sim message bus: send winner's action path to files it mentions ──────
    # Files referenced in the action path get mail so their next sim can chain
    # off this signal — cross-file sim learning without a central coordinator.
    if winner.completion and winner.completion.strip() != 'NO_ACTION':
        mentioned = _extract_stems_from_text(winner.completion)
        # Don't mail back to the sender files (strip short overlap)
        sender_short = {f.split('_seq')[0] for f in winner.files}
        recipients = [s for s in mentioned if s not in sender_short]
        if recipients:
            n = _send_sim_mail(
                from_stems=winner.files,
                to_stems=recipients,
                sim_name=winner.name,
                action_path=winner.completion,
                intent=buffer,
                score=winner.score,
                root=ROOT,
            )
            if n:
                print(f'[sim] {n} mail(s) -> {recipients[:3]}')

    # Reinject winner into intent compressor feed
    _reinject_to_intent_compiler(buffer, winner, ts)


def _reinject_to_intent_compiler(buffer: str, winner: SimResult, ts: str) -> None:
    """Write winner expansion into intent compressor's latest_context file."""
    reinject_path = ROOT / 'logs' / 'tc_intent_reinjection.json'
    payload = {
        'ts': ts,
        'buffer': buffer,
        'expanded_prompt': f'{buffer} {winner.completion}'.strip(),
        'sim_name': winner.name,
        'files': winner.files,
        'score': winner.score,
    }
    try:
        reinject_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        # Invalidate context cache so next call_gemini() picks up the reinjection
        invalidate_context_cache()
        print(f'[sim] reinjected winner ({winner.name}, score={winner.score:.2f}) -> intent compiler')
    except Exception as e:
        print(f'[sim] reinject failed: {e}')
