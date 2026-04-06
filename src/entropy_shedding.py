"""entropy_shedding — copilot self-reported uncertainty accumulator.

copilot emits entropy markers at end of each response.
this module parses them from ai_responses, accumulates per-module
entropy over time, and builds heat maps for prompt injection.

entropy sources (all self-reported, zero API calls):
  - confidence scores per decision point (0.0-1.0)
  - uncertainty flags on specific modules/functions
  - hedge markers (alternatives considered, caveats stated)
  - rework predictions (will this need fixing?)

the accumulated map = the shedding layer.
copilot sheds uncertainty data like skin. it builds up.
eventually the map tells copilot exactly where it's been wrong before.

the red layer = file-linked entropy math.
every target gets a numeric surface that can be injected back into prompt context.
"""

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


# ─── PARSER ────────────────────────────────────────────────────────
# extracts <!-- entropy:shed --> blocks from copilot responses

SHED_PATTERN = re.compile(
    r'<!-- entropy:shed\s*\n(.*?)\n\s*-->', re.DOTALL
)

MARKER_PATTERN = re.compile(
    r'^([\w./-]+)\s*:\s*([0-9.]+)(?:\s*\|\s*(.+))?$', re.MULTILINE
)


def _parse_single_shed_block(block: str) -> list[dict[str, Any]]:
    markers = []
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        mm = MARKER_PATTERN.match(line)
        if mm:
            markers.append({
                'target': mm.group(1),
                'confidence': float(mm.group(2)),
                'note': (mm.group(3) or '').strip(),
            })
    return markers


def parse_shed_blocks(text):
    markers = []
    for match in SHED_PATTERN.finditer(text):
        markers.extend(_parse_single_shed_block(match.group(1)))
    return markers


def parse_shed_block(text):
    return parse_shed_blocks(text)


# ─── BEHAVIORAL ENTROPY ───────────────────────────────────────────
# compute entropy from copilot's observable behavior in responses

def _response_entropy_signals(response_text):
    text = response_text.lower()
    signals = {}

    # hedge words = uncertainty markers
    hedges = ['i think', 'probably', 'might', 'maybe', 'possibly',
              'not sure', 'unclear', 'i believe', 'it seems',
              'could be', 'likely', 'appears to', 'should work']
    hedge_count = sum(text.count(h) for h in hedges)
    signals['hedge_count'] = hedge_count

    # alternatives offered = decision entropy
    alt_markers = ['alternatively', 'another approach', 'or you could',
                   'option 1', 'option 2', 'on the other hand',
                   'either way', 'you could also']
    signals['alternatives'] = sum(text.count(a) for a in alt_markers)

    # caveats = known unknowns
    caveats = ['caveat', 'warning', 'note:', 'careful', 'be aware',
               'watch out', 'gotcha', 'edge case']
    signals['caveats'] = sum(text.count(c) for c in caveats)

    # question marks in response = copilot unsure
    signals['questions_asked'] = text.count('?')

    # error handling verbosity = defensive coding (high entropy)
    signals['try_except_blocks'] = text.count('try:') + text.count('except')

    # repetition = circling (high entropy)
    words = text.split()
    if len(words) > 20:
        bigrams = [f'{words[i]} {words[i+1]}' for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        repeated = sum(1 for c in bigram_counts.values() if c > 2)
        signals['repetition_score'] = repeated
    else:
        signals['repetition_score'] = 0

    # word count as weight
    signals['word_count'] = len(words)

    # compute composite entropy H (weighted sum normalized 0-1)
    raw = (hedge_count * 2.0 + signals['alternatives'] * 3.0 +
           signals['caveats'] * 1.5 + signals['questions_asked'] * 0.3 +
           signals['repetition_score'] * 1.5)
    # normalize: use sigmoid-like curve so short responses don't spike
    word_len = max(len(words), 1)
    density = raw / word_len
    # sigmoid mapping: density of ~0.1 -> H~0.5
    H = 1.0 / (1.0 + math.exp(-10 * (density - 0.1)))
    signals['entropy_H'] = round(H, 4)

    return signals


# ─── MODULE EXTRACTION ─────────────────────────────────────────────
# figure out which modules a response is about

MODULE_RE = re.compile(r'`([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)`')
FILE_RE = re.compile(r'(?:src|pigeon_compiler|pigeon_brain)/[\w./]+\.py')


def _extract_modules(text):
    modules = set()
    for m in MODULE_RE.finditer(text):
        name = m.group(1)
        if len(name) > 3 and not name.startswith(('True', 'False', 'None')):
            modules.add(name)
    for m in FILE_RE.finditer(text):
        stem = Path(m.group()).stem
        modules.add(stem)
    return modules


# ─── ACCUMULATOR ───────────────────────────────────────────────────

def accumulate_entropy(root):
    root = Path(root)
    responses_path = root / 'logs' / 'ai_responses.jsonl'
    out_path = root / 'logs' / 'entropy_map.json'

    if not responses_path.exists():
        return {'error': 'no ai_responses.jsonl'}

    lines = responses_path.read_text('utf-8', errors='ignore').splitlines()

    per_module = defaultdict(lambda: {
        'total_H': 0.0, 'samples': 0,
        'hedge_total': 0, 'alt_total': 0, 'caveat_total': 0,
        'shed_reports': [],
    })
    global_entropy = []
    shed_count = 0

    for line in lines:
        try:
            entry = json.loads(line)
        except Exception:
            continue

        response = entry.get('response', '')
        ts = entry.get('ts', '')
        prompt = entry.get('prompt', '')

        # behavioral entropy from response text
        signals = _response_entropy_signals(response)
        H = signals['entropy_H']
        global_entropy.append(H)

        # which modules is this about?
        all_text = f'{prompt} {response}'
        modules = _extract_modules(all_text)

        # accumulate per module
        for mod in modules:
            pm = per_module[mod]
            pm['total_H'] += H
            pm['samples'] += 1
            pm['hedge_total'] += signals['hedge_count']
            pm['alt_total'] += signals['alternatives']
            pm['caveat_total'] += signals['caveats']

        # check for explicit shed blocks
        shed_markers = parse_shed_blocks(response)
        if shed_markers:
            shed_count += 1
            for marker in shed_markers:
                target = marker['target']
                per_module[target]['shed_reports'].append({
                    'ts': ts,
                    'confidence': marker['confidence'],
                    'note': marker['note'],
                })

    # compute averages and rank
    module_scores = []
    for mod, data in per_module.items():
        if data['samples'] < 2:
            continue
        avg_H = data['total_H'] / data['samples']
        # entropy from shed blocks (explicit self-reports)
        shed_scores = [s['confidence'] for s in data['shed_reports']]
        avg_shed = sum(shed_scores) / len(shed_scores) if shed_scores else None

        module_scores.append({
            'module': mod,
            'avg_entropy': round(avg_H, 4),
            'samples': data['samples'],
            'hedges': data['hedge_total'],
            'alternatives': data['alt_total'],
            'caveats': data['caveat_total'],
            'shed_avg_confidence': round(avg_shed, 3) if avg_shed is not None else None,
            'shed_count': len(data['shed_reports']),
        })

    module_scores.sort(key=lambda x: -x['avg_entropy'])

    # global stats
    avg_global = sum(global_entropy) / max(len(global_entropy), 1)
    high_entropy_pct = sum(1 for h in global_entropy if h > 0.3) / max(len(global_entropy), 1)

    red_layer = []
    for entry in module_scores:
        shed_conf = entry.get('shed_avg_confidence')
        explicit_uncertainty = (1.0 - float(shed_conf)) if shed_conf is not None else float(entry['avg_entropy'])
        red = round(max(float(entry['avg_entropy']), explicit_uncertainty), 4)
        red_layer.append({
            'module': entry['module'],
            'red': red,
            'avg_entropy': entry['avg_entropy'],
            'shed_avg_confidence': shed_conf,
            'samples': entry['samples'],
            'hedges': entry['hedges'],
            'shed_count': entry['shed_count'],
        })
    red_layer.sort(key=lambda item: (-float(item['red']), -int(item['hedges']), str(item['module'])))

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_responses': len(lines),
        'shed_blocks_found': shed_count,
        'global_avg_entropy': round(avg_global, 4),
        'high_entropy_pct': round(high_entropy_pct * 100, 1),
        'top_entropy_modules': module_scores[:20],
        'red_layer': red_layer[:20],
        'low_entropy_modules': [m for m in module_scores if m['avg_entropy'] < 0.1][-10:],
    }

    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


# ─── PROMPT BLOCK BUILDER ─────────────────────────────────────────

def build_entropy_block(root):
    root = Path(root)
    data = accumulate_entropy(root)
    if 'error' in data:
        return ''

    top_raw = data.get('top_entropy_modules', [])
    top = cast(list[dict[str, Any]], [m for m in top_raw[:8] if isinstance(m, dict)])
    if not top:
        return ''

    lines = [
        '<!-- pigeon:entropy-map -->',
        '## Entropy Shedding Map',
        '',
        f'*{data["total_responses"]} responses analyzed · '
        f'global H={data["global_avg_entropy"]:.3f} · '
        f'{data["high_entropy_pct"]}% high-entropy · '
        f'{data["shed_blocks_found"]} explicit sheds*',
        '',
        '**where copilot is most uncertain (act with extra care):**',
        '',
    ]

    for m in top:
        mod = str(m.get('module', '?'))
        H = float(m.get('avg_entropy', 0.0))
        n = int(m.get('samples', 0))
        hedges = int(m.get('hedges', 0))
        shed_raw = m.get('shed_avg_confidence')
        shed = float(shed_raw) if shed_raw is not None else None
        shed_s = f' shed_conf={shed}' if shed is not None else ''
        lines.append(f'- `{mod}` H={H:.3f} ({n} samples, {hedges} hedges{shed_s})')

    lines.append('')
    lines.append('> emit `<!-- entropy:shed -->` blocks to improve this map.')
    lines.append('<!-- /pigeon:entropy-map -->')
    return '\n'.join(lines)


def build_red_layer_block(root):
    root = Path(root)
    data = accumulate_entropy(root)
    if 'error' in data:
        return ''

    rows_raw = data.get('red_layer', [])
    rows = cast(list[dict[str, Any]], [row for row in rows_raw[:10] if isinstance(row, dict)])
    if not rows:
        return ''

    lines = [
        '<!-- pigeon:entropy-red-layer -->',
        '## Red Layer',
        '',
        '*file-linked entropy math surface*',
        '',
        '`red[module] = max(H_avg, 1 - shed_conf)`',
        '`vec[module] = [red, H_avg, shed_conf?, samples, hedges]`',
        '',
    ]

    for row in rows:
        mod = str(row.get('module', '?'))
        red = float(row.get('red', 0.0))
        H = float(row.get('avg_entropy', 0.0))
        shed_raw = row.get('shed_avg_confidence')
        shed = float(shed_raw) if shed_raw is not None else None
        samples = int(row.get('samples', 0))
        hedges = int(row.get('hedges', 0))
        shed_part = f'{shed:.3f}' if shed is not None else 'null'
        lines.append(f'- `red[{mod}] = [{red:.3f}, {H:.3f}, {shed_part}, {samples}, {hedges}]`')

    lines.append('<!-- /pigeon:entropy-red-layer -->')
    return '\n'.join(lines)


# ─── SHED PROTOCOL ─────────────────────────────────────────────────

SHED_TEMPLATE = """
<!-- entropy:shed
{markers}
-->
"""


def format_shed_block(markers):
    lines = []
    for target, confidence, note in markers:
        note_s = f' | {note}' if note else ''
        lines.append(f'{target}: {confidence:.2f}{note_s}')
    return SHED_TEMPLATE.format(markers='\n'.join(lines)).strip()


if __name__ == '__main__':
    r = accumulate_entropy(Path('.'))
    print(f'responses: {r["total_responses"]}')
    print(f'global entropy: {r["global_avg_entropy"]:.4f}')
    print(f'high entropy: {r["high_entropy_pct"]}%')
    print(f'shed blocks: {r["shed_blocks_found"]}')
    print()
    print('top entropy modules:')
    top_modules = cast(list[dict[str, Any]], r.get('top_entropy_modules', []))
    for m in top_modules[:10]:
        mod = str(m.get('module', '?'))
        avg_entropy = float(m.get('avg_entropy', 0.0))
        samples = int(m.get('samples', 0))
        hedges = int(m.get('hedges', 0))
        print(f'  {mod}: H={avg_entropy:.4f} ({samples} samples, {hedges} hedges)')
