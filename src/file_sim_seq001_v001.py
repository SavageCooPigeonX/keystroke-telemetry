"""file_sim_seq001_v001.py — Micro sim engine: prompt × file → grade → matrix update.

Loop:
  intent_job (prompt_vec + text)
  → all src files run self_score() locally (cosine gate — no API)
  → survivors above threshold go to deepseek for grading
  → self-excluded files logged with self_excluded=True (zero API cost)
  → grade stored in logs/sim_results.jsonl
  → record_touch(prompt, file, reward=grade) updates matrix
  → intent_job marked 'simulated' (cleared only after copilot+test confirm)

Deepseek is the grader. Copilot is the executor. Test runner is verifier.
Ctrl+Z from os_hook = negative reward (overrides sim grade).

self_score() gate: local cosine(file_heat_vec, prompt_vec) × coupling_weight
Files below SELF_SCORE_THRESHOLD self-exclude silently — never hits deepseek.
"""
from __future__ import annotations
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-19T23:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add self_score gate + sim observatory feed
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

import json
import os
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SIM_LOG = ROOT / 'logs' / 'sim_results.jsonl'
INTENT_JOBS = ROOT / 'logs' / 'intent_jobs.jsonl'
JOURNAL = ROOT / 'logs' / 'prompt_journal.jsonl'

SELF_SCORE_THRESHOLD = 0.12  # files below this self-exclude (no deepseek call)

_GRADE_PROMPT = """You are grading whether a file needs to change to fulfill an intent.

INTENT: {intent_text}

FILE: {file_stem}
SOURCE (first 60 lines):
{source}

Answer JSON only:
{{"needs_change": true/false, "confidence": 0.0-1.0, "reason": "one line"}}

Rules:
- needs_change=true if the file is directly involved in the intent
- confidence > 0.7 = strong signal, < 0.4 = noise
- reason = single sentence, no preamble"""


def _load_api_key() -> str:
    for name in ('DEEPSEEK_API_KEY',):
        v = os.environ.get(name, '')
        if v:
            return v
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text('utf-8').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                return line.split('=', 1)[1].strip()
    return ''


def _call_deepseek(prompt: str, api_key: str) -> str | None:
    import json as _json
    import urllib.request
    body = _json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 120,
        'temperature': 0.1,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = _json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'  [file_sim] deepseek failed: {e}')
        return None


def _read_source(root: Path, file_stem: str) -> str:
    """Find file by stem and return first 60 lines."""
    # Search common locations
    for pattern in (f'src/{file_stem}.py', f'src/**/{file_stem}.py',
                    f'pigeon_compiler/**/{file_stem}.py',
                    f'pigeon_brain/**/{file_stem}.py'):
        hits = list(root.glob(pattern))
        if hits:
            lines = hits[0].read_text('utf-8', errors='replace').splitlines()[:60]
            return '\n'.join(lines)
    return '[not found]'


def _append_jsonl(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def self_score(file_stem: str, prompt_vec: dict[str, float],
               root: Path | None = None) -> float:
    """Local cosine gate — no API call.

    Builds a simple file identity vector from:
      - heat score (how often this file is touched)
      - intent matrix weight for words in prompt_vec
      - name overlap (word match between stem tokens and prompt words)

    Returns score in [0.0, 1.0].  Below SELF_SCORE_THRESHOLD = self-exclude.
    """
    root = root or ROOT

    # Component 1: intent matrix weight (bag-of-words cosine proxy)
    matrix_score = 0.0
    try:
        matrix_path = root / 'logs' / 'intent_matrix.json'
        if matrix_path.exists():
            matrix = json.loads(matrix_path.read_text('utf-8'))
            # sum prompt_vec weights for words that have non-zero file relevance
            # (simple proxy: if the word has any entry in matrix, it's relevant)
            for word_id, w in prompt_vec.items():
                row = matrix.get(word_id, {})
                if file_stem in row:
                    matrix_score += float(w) * float(row[file_stem])
    except Exception:
        pass
    matrix_score = min(matrix_score, 1.0)

    # Component 2: heat score from file_heat_map.json
    heat_score = 0.0
    try:
        heat_path = root / 'file_heat_map.json'
        if heat_path.exists():
            heat_map = json.loads(heat_path.read_text('utf-8'))
            # heat_map: {stem: {count, ...}} or {stem: float}
            val = heat_map.get(file_stem, 0)
            if isinstance(val, dict):
                val = val.get('count', val.get('heat', 0))
            # normalize: cap at 20 touches = 1.0
            heat_score = min(float(val) / 20.0, 1.0) * 0.3
    except Exception:
        pass

    # Component 3: name token overlap
    import re as _re
    stem_tokens = set(_re.split(r'[_\-\s]', file_stem.lower()))
    prompt_words = set()
    try:
        vocab_path = root / 'logs' / 'intent_vocab.json'
        if vocab_path.exists():
            vocab = json.loads(vocab_path.read_text('utf-8'))
            id_to_word = {str(v): k for k, v in vocab.items()}
            for word_id in prompt_vec:
                w = id_to_word.get(word_id, '')
                if w:
                    prompt_words.add(w.lower())
    except Exception:
        pass
    overlap = len(stem_tokens & prompt_words)
    name_score = min(overlap / max(len(prompt_words), 1), 1.0) * 0.4

    total = matrix_score * 0.6 + heat_score + name_score
    return round(min(total, 1.0), 4)


def _scan_all_stems(root: Path) -> list[str]:
    """Return all Python file stems under src/ and key subdirs."""
    stems = []
    for p in root.glob('src/**/*.py'):
        stems.append(p.stem)
    return list(set(stems))


def grade_file_for_intent(intent_text: str, file_stem: str,
                          root: Path | None = None,
                          api_key: str | None = None) -> dict:
    """Single sim: does file_stem need to change for this intent?
    Returns: {file_stem, needs_change, confidence, reason, grade}
    grade = confidence if needs_change else -confidence (for matrix reward)
    """
    root = root or ROOT
    api_key = api_key or _load_api_key()
    source = _read_source(root, file_stem)

    raw = None
    if api_key:
        prompt = _GRADE_PROMPT.format(
            intent_text=intent_text[:300],
            file_stem=file_stem,
            source=source[:2000],
        )
        raw = _call_deepseek(prompt, api_key)

    # Parse response
    result = {'file_stem': file_stem, 'needs_change': False,
              'confidence': 0.0, 'reason': 'no api key', 'grade': 0.0}
    if raw:
        try:
            # Extract JSON from response (may have surrounding text)
            start = raw.find('{')
            end = raw.rfind('}') + 1
            parsed = json.loads(raw[start:end]) if start >= 0 else {}
            result['needs_change'] = bool(parsed.get('needs_change', False))
            result['confidence'] = float(parsed.get('confidence', 0.5))
            result['reason'] = str(parsed.get('reason', ''))[:120]
            result['grade'] = result['confidence'] if result['needs_change'] else -result['confidence']
        except Exception:
            result['reason'] = f'parse failed: {raw[:80]}'

    return result


def run_sim(intent_text: str, prompt_text: str | None = None,
            top_n: int = 5, root: Path | None = None) -> list[dict]:
    """Run micro sim for an intent across top predicted files.
    
    1. Predict top_n files from intent_numeric
    2. Grade each with deepseek
    3. Log results to sim_results.jsonl
    4. Update intent_numeric matrix with grades
    5. Return graded results sorted by grade desc
    """
    root = root or ROOT
    api_key = _load_api_key()
    prompt_text = prompt_text or intent_text
    ts = datetime.now(timezone.utc).isoformat()

    # Step 1: encode prompt → vec (reuse if provided)
    prompt_vec: dict[str, float] = {}
    try:
        from src.intent_numeric_seq001_v001 import prompt_to_vector, predict_files, record_touch
        prompt_vec = {str(k): float(v) for k, v in prompt_to_vector(intent_text).items()}
    except Exception as e:
        print(f'  [file_sim] prompt_to_vector failed: {e}')
        try:
            from src.intent_numeric_seq001_v001 import predict_files, record_touch
        except Exception:
            pass

    # Step 2: all src file stems run self_score locally (zero API cost)
    all_stems = _scan_all_stems(root)
    # fallback: use predict_files if self_score gives empty (empty matrix cold start)
    shortlisted = []
    excluded = []
    if all_stems and prompt_vec:
        for stem in all_stems:
            score = self_score(stem, prompt_vec, root)
            if score >= SELF_SCORE_THRESHOLD:
                shortlisted.append((stem, score))
            else:
                excluded.append(stem)
        shortlisted.sort(key=lambda x: x[1], reverse=True)
        shortlisted = shortlisted[:top_n]  # cap at top_n survivors
    
    # Cold-start fallback — matrix empty, use predict_files heuristic
    if not shortlisted:
        try:
            shortlisted = list(predict_files(intent_text, top_n=top_n))
        except Exception as e:
            print(f'  [file_sim] predict_files fallback failed: {e}')

    # Log self-exclusions (no API call — just mark in sim_results)
    for stem in excluded:
        _append_jsonl(SIM_LOG, {
            'ts': ts, 'file_stem': stem, 'self_excluded': True,
            'self_score': self_score(stem, prompt_vec, root),
            'needs_change': False, 'confidence': 0.0,
            'reason': 'self_excluded: below threshold',
            'grade': 0.0, 'intent_preview': intent_text[:80],
        })

    candidates = [s for s, _ in shortlisted] if shortlisted and isinstance(shortlisted[0], tuple) else shortlisted

    if not candidates:
        print('  [file_sim] no candidates — run some prompts first to warm the matrix')
        return []

    print(f'  [file_sim] {len(excluded)} self-excluded · {len(candidates)} enter debate: "{intent_text[:55]}"')
    results = []
    for stem in candidates:
        r = grade_file_for_intent(intent_text, stem, root, api_key)
        r['ts'] = ts
        r['intent_preview'] = intent_text[:80]
        r['self_excluded'] = False
        results.append(r)
        flag = '✓' if r['needs_change'] else '·'
        print(f'    {flag} {stem}: conf={r["confidence"]:.2f} | {r["reason"][:60]}')

        # Step 4: update matrix — positive reward for relevant files
        if api_key and abs(r['grade']) > 0.1:
            try:
                record_touch(prompt_text, [stem],
                             learning_rate=0.05 * abs(r['grade']))
            except Exception:
                pass

        _append_jsonl(SIM_LOG, r)

    results.sort(key=lambda x: x['grade'], reverse=True)

    # Write intent_job entry
    _append_jsonl(INTENT_JOBS, {
        'ts': ts,
        'intent_text': intent_text[:300],
        'status': 'simulated',
        'top_files': [r['file_stem'] for r in results if r['needs_change']],
        'grades': {r['file_stem']: round(r['grade'], 3) for r in results},
        'actors_cleared': [],
    })

    return results


def apply_undo_penalty(file_stem: str, prompt_text: str, root: Path | None = None):
    """Called when Ctrl+Z detected after editing file_stem.
    Negative reward pushes this file away from this intent pattern.
    """
    root = root or ROOT
    try:
        from src.intent_numeric_seq001_v001 import record_touch
        record_touch(prompt_text, [file_stem], learning_rate=-0.08)
        print(f'  [file_sim] undo penalty → {file_stem}')
    except Exception as e:
        print(f'  [file_sim] undo penalty failed: {e}')


def clear_intent_job(intent_text: str, actor: str, root: Path | None = None):
    """Mark an intent job as cleared by an actor (copilot|tester|operator).
    Job is fully resolved when all 3 actors clear it.
    """
    root = root or ROOT
    jobs = []
    if INTENT_JOBS.exists():
        for line in INTENT_JOBS.read_text('utf-8').splitlines():
            if line.strip():
                jobs.append(json.loads(line))

    target = intent_text[:80]
    updated = False
    for job in reversed(jobs):
        if job.get('intent_text', '')[:80] == target and job.get('status') != 'cleared':
            if actor not in job.get('actors_cleared', []):
                job.setdefault('actors_cleared', []).append(actor)
            actors = set(job['actors_cleared'])
            if {'copilot', 'tester', 'operator'}.issubset(actors) or len(actors) >= 2:
                job['status'] = 'cleared'
                job['cleared_ts'] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if updated:
        INTENT_JOBS.write_text(
            '\n'.join(json.dumps(j, ensure_ascii=False) for j in jobs) + '\n',
            'utf-8')


if __name__ == '__main__':
    import sys
    intent = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'wire prompt_to_vector into u_pj journal entries'
    results = run_sim(intent, top_n=5)
    print(f'\n  {len([r for r in results if r["needs_change"]])} files need change')
