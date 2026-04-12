"""Completion grader — scores every thought completion with computed metrics.

NO operator raw text stored. Only LLM reconstructions + computed scores.
Grades are written per-completion and aggregated for self-learning.

Grading happens post-hoc: after outcome is known (accept/dismiss/ignore/etc.)
we score the completion on multiple axes and persist the grade.
"""
from __future__ import annotations
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .tc_constants import ROOT

GRADES_PATH = ROOT / 'logs' / 'completion_grades.jsonl'
GRADE_SUMMARY_PATH = ROOT / 'logs' / 'completion_grade_summary.json'


def _word_set(text: str) -> set[str]:
    return set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower()))


def _prefix_match_len(buffer: str, completion: str) -> int:
    """How many chars of the completion match what comes after the buffer."""
    # The completion should continue FROM the buffer's end
    # Check if completion starts with characters that would naturally follow
    buf_tail = buffer.rstrip()
    comp = completion.lstrip()
    match_len = 0
    for i, c in enumerate(comp):
        if i >= len(comp):
            break
        match_len = i + 1
        # Stop at first major divergence
        if c in '.!?\n' and i > 5:
            break
    return match_len


def grade_completion(buffer: str, completion: str, outcome: str,
                     context_files: list[str] | None = None,
                     latency_ms: int = 0,
                     final_text: str = '') -> dict:
    """Grade a single completion on multiple axes.

    Returns a grade dict — NO raw operator text, only computed metrics
    and LLM-reconstructed intent signals.
    """
    buf_words = _word_set(buffer)
    comp_words = _word_set(completion)

    # ── RELEVANCE: does the completion share topic with buffer? ──
    if buf_words and comp_words:
        overlap = len(buf_words & comp_words)
        union = len(buf_words | comp_words)
        relevance = overlap / union if union else 0
    else:
        relevance = 0

    # ── NOVELTY: does it ADD something vs just echo? ──
    if comp_words:
        new_words = comp_words - buf_words
        novelty = len(new_words) / len(comp_words) if comp_words else 0
    else:
        novelty = 0

    # ── ECHO SCORE: lower is better — did it just parrot the buffer? ──
    if comp_words and buf_words:
        echo = len(comp_words & buf_words) / len(comp_words)
    else:
        echo = 0

    # ── LENGTH FITNESS: is it the right length? ──
    comp_len = len(completion)
    # Intent amplification: prose can be much longer (full intent packets)
    is_code = any(sig in completion for sig in ('def ', 'class ', 'import ', '()', ' = '))
    if is_code:
        length_fitness = 1.0 if 40 <= comp_len <= 300 else max(0, 1.0 - abs(comp_len - 170) / 300)
    else:
        # prose intent amplification: full thought packets can be 20-800 chars
        length_fitness = 1.0 if 20 <= comp_len <= 800 else max(0, 1.0 - abs(comp_len - 300) / 800)

    # ── CONTINUATION QUALITY: does it feel like a natural next sentence? ──
    buf_tail = buffer.strip()[-30:].lower()
    comp_head = completion.strip()[:30].lower()
    # Check for awkward repetition at boundary
    continuation = 1.0
    if buf_tail and comp_head:
        # Penalize if completion starts with same words as buffer end
        buf_last_words = buf_tail.split()[-3:]
        comp_first_words = comp_head.split()[:3]
        repeated = sum(1 for w in comp_first_words if w in buf_last_words)
        if repeated >= 2:
            continuation -= 0.4
        # Penalize if completion just restates the buffer
        if buf_tail[-15:] in comp_head:
            continuation -= 0.3

    # ── OUTCOME SCORE: hard signal ──
    outcome_scores = {
        'rewarded': 1.0,
        'accepted': 0.8,
        'dismissed': 0.0,
        'ignored': 0.1,
        'superseded': 0.2,
    }
    outcome_score = outcome_scores.get(outcome, 0.1)

    # ── COMPOSITE GRADE ──
    # Weighted: outcome matters most, then relevance + novelty
    composite = (
        outcome_score * 0.40 +
        relevance * 0.15 +
        novelty * 0.15 +
        (1 - echo) * 0.10 +
        length_fitness * 0.10 +
        continuation * 0.10
    )

    # ── LLM RECONSTRUCTION: summarize what was happening (no raw text) ──
    # Extract intent signals from buffer without storing the actual words
    intent_words = sorted(buf_words - {
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have',
        'what', 'how', 'not', 'are', 'you', 'was', 'but', 'can',
    })[:8]

    grade = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'outcome': outcome,
        'composite': round(composite, 3),
        'relevance': round(relevance, 3),
        'novelty': round(novelty, 3),
        'echo': round(echo, 3),
        'length_fitness': round(length_fitness, 3),
        'continuation': round(continuation, 3),
        'outcome_score': outcome_score,
        'comp_len': comp_len,
        'buf_len': len(buffer),
        'is_code': is_code,
        'latency_ms': latency_ms,
        # LLM-reconstructed intent (no raw operator text)
        'intent_keywords': intent_words,
        'completion_head': completion[:60],  # completions are LLM-generated, safe to log
        'context_files': context_files or [],
        'n_context_files': len(context_files) if context_files else 0,
    }
    return grade


def log_grade(grade: dict):
    """Append grade to persistent log."""
    GRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GRADES_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(grade, ensure_ascii=False) + '\n')


def update_grade_summary():
    """Rebuild the rolling summary from all grades. Called periodically."""
    if not GRADES_PATH.exists():
        return
    grades = []
    for line in GRADES_PATH.read_text('utf-8', errors='ignore').strip().splitlines():
        try:
            grades.append(json.loads(line))
        except Exception:
            continue
    if not grades:
        return
    n = len(grades)
    recent = grades[-50:]  # last 50 for rolling metrics
    summary = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'total_graded': n,
        'all_time': {
            'avg_composite': round(sum(g['composite'] for g in grades) / n, 3),
            'avg_relevance': round(sum(g['relevance'] for g in grades) / n, 3),
            'avg_novelty': round(sum(g['novelty'] for g in grades) / n, 3),
            'avg_echo': round(sum(g['echo'] for g in grades) / n, 3),
            'accept_rate': round(sum(1 for g in grades if g['outcome'] in ('accepted', 'rewarded')) / n, 3),
        },
        'recent_50': {
            'avg_composite': round(sum(g['composite'] for g in recent) / len(recent), 3),
            'avg_relevance': round(sum(g['relevance'] for g in recent) / len(recent), 3),
            'avg_novelty': round(sum(g['novelty'] for g in recent) / len(recent), 3),
            'avg_echo': round(sum(g['echo'] for g in recent) / len(recent), 3),
            'accept_rate': round(sum(1 for g in recent if g['outcome'] in ('accepted', 'rewarded')) / len(recent), 3),
        },
        # What context files appear in accepted vs rejected completions?
        'context_effectiveness': _score_context_effectiveness(grades),
        # What completion lengths get accepted?
        'length_profile': _length_profile(grades),
        # Trending — is it getting better or worse?
        'trend': _compute_trend(grades),
    }
    GRADE_SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return summary


def _score_context_effectiveness(grades: list[dict]) -> dict:
    """Which context files correlate with accepted completions?"""
    file_accepts: Counter = Counter()
    file_rejects: Counter = Counter()
    for g in grades:
        files = g.get('context_files', [])
        if g['outcome'] in ('accepted', 'rewarded'):
            for f in files:
                file_accepts[f] += 1
        elif g['outcome'] in ('dismissed', 'ignored'):
            for f in files:
                file_rejects[f] += 1
    all_files = set(file_accepts) | set(file_rejects)
    effectiveness = {}
    for f in all_files:
        a = file_accepts.get(f, 0)
        r = file_rejects.get(f, 0)
        total = a + r
        if total >= 3:  # minimum sample
            effectiveness[f] = {
                'accept_rate': round(a / total, 2),
                'total': total,
            }
    return effectiveness


def _length_profile(grades: list[dict]) -> dict:
    """What completion lengths get accepted?"""
    accepted_lens = [g['comp_len'] for g in grades if g['outcome'] in ('accepted', 'rewarded')]
    rejected_lens = [g['comp_len'] for g in grades if g['outcome'] in ('dismissed', 'ignored')]
    return {
        'accepted_avg': round(sum(accepted_lens) / len(accepted_lens), 0) if accepted_lens else 0,
        'rejected_avg': round(sum(rejected_lens) / len(rejected_lens), 0) if rejected_lens else 0,
        'accepted_range': [min(accepted_lens, default=0), max(accepted_lens, default=0)],
    }


def _compute_trend(grades: list[dict]) -> dict:
    """Is completion quality trending up or down?"""
    if len(grades) < 20:
        return {'direction': 'insufficient_data', 'delta': 0}
    first_half = grades[:len(grades) // 2]
    second_half = grades[len(grades) // 2:]
    avg_first = sum(g['composite'] for g in first_half) / len(first_half)
    avg_second = sum(g['composite'] for g in second_half) / len(second_half)
    delta = avg_second - avg_first
    if delta > 0.05:
        direction = 'improving'
    elif delta < -0.05:
        direction = 'degrading'
    else:
        direction = 'stable'
    return {'direction': direction, 'delta': round(delta, 3)}


def format_grades_for_prompt(max_entries: int = 5) -> str:
    """Format recent grades for injection into the Gemini prompt.

    This is the SELF-LEARNING signal — tells the model what worked and what didn't.
    """
    if not GRADES_PATH.exists():
        return ''
    lines_raw = GRADES_PATH.read_text('utf-8', errors='ignore').strip().splitlines()
    if not lines_raw:
        return ''
    recent = []
    for line in lines_raw[-max_entries:]:
        try:
            recent.append(json.loads(line))
        except Exception:
            continue
    if not recent:
        return ''

    # Also load summary if available
    summary = None
    if GRADE_SUMMARY_PATH.exists():
        try:
            summary = json.loads(GRADE_SUMMARY_PATH.read_text('utf-8', errors='ignore'))
        except Exception:
            pass

    parts = ['COMPLETION GRADES (self-learning — adapt based on these scores):']
    for g in recent:
        icon = {'rewarded': '\u2b50', 'accepted': '\u2713', 'dismissed': '\u2717',
                'ignored': '\u00b7', 'superseded': '\u21bb'}.get(g['outcome'], '?')
        parts.append(
            f'  {icon} composite={g["composite"]:.2f} '
            f'rel={g["relevance"]:.2f} '
            f'novel={g["novelty"]:.2f} '
            f'echo={g["echo"]:.2f} '
            f'len={g["comp_len"]} '
            f'ctx=[{",".join(g.get("context_files", [])[:2])}]'
        )

    if summary:
        r50 = summary.get('recent_50', {})
        trend = summary.get('trend', {})
        parts.append(
            f'\nPERFORMANCE: accept_rate={r50.get("accept_rate", 0):.0%} '
            f'avg_composite={r50.get("avg_composite", 0):.2f} '
            f'trend={trend.get("direction", "?")}({trend.get("delta", 0):+.3f})'
        )
        lp = summary.get('length_profile', {})
        if lp.get('accepted_avg'):
            parts.append(
                f'ACCEPTED LENGTH: avg={lp["accepted_avg"]:.0f} chars '
                f'(rejected avg={lp.get("rejected_avg", 0):.0f}). '
                f'TARGET your completions to ~{lp["accepted_avg"]:.0f} chars.'
            )
        ce = summary.get('context_effectiveness', {})
        if ce:
            best = sorted(ce.items(), key=lambda x: x[1]['accept_rate'], reverse=True)[:3]
            parts.append(
                f'BEST CONTEXT FILES: {", ".join(f"{f}({d['accept_rate']:.0%})" for f, d in best)}'
            )

    parts.append('IMPROVE: if echo is high, add NEW ideas. if relevance is low, stay on topic. '
                 'if continuation is low, dont repeat the buffer.')
    return '\n'.join(parts)


def compute_adaptive_params() -> dict:
    """Compute adaptive generation parameters from grade history.

    Returns dict with temperature, maxOutputTokens, topP — tuned from
    what actually works for this operator. Falls back to sensible defaults.
    """
    defaults = {'temperature': 0.7, 'maxOutputTokens': 400, 'topP': 0.9}
    if not GRADE_SUMMARY_PATH.exists():
        return defaults
    try:
        summary = json.loads(GRADE_SUMMARY_PATH.read_text('utf-8', errors='ignore'))
    except Exception:
        return defaults

    r50 = summary.get('recent_50', {})
    trend = summary.get('trend', {})
    lp = summary.get('length_profile', {})
    total = summary.get('total_graded', 0)
    if total < 20:
        return defaults

    temp = 0.7
    max_tokens = 400
    top_p = 0.9

    # ── TEMPERATURE: adapt to relevance + accept rate ──
    avg_rel = r50.get('avg_relevance', 0.1)
    accept_rate = r50.get('accept_rate', 0.05)
    avg_echo = r50.get('avg_echo', 0.1)

    if avg_rel < 0.1:
        # completions are off-topic — lower temp to stay focused
        temp = 0.4
    elif avg_rel < 0.2:
        temp = 0.55
    elif avg_rel > 0.3 and avg_echo > 0.3:
        # too much echo, needs creativity
        temp = 0.85
    elif accept_rate > 0.2:
        # working well, keep it steady
        temp = 0.65

    # Trend adjustment
    if trend.get('direction') == 'degrading':
        temp = max(0.3, temp - 0.1)  # getting worse → tighten
    elif trend.get('direction') == 'improving':
        temp = min(0.9, temp + 0.05)  # getting better → don't change much

    # ── MAX TOKENS: match accepted length profile ──
    # Intent amplification needs room — floor is higher for prose completions
    accepted_avg = lp.get('accepted_avg', 0)
    if accepted_avg > 0:
        # tokens ≈ chars/4, give 3x headroom for full intent amplification
        max_tokens = max(200, min(1200, int(accepted_avg / 4 * 3)))
    else:
        max_tokens = 600  # default for amplification
    rejected_avg = lp.get('rejected_avg', 0)
    if rejected_avg > 0 and accepted_avg > 0:
        if rejected_avg > accepted_avg * 2:
            max_tokens = max(200, min(max_tokens, int(accepted_avg / 4 * 2.5)))

    # ── TOP_P: narrow when unfocused ──
    if avg_rel < 0.1:
        top_p = 0.8
    elif accept_rate > 0.15:
        top_p = 0.92

    return {
        'temperature': round(temp, 2),
        'maxOutputTokens': max_tokens,
        'topP': round(top_p, 2),
    }
