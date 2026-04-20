"""tc_sim_engine_seq001_v001 — intent simulation on typing pause.

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
# EDIT_WHY:  create sim engine on pause
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
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
from .tc_gemini_seq001_v003_d0420__gemini_api_call_system_prompt_lc_chore_pigeon_rename_cascade import _load_api_key, SYSTEM_PROMPT
from .tc_context_seq001_v001 import load_context, invalidate_context_cache
from .tc_context_agent_seq001_v004_d0420__picks_relevant_source_files_based_lc_chore_pigeon_rename_cascade import select_context_ensemble
from .tc_profile_seq001_v001 import load_profile

SIM_LOG = ROOT / 'logs' / 'tc_sim_results.jsonl'
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
    """Score 0-1: specificity × profile alignment × length utility."""
    if not completion or len(completion) < 10:
        return 0.0
    # specificity: contains module/function names (dots, underscores, parens)
    spec = min(1.0, (completion.count('_') + completion.count('.') + completion.count('(')) / 8)
    # length utility: sweet spot 40-200 chars
    length = len(completion)
    len_score = 1.0 if 40 <= length <= 200 else (length / 40 if length < 40 else max(0.3, 200 / length))
    # profile alignment: contains any of operator's topic keywords
    topics = profile.get('topics', {}).get('top_tokens', [])[:15]
    comp_lower = completion.lower()
    topic_hits = sum(1 for t in topics if t in comp_lower)
    topic_score = min(1.0, topic_hits / max(1, min(3, len(topics))))
    return round(0.4 * spec + 0.3 * len_score + 0.3 * topic_score, 3)


def _select_files_for_sim(buffer: str, ctx: dict, profile_weight: float) -> list[dict]:
    """Get file selection biased by profile_weight (0=task-only, 1=profile-driven)."""
    base_files = select_context_ensemble(buffer, ctx, max_files=5)[:5]
    if profile_weight < 0.4:
        return base_files[:3]
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
    return files[:4]


def _build_sim_prompt(buffer: str, ctx: dict, selected_files: list[dict],
                      sim_name: str, profile: dict) -> str:
    """Build a prompt variant for this sim — injects deleted words for divergent."""
    deleted = ctx.get('deleted_words_recent', [])
    files_block = ''
    if selected_files:
        lines = []
        for f in selected_files:
            snippet = f.get('snippet', '')[:300]
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
        f"BUFFER: {buffer}\n"
        f"SIM MODE: {sim_name}\n"
        f"OPERATOR STATE: {state}"
        f"{profile_block}"
        f"{deleted_block}\n\n"
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


def _call_gemini_sim(user_prompt: str, temperature: float) -> str:
    """Single Gemini call for one sim variant."""
    api_key = _load_api_key()
    if not api_key:
        return ''
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
           f':generateContent?key={api_key}')
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': 256,
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
        return ''


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
        t.join(timeout=GEMINI_TIMEOUT + 2)

    if not results:
        return None

    winner = max(results, key=lambda r: r.score)
    _persist_sim(buffer, results, winner)
    return winner


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
        print(f'[sim] reinjected winner ({winner.name}, score={winner.score:.2f}) → intent compiler')
    except Exception as e:
        print(f'[sim] reinject failed: {e}')
