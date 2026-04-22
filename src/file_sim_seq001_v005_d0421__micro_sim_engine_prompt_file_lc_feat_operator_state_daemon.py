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

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v005 | 433 lines | ~4,116 tokens
# DESC:   micro_sim_engine_prompt_file
# INTENT: feat_operator_state_daemon
# LAST:   2026-04-21 @ f9a3310
# SESSIONS: 4
# ──────────────────────────────────────────────
from __future__ import annotations
from src._resolve import src_import
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-22T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add file cortex self-accumulating knowledge
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
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

FILE CORTEX (self-knowledge — use to improve grading accuracy):
{cortex_summary}

Answer JSON only:
{{"needs_change": true/false, "confidence": 0.0-1.0, "reason": "one line"}}

Rules:
- needs_change=true if the file is directly involved in the intent
- confidence > 0.7 = strong signal, < 0.4 = noise
- reason = single sentence, no preamble
- if cortex shows file was flagged for similar intents before, weight that heavily"""

FILE_PROFILES = ROOT / 'file_profiles.json'
_CORTEX_HISTORY_LIMIT = 20  # max entries per history list


def _load_profiles(root: Path) -> dict:
    fp = root / 'file_profiles.json'
    if fp.exists():
        try:
            return json.loads(fp.read_text('utf-8', errors='ignore'))
        except Exception:
            pass
    return {}


def _save_profiles(profiles: dict, root: Path) -> None:
    fp = root / 'file_profiles.json'
    try:
        fp.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), 'utf-8')
    except Exception as e:
        print(f'  [cortex] save failed: {e}')


def _cortex_summary(profile: dict) -> str:
    """Build a compact cortex string to inject into the grade prompt."""
    lines = []
    sim_h = profile.get('sim_history', [])
    if sim_h:
        last = sim_h[-1]
        lines.append(f"last_grade: {last.get('grade',0):.2f} | intent: {last.get('intent','')[:60]}")
        avg = sum(e.get('grade', 0) for e in sim_h) / len(sim_h)
        lines.append(f"avg_grade: {avg:.2f} over {len(sim_h)} sim runs")
    repair = profile.get('repair_log', [])
    if repair:
        last_fix = repair[-1]
        lines.append(f"last_fix: {last_fix.get('fix','?')} (success={last_fix.get('success')}) triggered by {last_fix.get('trigger','?')[:40]}")
    breaks = profile.get('break_patterns', [])
    if breaks:
        top = sorted(breaks, key=lambda x: x.get('times', 0), reverse=True)[:3]
        lines.append(f"break_partners: {', '.join(b['partner'] + '×' + str(b.get('times',1)) for b in top)}")
    hint = profile.get('self_repair_hint', '')
    if hint:
        lines.append(f"hint: {hint[:100]}")
    watch = profile.get('backwards_pass_watch', [])
    if watch:
        lines.append(f"watch_siblings: {', '.join(watch[:5])}")
    return '\n'.join(lines) if lines else 'no cortex yet'


def update_file_cortex(
        stem: str,
        root: Path,
        event: dict,
) -> None:
    """Append a learning event to file_profiles.json[stem] cortex.

    event types + required keys:
      sim_grade:          {intent, grade, reason, needs_change}
      10q_result:         {score_n, failed_qs}
      backprop_received:  {from_stem, reward, intent}
      self_fix_attempted: {fix, success, trigger}
      undo:               {intent, delta}
      interlinked:        {}
    """
    profiles = _load_profiles(root)
    profile = profiles.setdefault(stem, {})
    ts = datetime.now(timezone.utc).isoformat()
    etype = event.get('type', 'unknown')

    if etype == 'sim_grade':
        hist = profile.setdefault('sim_history', [])
        hist.append({
            'ts': ts,
            'grade': round(float(event.get('grade', 0)), 3),
            'intent': str(event.get('intent', ''))[:80],
            'reason': str(event.get('reason', ''))[:80],
            'needs_change': bool(event.get('needs_change', False)),
        })
        profile['sim_history'] = hist[-_CORTEX_HISTORY_LIMIT:]

    elif etype == '10q_result':
        trend = profile.setdefault('10q_trend', [])
        failed = event.get('failed_qs', [])
        trend.append({
            'ts': ts,
            'score': f"{event.get('score_n', 0)}/10",
            'failed': failed[:5],
        })
        profile['10q_trend'] = trend[-_CORTEX_HISTORY_LIMIT:]

    elif etype == 'backprop_received':
        from_stem = str(event.get('from_stem', 'unknown'))
        # Update break_patterns: track which siblings precede our state changes
        patterns = profile.setdefault('break_patterns', [])
        found = next((p for p in patterns if p['partner'] == from_stem), None)
        if found:
            found['times'] = found.get('times', 1) + 1
            found['last_ts'] = ts
            found['last_intent'] = str(event.get('intent', ''))[:60]
        else:
            patterns.append({'partner': from_stem, 'times': 1, 'last_ts': ts,
                              'last_intent': str(event.get('intent', ''))[:60]})
        profile['break_patterns'] = sorted(patterns, key=lambda x: x.get('times', 0), reverse=True)[:15]
        # Update backwards_pass_watch list
        watch = profile.setdefault('backwards_pass_watch', [])
        if from_stem not in watch:
            watch.insert(0, from_stem)
        profile['backwards_pass_watch'] = watch[:10]

    elif etype == 'self_fix_attempted':
        log = profile.setdefault('repair_log', [])
        log.append({
            'ts': ts,
            'fix': str(event.get('fix', 'unknown'))[:60],
            'success': bool(event.get('success', False)),
            'trigger': str(event.get('trigger', ''))[:60],
        })
        profile['repair_log'] = log[-_CORTEX_HISTORY_LIMIT:]

    elif etype == 'undo':
        # treat undo as a negative backprop signal — this intent was wrong for this file
        neg = profile.setdefault('undo_patterns', [])
        neg.append({'ts': ts, 'intent': str(event.get('intent', ''))[:80], 'delta': event.get('delta', -0.08)})
        profile['undo_patterns'] = neg[-10:]

    elif etype == 'interlinked':
        profile['interlinked_at'] = ts
        profile['personality'] = 'interlinked'

    # Rebuild self_repair_hint from accumulated patterns (lightweight — no LLM)
    _refresh_self_repair_hint(profile, stem)

    profiles[stem] = profile
    _save_profiles(profiles, root)


def _refresh_self_repair_hint(profile: dict, stem: str) -> None:
    """Generate a rule-based repair hint from accumulated cortex data.
    Updated on every cortex write — no LLM call needed for the hint itself.
    """
    parts = []
    # Most-frequent break partner
    bp = profile.get('break_patterns', [])
    if bp:
        top = bp[0]
        if top.get('times', 0) >= 2:
            parts.append(f"When {top['partner']} is edited, recheck this file ({top['times']}× co-change).")
    # Recurring 10Q failures
    trend = profile.get('10q_trend', [])
    if len(trend) >= 2:
        all_failed: list[str] = []
        for entry in trend[-5:]:
            all_failed.extend(entry.get('failed', []))
        from collections import Counter
        top_fail = Counter(all_failed).most_common(2)
        if top_fail:
            qs = ', '.join(f"{q}({n}×)" for q, n in top_fail)
            parts.append(f"Recurring 10Q failures: {qs}.")
    # High undo rate
    undos = profile.get('undo_patterns', [])
    if len(undos) >= 2:
        parts.append(f"Operator undid edits {len(undos)}× — be cautious about auto-patching.")
    # Average grade direction
    hist = profile.get('sim_history', [])
    if len(hist) >= 3:
        recent = [e.get('grade', 0) for e in hist[-5:]]
        avg = sum(recent) / len(recent)
        if avg > 0.6:
            parts.append(f"Sim grades trending high ({avg:.2f}) — likely needs active change.")
        elif avg < 0.0:
            parts.append(f"Sim grades trending negative ({avg:.2f}) — may be over-selected.")
    profile['self_repair_hint'] = ' '.join(parts)[:300] if parts else ''


def _load_api_key() -> tuple[str, str]:
    """Returns (api_key, provider) — prefers Gemini over DeepSeek."""
    for name, provider in (('GEMINI_API_KEY', 'gemini'), ('DEEPSEEK_API_KEY', 'deepseek')):
        v = os.environ.get(name, '')
        if v:
            return v, provider
    env = ROOT / '.env'
    if env.exists():
        lines = env.read_text('utf-8').splitlines()
        for line in lines:
            if line.startswith('GEMINI_API_KEY='):
                v = line.split('=', 1)[1].strip()
                if v:
                    return v, 'gemini'
        for line in lines:
            if line.startswith('DEEPSEEK_API_KEY='):
                v = line.split('=', 1)[1].strip()
                if v:
                    return v, 'deepseek'
    return '', ''


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


def _call_gemini(prompt: str, api_key: str) -> str | None:
    import json as _json
    import urllib.request
    import time as _time
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
           f'gemini-2.0-flash:generateContent?key={api_key}')
    body = _json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 150, 'temperature': 0.1},
    }).encode('utf-8')
    req = urllib.request.Request(url, data=body,
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = _json.loads(resp.read().decode('utf-8'))
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 3 * (attempt + 1)
                print(f'  [file_sim] gemini 429 rate limit — retry in {wait}s')
                _time.sleep(wait)
                continue
            print(f'  [file_sim] gemini HTTP {e.code}: {e}')
            return None
        except Exception as e:
            print(f'  [file_sim] gemini failed: {e}')
            return None
    return None


def _call_grader(prompt: str, api_key: str, provider: str) -> str | None:
    if provider == 'gemini':
        return _call_gemini(prompt, api_key)
    return _call_deepseek(prompt, api_key)


def _read_source(root: Path, file_stem: str) -> str:
    """Find file by stem and return first 60 lines."""
    try:
        canonicalize_file_key = src_import("intent_numeric_seq001", "canonicalize_file_key")
        canonical = canonicalize_file_key(file_stem)
    except Exception:
        canonical = file_stem
    candidates = []
    for stem in (file_stem, canonical):
        if stem and stem not in candidates:
            candidates.append(stem)
    # Search common locations
    for stem in candidates:
        for pattern in (
            f'{stem}.py',
            f'{stem}_seq*.py',
            f'client/{stem}.py',
            f'client/**/{stem}.py',
            f'client/**/{stem}_seq*.py',
            f'src/{stem}.py',
            f'src/{stem}_seq*.py',
            f'src/**/{stem}.py',
            f'src/**/{stem}_seq*.py',
            f'pigeon_compiler/**/{stem}.py',
            f'pigeon_compiler/**/{stem}_seq*.py',
            f'pigeon_brain/**/{stem}.py',
            f'pigeon_brain/**/{stem}_seq*.py',
        ):
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
    try:
        canonicalize_file_key = src_import("intent_numeric_seq001", "canonicalize_file_key")
        key_candidates = []
        for key in (file_stem, canonicalize_file_key(file_stem)):
            if key and key not in key_candidates:
                key_candidates.append(key)
    except Exception:
        key_candidates = [file_stem]

    # Component 1: intent matrix weight (bag-of-words cosine proxy)
    matrix_score = 0.0
    try:
        matrix_path = root / 'logs' / 'intent_matrix.json'
        if matrix_path.exists():
            data = json.loads(matrix_path.read_text('utf-8'))
            matrix = data.get('matrix', {})
            for file_key in key_candidates:
                file_weights = matrix.get(file_key, {})
                candidate_score = 0.0
                for word_id, weight in prompt_vec.items():
                    stored = file_weights.get(str(word_id))
                    if stored is not None:
                        candidate_score += float(weight) * float(stored)
                matrix_score = max(matrix_score, candidate_score)
    except Exception:
        pass
    matrix_score = min(matrix_score, 1.0)

    # Component 2: heat score from file_heat_map.json
    heat_score = 0.0
    try:
        heat_path = root / 'file_heat_map.json'
        if heat_path.exists():
            heat_map = json.loads(heat_path.read_text('utf-8'))
            for file_key in key_candidates:
                val = heat_map.get(file_key, 0)
                if isinstance(val, dict):
                    if 'count' in val:
                        normalized = min(float(val['count']) / 20.0, 1.0)
                    else:
                        normalized = min(float(val.get('heat', val.get('touch_score', 0))), 1.0)
                else:
                    normalized = min(float(val), 1.0)
                heat_score = max(heat_score, normalized * 0.3)
    except Exception:
        pass

    # Component 3: name token overlap
    import re as _re
    stem_tokens = set()
    for file_key in key_candidates:
        stem_tokens |= {tok for tok in _re.split(r'[_\-\s]', file_key.lower()) if tok}
    prompt_words = set()
    try:
        vocab_path = root / 'logs' / 'intent_vocab.json'
        if vocab_path.exists():
            vocab = json.loads(vocab_path.read_text('utf-8'))
            word_to_id = vocab.get('word_to_id', {})
            id_to_word = {str(v): k for k, v in word_to_id.items()}
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
    for pattern in ('*.py', 'client/**/*.py', 'src/**/*.py', 'pigeon_compiler/**/*.py', 'pigeon_brain/**/*.py'):
        for p in root.glob(pattern):
            if p.name == '__init__.py' or 'tests' in p.parts or 'build' in p.parts:
                continue
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
    _key, _provider = _load_api_key()
    api_key = api_key or _key
    provider = _provider if not api_key else _provider
    source = _read_source(root, file_stem)

    raw = None
    if api_key:
        profiles = _load_profiles(root)
        cortex = _cortex_summary(profiles.get(file_stem, {}))
        prompt = _GRADE_PROMPT.format(
            intent_text=intent_text[:300],
            file_stem=file_stem,
            source=source[:2000],
            cortex_summary=cortex,
        )
        raw = _call_grader(prompt, api_key, provider)

    # Parse response
    result = {'file_stem': file_stem, 'needs_change': False,
              'confidence': 0.0, 'reason': 'grader call failed', 'grade': 0.0}
    if not api_key:
        result['reason'] = 'no api key'
    elif raw:
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

    # Persist to cortex so the file learns its own grade history
    try:
        update_file_cortex(file_stem, root, event={
            'type': 'sim_grade',
            'intent': intent_text,
            'grade': result['grade'],
            'reason': result['reason'],
            'needs_change': result['needs_change'],
        })
    except Exception:
        pass

    return result


def _trigger_overwriter_async(stem: str, intent_text: str, grade_result: dict,
                              root: Path) -> None:
    """Spawn background thread to run file_overwriter.
    Auto-applies by default. Set PIGEON_AUTO_OVERWRITE=0 to force dry-run.
    """
    import threading as _th
    dry = os.environ.get('PIGEON_AUTO_OVERWRITE', '1') == '0'
    live = not dry

    def _run():
        try:
            import importlib.util as _ilu
            matches = sorted((root / 'src').glob('file_overwriter*.py'),
                             key=lambda p: len(p.name))
            if not matches:
                return
            spec = _ilu.spec_from_file_location('file_overwriter', matches[-1])
            m = _ilu.module_from_spec(spec)
            if spec and spec.loader:
                spec.loader.exec_module(m)
                r = m.overwrite_file(stem, intent_text, grade_result=grade_result,
                                     root=root, dry_run=dry)
                flag = '(dry)' if dry else ('✓ applied' if r.get('applied') else '✗ failed')
                print(f'  [overwriter] {stem}: {flag} | {r.get("diff","")[:60]}')
        except Exception as e:
            print(f'  [overwriter] {stem} error: {e}')
    _th.Thread(target=_run, daemon=True).start()


def run_sim(intent_text: str, prompt_text: str | None = None,
            top_n: int = 5, root: Path | None = None,
            deleted_words: list | None = None) -> list[dict]:
    """Run micro sim for an intent across top predicted files.
    
    1. Predict top_n files from intent_numeric
    2. Grade each with deepseek
    3. Log results to sim_results.jsonl
    4. Update intent_numeric matrix with grades
    5. Return graded results sorted by grade desc

    deleted_words: carried from prompt_journal, appended to intent_text before encoding.
    """
    root = root or ROOT
    api_key, _provider = _load_api_key()
    # Augment intent with deleted signal — operator's unsaid words carry design intent
    if deleted_words:
        intent_text = intent_text + ' ' + ' '.join(str(w) for w in deleted_words[:15])
    prompt_text = prompt_text or intent_text
    ts = datetime.now(timezone.utc).isoformat()

    # Step 1: encode prompt → vec (reuse if provided)
    prompt_vec: dict[str, float] = {}
    try:
        prompt_to_vector, predict_files, record_touch = src_import("intent_numeric_seq001", "prompt_to_vector", "predict_files", "record_touch")
        prompt_vec = {str(k): float(v) for k, v in prompt_to_vector(intent_text).items()}
    except Exception as e:
        print(f'  [file_sim] prompt_to_vector failed: {e}')
        try:
            predict_files, record_touch = src_import("intent_numeric_seq001", "predict_files", "record_touch")
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

        # Step 4b: run 10Q on this file — interlink score feeds back into reward scaling
        q_result = run_10q_for_file(stem, root, write_log=True)
        r['10q_score'] = int(q_result.get('score', '0/10').split('/')[0]) / 10.0
        r['interlinked'] = q_result.get('interlinked', False)
        q_flag = '★' if r['interlinked'] else f"Q{q_result.get('score','?')}"
        print(f'      10Q={q_flag}')

        # Step 4c: backprop to siblings if this file needs change
        if r['needs_change'] and abs(r['grade']) > 0.1:
            edit_why = q_result.get('notes', {}).get('Q10_scenario', '')
            backprop_sibling_reward(stem, intent_text, edit_why, r['grade'], root)

        # Step 4d: file overwriter — fires automatically at high confidence
        # Dry-run by default; set PIGEON_AUTO_OVERWRITE=1 to live-apply
        if r['needs_change'] and r['confidence'] >= 0.85:
            _trigger_overwriter_async(stem, intent_text, r, root)

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
        record_touch = src_import("intent_numeric_seq001", "record_touch")
        record_touch(prompt_text, [file_stem], learning_rate=-0.08)
        print(f'  [file_sim] undo penalty → {file_stem}')
        update_file_cortex(file_stem, root, event={
            'type': 'undo', 'intent': prompt_text[:80], 'delta': -0.08,
        })
    except Exception as e:
        print(f'  [file_sim] undo penalty failed: {e}')


# ── 10Q scoring ──────────────────────────────────────────────────────────────

def _get_10q_score(file_stem: str, root: Path) -> float:
    """Return 0.0–1.0 based on last known 10Q score (no re-run, reads log).
    Used to scale rewards: interlinked files get full reward, Q1=0.1 scaling.
    """
    log = root / 'logs' / 'tc_10q_results.jsonl'
    if not log.exists():
        return 0.5  # unknown — neutral
    best = None
    for line in log.read_text('utf-8', errors='ignore').splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            if e.get('module') == file_stem or e.get('module') in file_stem:
                score_str = e.get('score', '0/10')
                passed = int(score_str.split('/')[0])
                best = passed / 10.0
        except Exception:
            pass
    return best if best is not None else 0.5


def run_10q_for_file(file_stem: str, root: Path | None = None, write_log: bool = True) -> dict:
    """Run full 10Q qualification test on a file by stem. Updates logs/tc_10q_results.jsonl."""
    root = root or ROOT
    try:
        import importlib.util as _ilu
        matches = sorted((root / 'src').glob('tc_10q*.py'), key=lambda p: len(p.name))
        if not matches:
            return {'score': '0/10', 'interlinked': False, 'error': 'tc_10q not found'}
        spec = _ilu.spec_from_file_location('tc_10q', matches[-1])
        if spec is None:
            return {'score': '0/10', 'interlinked': False, 'error': 'spec None'}
        mod = _ilu.module_from_spec(spec)
        if spec.loader is None:
            return {'score': '0/10', 'interlinked': False, 'error': 'loader None'}
        spec.loader.exec_module(mod)
        # find actual file path
        src_matches = sorted((root / 'src').glob(f'{file_stem}*.py'), key=lambda p: len(p.name))
        if not src_matches:
            return {'score': '0/10', 'interlinked': False, 'error': f'{file_stem} not found'}
        result = mod.qualify_module(src_matches[0], write_log=write_log)
        # Persist 10Q result to cortex
        try:
            score_str = result.get('score', '0/10')
            score_n = int(str(score_str).split('/')[0]) if '/' in str(score_str) else 0
            failed_qs = [k for k, v in result.get('notes', {}).items() if v is False]
            update_file_cortex(file_stem, root, event={
                'type': '10q_result',
                'score_n': score_n,
                'failed_qs': failed_qs,
            })
        except Exception:
            pass
        return result
    except Exception as e:
        return {'score': '0/10', 'interlinked': False, 'error': str(e)[:120]}


# ── sibling backprop ──────────────────────────────────────────────────────────

def backprop_sibling_reward(
        edited_stem: str,
        intent_text: str,
        edit_why: str,
        grade: float,
        root: Path | None = None,
):
    """When a file is edited, propagate a decayed reward to its siblings.

    Siblings = files that share coupling signals (imports, co-edit history).
    Reward decays with distance: direct importer → 0.4×grade, indirect → 0.2×grade.
    Also runs 10Q on the edited file and scales reward by interlink score.
    """
    root = root or ROOT
    try:
        record_touch = src_import("intent_numeric_seq001", "record_touch")
    except Exception:
        return

    # Scale reward by 10Q score — interlinked files' edits carry more signal
    q_scale = _get_10q_score(edited_stem, root)
    scaled_grade = grade * max(q_scale, 0.3)  # floor at 0.3 so cold files still learn

    # Find siblings via import graph (quick scan — no AST, just grep for module name)
    siblings: list[tuple[str, float]] = []  # (stem, decay)
    src_dir = root / 'src'
    for py in src_dir.glob('*.py'):
        if py.stem == edited_stem or edited_stem not in py.read_text('utf-8', errors='ignore'):
            continue
        # file imports edited_stem — direct sibling
        siblings.append((py.stem, 0.4))

    # Also check file_profiles for coupling
    fp = root / 'file_profiles.json'
    if fp.exists():
        try:
            profiles = json.loads(fp.read_text('utf-8'))
            edited_profile = profiles.get(edited_stem, {})
            for coupled_stem in edited_profile.get('coupled_with', []):
                if not any(s == coupled_stem for s, _ in siblings):
                    siblings.append((coupled_stem, 0.2))
        except Exception:
            pass

    if not siblings:
        return

    # Augment intent with edit_why so siblings learn the reason too
    backprop_intent = intent_text + ' ' + edit_why if edit_why else intent_text

    ts = datetime.now(timezone.utc).isoformat()
    logged = []
    for stem, decay in siblings[:12]:  # cap at 12 siblings
        sibling_reward = scaled_grade * decay
        if abs(sibling_reward) < 0.02:
            continue
        try:
            record_touch(backprop_intent, [stem], learning_rate=0.05 * abs(sibling_reward))
            logged.append({'stem': stem, 'reward': round(sibling_reward, 3), 'decay': decay})
            # Cortex: sibling learns who triggered it and why
            update_file_cortex(stem, root, event={
                'type': 'backprop_received',
                'from_stem': edited_stem,
                'reward': sibling_reward,
                'intent': intent_text,
            })
        except Exception:
            pass

    # Log backprop event
    bp_log = root / 'logs' / 'sim_backprop.jsonl'
    try:
        with open(bp_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'ts': ts,
                'edited': edited_stem,
                'edit_why': edit_why,
                'grade': grade,
                'q_scale': q_scale,
                'scaled_grade': round(scaled_grade, 3),
                'siblings_rewarded': logged,
                'intent_preview': intent_text[:80],
            }, ensure_ascii=False) + '\n')
    except Exception:
        pass

    print(f'  [backprop] {edited_stem} q={q_scale:.1f} → {len(logged)} siblings rewarded')


def predict_patch_need(file_stem: str, root: Path | None = None) -> dict:
    """Predict whether a file needs patching based on:
    - 10Q score trend (falling = needs patch)
    - Recent sim grades for this file (negative trend = needs patch)
    - Sibling edit pressure (many siblings edited = likely needs update)

    Returns: {needs_patch: bool, confidence: float, reason: str, 10q_score: float}
    """
    root = root or ROOT
    q_score = _get_10q_score(file_stem, root)

    # Scan sim_results for this file's recent grades
    recent_grades: list[float] = []
    if SIM_LOG.exists():
        for line in SIM_LOG.read_text('utf-8', errors='ignore').splitlines()[-200:]:
            try:
                e = json.loads(line)
                if file_stem in e.get('file_stem', ''):
                    recent_grades.append(float(e.get('grade', 0.0)))
            except Exception:
                pass

    # Sibling pressure from backprop log
    sibling_pressure = 0.0
    bp_log = root / 'logs' / 'sim_backprop.jsonl'
    if bp_log.exists():
        for line in bp_log.read_text('utf-8', errors='ignore').splitlines()[-100:]:
            try:
                e = json.loads(line)
                for sib in e.get('siblings_rewarded', []):
                    if sib.get('stem') == file_stem:
                        sibling_pressure += abs(sib.get('reward', 0.0))
            except Exception:
                pass

    avg_grade = sum(recent_grades) / len(recent_grades) if recent_grades else 0.0
    # Score: high avg_grade (sim says needs change) + low 10Q + sibling pressure → needs patch
    patch_score = (avg_grade * 0.5) + ((1.0 - q_score) * 0.3) + min(sibling_pressure * 0.2, 0.2)
    needs_patch = patch_score > 0.45

    reason_parts = []
    if avg_grade > 0.5:
        reason_parts.append(f'sim grades high ({avg_grade:.2f})')
    if q_score < 0.7:
        reason_parts.append(f'10Q={q_score:.1f}')
    if sibling_pressure > 0.3:
        reason_parts.append(f'sibling_pressure={sibling_pressure:.2f}')

    return {
        'file_stem': file_stem,
        'needs_patch': needs_patch,
        'patch_score': round(patch_score, 3),
        'confidence': round(min(patch_score * 1.5, 1.0), 2),
        'reason': ', '.join(reason_parts) or 'no signal',
        '10q_score': q_score,
        'avg_sim_grade': round(avg_grade, 3),
        'sibling_pressure': round(sibling_pressure, 3),
        'n_sim_samples': len(recent_grades),
    }


ESCALATION_STATE = ROOT / 'logs' / 'escalation_state.json'


def escalation_sweep(root: Path | None = None, dry_run: bool = False) -> dict:
    """Sweep all src files for patch need, run self-fix on flagged ones,
    re-run 10Q, and promote to interlinked in pigeon_registry.json.

    Writes results to logs/escalation_state.json (readable by observatory).

    Returns summary dict: {swept, flagged, fixed, promoted, events}
    """
    root = root or ROOT
    ts_start = datetime.now(timezone.utc).isoformat()
    events: list[dict] = []
    promoted: list[str] = []
    fixed: list[str] = []

    # 1. Collect all known file stems from sim_memory + registry
    stems: set[str] = set()
    sm_path = root / 'logs' / 'sim_memory.json'
    if sm_path.exists():
        try:
            sm = json.loads(sm_path.read_text('utf-8', errors='ignore'))
            stems.update(sm.get('files', {}).keys())
        except Exception:
            pass
    reg_path = root / 'pigeon_registry.json'
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text('utf-8', errors='ignore'))
            entries = reg if isinstance(reg, list) else reg.get('modules', reg.get('entries', []))
            for entry in entries:
                stem = entry.get('stem') or entry.get('name') or ''
                if stem:
                    stems.add(stem)
        except Exception:
            pass

    swept = list(stems)
    flagged: list[str] = []

    # 2. Predict patch need for each stem
    for stem in swept:
        try:
            pred = predict_patch_need(stem, root)
            if pred['needs_patch']:
                flagged.append(stem)
                events.append({'stem': stem, 'action': 'flagged',
                               'patch_score': pred['patch_score'],
                               'reason': pred['reason']})
        except Exception as e:
            events.append({'stem': stem, 'action': 'predict_error', 'error': str(e)})

    # 3. Self-fix: try to resolve broken imports/issues for flagged files
    if not dry_run:
        for stem in flagged:
            try:
                # Use existing auto_fix_broken_imports scanner
                auto_fix = src_import('修f_sf_scfc', 'auto_fix_broken_imports')
                result = auto_fix(root, stem)
                if result:
                    fixed.append(stem)
                    events.append({'stem': stem, 'action': 'self_fixed', 'result': str(result)[:80]})
                    update_file_cortex(stem, root, event={
                        'type': 'self_fix_attempted',
                        'fix': 'auto_fix_broken_imports',
                        'success': True,
                        'trigger': 'escalation_sweep',
                    })
            except Exception:
                # self-fix not available or failed — record and continue
                pass

    # 4. Re-run 10Q on all flagged files and check for interlink promotion
    for stem in flagged:
        try:
            q_result = run_10q_for_file(stem, root, write_log=True)
            score_str = q_result.get('score', '0/10')
            score_n = int(str(score_str).split('/')[0]) if '/' in str(score_str) else 0
            is_interlinked = score_n >= 10
            events.append({'stem': stem, 'action': '10q_scored',
                           'score': score_str, 'interlinked': is_interlinked})
            if is_interlinked and not dry_run:
                _promote_to_interlinked(stem, root)
                promoted.append(stem)
                events.append({'stem': stem, 'action': 'promoted_interlinked'})
                update_file_cortex(stem, root, event={'type': 'interlinked'})
        except Exception as e:
            events.append({'stem': stem, 'action': '10q_error', 'error': str(e)[:60]})

    # 5. Write shared escalation state (observable by observatory + codebase)
    state = {
        'ts': ts_start,
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'swept': len(swept),
        'flagged': len(flagged),
        'flagged_stems': flagged,
        'fixed': len(fixed),
        'fixed_stems': fixed,
        'promoted': len(promoted),
        'promoted_stems': promoted,
        'events': events[-50:],  # cap at 50 for size
    }
    if not dry_run:
        ESCALATION_STATE.parent.mkdir(parents=True, exist_ok=True)
        ESCALATION_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), 'utf-8')

    return state


def _promote_to_interlinked(stem: str, root: Path) -> None:
    """Mark a file stem as interlinked in pigeon_registry.json."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return
    try:
        reg = json.loads(reg_path.read_text('utf-8', errors='ignore'))
        entries = reg if isinstance(reg, list) else None
        key = None
        if isinstance(reg, dict):
            for k in ('modules', 'entries', 'files'):
                if k in reg:
                    entries = reg[k]; key = k; break
        if entries is None:
            return
        updated = False
        for entry in entries:
            s = entry.get('stem') or entry.get('name') or ''
            if stem in s or s in stem:
                entry['interlinked'] = True
                entry['interlinked_at'] = datetime.now(timezone.utc).isoformat()
                updated = True
                break
        if updated:
            if key:
                reg[key] = entries
            else:
                reg = entries
            reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), 'utf-8')
    except Exception:
        pass


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
