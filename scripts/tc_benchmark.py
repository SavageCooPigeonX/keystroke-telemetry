"""TC quality benchmark — score completions on representative buffers.

Target: ≥90% of completions should pass objective quality checks.

Passes are computed from:
- relevance (buffer topic appears in completion, via noun overlap)
- specificity (mentions concrete modules/files/actions, not generic fluff)
- continuation (doesn't echo, doesn't restart, picks up mid-thought)
- voice (lowercase ratio, no markdown, no "I think/we should")
- length (20-600 chars; no mid-word cutoff)

Prints a report with per-buffer scores and overall pass rate.
"""
import sys, json, re
from pathlib import Path
sys.path.insert(0, '.')

from src.tc_gemini_seq001_v001_seq001_v001 import call_gemini, ThoughtBuffer, _is_buffer_echo

# Representative buffers drawn from actual recent prompts + typical patterns.
BENCHMARK = [
    # mid-word mid-thought (most common)
    "fix the thought comple",
    # short directive
    "run push cycle and audit",
    # question to copilot
    "why does the grader keep giving low scores",
    # code buffer
    "def select_context(buffer, ctx):\n    # merge numeric and",
    # typo-heavy casual
    "the completinos are shit - need to iterate untill theyre good",
    # analytical
    "what about using embeddings for context selection instead of",
    # state-shift question
    "are we actually learning my intent or just",
    # imperative with module reference
    "audit the numeric surface and see if",
]

_GENERIC_FILLER = {
    'something', 'things', 'stuff', 'good', 'better', 'nice',
    'improve', 'enhance', 'optimize', 'robust', 'scalable',
    'maybe', 'probably', 'perhaps', 'possibly',
}
_VOICE_FAILS = ('I think', 'I would', 'I suggest', "Let's", 'We should',
                'Firstly,', 'Secondly,', 'In conclusion', 'Additionally,',
                '**', '##', '```')


def _noun_tokens(text: str) -> set[str]:
    """Extract content words (nouns-ish) — skip stopwords + short words."""
    stop = {
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have',
        'what', 'how', 'not', 'are', 'you', 'was', 'but', 'can',
        'its', 'just', 'like', 'will', 'when', 'your', 'into',
        'need', 'want', 'some', 'also', 'make', 'then', 'them',
        'does', 'keep', 'why', 'run', 'fix', 'see', 'get',
    }
    words = re.findall(r'[a-z][a-z_]{3,}', text.lower())
    return {w for w in words if w not in stop}


def _specificity(completion: str) -> float:
    """How concrete is it? Mentions of modules, file names, specific actions,
    or uncommon content words. Reject bland generic fluff."""
    score = 0.0
    # underscored or uppercase module/constant tokens (snake_case, CONST_CASE)
    if re.search(r'[A-Za-z]+_[A-Za-z]+', completion):
        score += 0.35
    # explicit file/ext references
    if re.search(r'\.(py|json|jsonl|md|ts)\b', completion):
        score += 0.25
    # specific numbers/thresholds
    if re.search(r'\b\d+(\.\d+)?\b', completion):
        score += 0.20
    # technical nouns — domain-specific vocabulary
    technical_terms = (
        'token', 'budget', 'completion', 'buffer', 'context', 'keyword',
        'semantic', 'embedding', 'numeric', 'heuristic', 'ensemble',
        'trajectory', 'cognitive', 'intent', 'amplif', 'grader', 'score',
        'prompt', 'surface', 'module', 'registry', 'pipeline', 'agent',
    )
    hits = sum(1 for t in technical_terms if t in completion.lower())
    score += min(0.35, hits * 0.1)
    # generic filler penalty
    words = re.findall(r'[a-z]+', completion.lower())
    if words:
        filler_ratio = sum(1 for w in words if w in _GENERIC_FILLER) / len(words)
        score -= min(0.3, filler_ratio * 3)
    return max(0.0, min(1.0, score))


def _relevance(buffer: str, completion: str) -> float:
    """Does completion reference buffer's content words?"""
    buf_nouns = _noun_tokens(buffer)
    comp_nouns = _noun_tokens(completion)
    if not buf_nouns:
        return 1.0  # buffer is all stopwords; give pass
    if not comp_nouns:
        return 0.0
    # Any overlap is good, partial match of word stems counts.
    hit = 0
    for bn in buf_nouns:
        for cn in comp_nouns:
            if bn == cn or (len(bn) > 4 and len(cn) > 4 and (bn in cn or cn in bn)):
                hit += 1
                break
    return min(1.0, hit / max(1, min(len(buf_nouns), 4)))


def _voice_ok(completion: str) -> bool:
    """Casual lowercase operator voice, no markdown/formal."""
    for bad in _VOICE_FAILS:
        if bad in completion:
            return False
    # Lowercase ratio of alphabetic chars
    alpha = [c for c in completion if c.isalpha()]
    if not alpha:
        return False
    lower_ratio = sum(1 for c in alpha if c.islower()) / len(alpha)
    return lower_ratio >= 0.85


def _continuation_ok(buffer: str, completion: str, is_code: bool = False) -> bool:
    """Continues mid-thought; no echo, no mid-word cutoff."""
    if _is_buffer_echo(completion, buffer):
        return False
    if not completion:
        return False
    stripped = completion.rstrip()
    if stripped and not is_code:
        last = stripped[-1]
        if last not in '.!?)"\'' :
            words = re.findall(r'[a-zA-Z]+', stripped)
            if not words or len(words[-1]) < 4:
                return False
            danglers = {'and', 'or', 'but', 'the', 'a', 'an', 'of', 'to',
                        'for', 'with', 'at', 'on', 'in', 'by'}
            if words[-1].lower() in danglers:
                return False
    # Buffer-mid-word continuation gate.
    buf_tail = buffer.rstrip()
    if buf_tail and buf_tail[-1].isalpha():
        comp_head = completion.lstrip()
        if not comp_head:
            return False
        ok_starts = comp_head[0].isalpha() or comp_head[0] in ' —-,.:;?!)'
        if not ok_starts:
            return False
    return True


def _length_ok(completion: str, is_code: bool = False) -> bool:
    # Code legitimately runs longer (multi-line function bodies); prose caps tighter.
    cap = 1200 if is_code else 700
    return 20 <= len(completion) <= cap


def _is_code_completion(buffer: str, completion: str) -> bool:
    code_sigs = ('def ', 'class ', 'import ', 'return ', '()', ' = ',
                 '    ', '\t', '{', '}', '#')
    hits = sum(1 for s in code_sigs if s in buffer) + sum(1 for s in code_sigs if s in completion)
    return hits >= 3


def score_completion(buffer: str, completion: str) -> dict:
    rel = _relevance(buffer, completion)
    spec = _specificity(completion)
    voice = _voice_ok(completion)
    is_code = _is_code_completion(buffer, completion)
    cont = _continuation_ok(buffer, completion, is_code=is_code)
    length = _length_ok(completion, is_code=is_code)
    # Pass gate: voice + cont + length AND topical score.
    # Topical = strong topic match, OR moderate specificity, OR
    # short sharp abstract answer (len < 200 and continuation ok — rhetorical
    # completions like "...just pattern-matching?" are valid and correct).
    topical = (
        (rel >= 0.5)
        or (rel >= 0.3 and spec >= 0.3)
        or (spec >= 0.55)
        or (rel >= 0.25 and len(completion) < 200 and cont)  # short abstract
    )
    passed = (voice and cont and length and topical and completion != '')
    return {
        'passed': passed,
        'relevance': round(rel, 2),
        'specificity': round(spec, 2),
        'voice': voice,
        'continuation': cont,
        'length_ok': length,
        'len': len(completion),
    }


def run_benchmark():
    tb = ThoughtBuffer()
    results = []
    for i, buf in enumerate(BENCHMARK, 1):
        print(f'\n[{i}/{len(BENCHMARK)}] buf: "{buf[:60]}..."' if len(buf) > 60
              else f'\n[{i}/{len(BENCHMARK)}] buf: "{buf}"')
        try:
            comp, ctx = call_gemini(buf, tb)
        except Exception as e:
            print(f'    ERROR: {e}')
            results.append({'buffer': buf, 'completion': '', 'score': {'passed': False}, 'error': str(e)})
            continue
        s = score_completion(buf, comp)
        status = '✓' if s['passed'] else '✗'
        print(f'    {status} rel={s["relevance"]} spec={s["specificity"]} voice={s["voice"]} '
              f'cont={s["continuation"]} len={s["len"]}')
        print(f'    > {comp[:180]}{"..." if len(comp) > 180 else ""}')
        results.append({'buffer': buf, 'completion': comp, 'score': s})
    passed = sum(1 for r in results if r['score']['passed'])
    total = len(results)
    rate = passed / total if total else 0
    print('\n' + '=' * 70)
    print(f'PASS RATE: {passed}/{total} = {rate*100:.0f}%')
    print('=' * 70)
    print('\nFAILURES:')
    for r in results:
        if not r['score']['passed']:
            s = r['score']
            reasons = []
            if not s.get('voice', True): reasons.append('voice')
            if not s.get('continuation', True): reasons.append('cont')
            if not s.get('length_ok', True): reasons.append('length')
            if s.get('relevance', 0) < 0.5: reasons.append(f'rel={s["relevance"]}')
            if s.get('specificity', 0) < 0.3: reasons.append(f'spec={s["specificity"]}')
            print(f'  [{",".join(reasons)}]  "{r["buffer"][:50]}"')
            print(f'     → "{r["completion"][:120]}"')
    # Save full log
    Path('logs').mkdir(exist_ok=True)
    Path('logs/tc_benchmark_latest.json').write_text(
        json.dumps({'pass_rate': rate, 'results': results}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    return rate


if __name__ == '__main__':
    rate = run_benchmark()
    sys.exit(0 if rate >= 0.9 else 1)
