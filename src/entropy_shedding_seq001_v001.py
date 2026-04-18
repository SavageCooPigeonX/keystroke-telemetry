"""entropy_shedding_seq001_v001 — copilot self-reported uncertainty accumulator.

copilot emits entropy markers at end of each response.
this module parses them from ai_responses, accumulates per-module
entropy over time, and builds heat maps for prompt injection.

entropy sources (zero API calls):
  - confidence scores per decision point (0.0-1.0)
  - uncertainty flags on specific modules/functions
  - hedge markers (alternatives considered, caveats stated)
  - rework predictions (will this need fixing?)
  - edit_pairs.jsonl latency/state data (real prompt→file touch ground truth)

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

EDIT_STATE_ENTROPY = {
    'focused': 0.05,
    'neutral': 0.08,
    'restructuring': 0.18,
    'abandoned': 0.24,
    'hesitant': 0.28,
    'frustrated': 0.32,
    'confused': 0.30,
    'unknown': 0.12,
}


def _module_key(raw_name: str) -> str:
    """Canonicalize a file-ish name into a stable module key."""
    name = _normalize_target(raw_name)
    if name.endswith(('.json', '.jsonl', '.md', '.txt')):
        return name
    stem = Path(name).stem
    mod = re.split(r'_s(?:eq)?\d{3}', stem)[0]
    return mod or stem


def _extract_modules(text):
    modules = set()
    for m in MODULE_RE.finditer(text):
        name = _normalize_target(m.group(1))
        if len(name) > 3 and not name.startswith(('True', 'False', 'None')):
            modules.add(name)
    for m in FILE_RE.finditer(text):
        modules.add(_module_key(m.group()))
    return modules


def _normalize_target(name: str) -> str:
    """Normalize shed block target names to match module extraction.

    Strips .py suffix, path prefixes, backslashes, and whitespace so that shed
    targets like 'escalation_engine_seq001_v001.py' or 'src/foo.py' merge with behavioral
    and edit-pair entries for 'escalation_engine_seq001_v001' or 'foo'.
    """
    name = name.strip().replace('\\', '/')
    if '/' in name:
        name = name.rsplit('/', 1)[-1]
    if name.endswith('.py'):
        name = name[:-3]
    return name


def _load_edit_entropy(root: Path) -> dict[str, dict[str, float]]:
    """Turn edit_pairs.jsonl into per-module entropy signals.

    This is the missing ground-truth bridge: real prompt→file touches with
    latency and operator state become uncertainty measurements even when the
    module is never named in an AI response.
    """
    ep = root / 'logs' / 'edit_pairs.jsonl'
    if not ep.exists():
        return {}

    per_module: dict[str, dict[str, float]] = defaultdict(lambda: {
        'total_H': 0.0,
        'samples': 0.0,
        'latency_total': 0.0,
    })

    for line in ep.read_text('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue

        raw_file = entry.get('file', '')
        if not raw_file:
            continue

        mod = _module_key(raw_file)
        latency_ms = max(0, int(entry.get('latency_ms', 0) or 0))
        state = str(entry.get('state') or 'unknown').strip().lower()
        edit_why = str(entry.get('edit_why') or '').strip().lower()

        latency_score = min(latency_ms / 300000.0, 1.0)  # 5 min = max uncertainty
        state_score = EDIT_STATE_ENTROPY.get(state, EDIT_STATE_ENTROPY['unknown'])
        # clear edit reason = LESS uncertain (reduces entropy)
        reason_bonus = -0.15 if edit_why and edit_why not in {'auto', 'none'} else 0.0
        event_H = max(0.0, min(1.0, latency_score * 0.55 + state_score * 0.35 + reason_bonus))

        pm = per_module[mod]
        pm['total_H'] += event_H
        pm['samples'] += 1
        pm['latency_total'] += latency_ms

    return per_module


def _load_direct_sheds(root: Path) -> list[dict]:
    """Load direct shed records from entropy_sheds.jsonl.
    
    This is the real-time feed: sheds recorded directly during session
    without waiting for ai_responses harvest.
    """
    sheds_path = root / 'logs' / 'entropy_sheds.jsonl'
    if not sheds_path.exists():
        return []
    
    sheds = []
    for line in sheds_path.read_text('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            sheds.append(entry)
        except Exception:
            continue
    return sheds


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
        'edit_total_H': 0.0, 'edit_samples': 0, 'latency_total': 0.0,
        'hedge_total': 0, 'alt_total': 0, 'caveat_total': 0,
        'shed_reports': [],
    })
    global_entropy = []
    shed_count = 0
    edit_entropy = _load_edit_entropy(root)

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
                target = _normalize_target(marker['target'])
                per_module[target]['shed_reports'].append({
                    'ts': ts,
                    'confidence': marker['confidence'],
                    'note': marker['note'],
                })

    # Merge in edit-pair-derived entropy so touched files show up even if never named.
    for mod, ed in edit_entropy.items():
        pm = per_module[mod]
        pm['edit_total_H'] += ed['total_H']
        pm['edit_samples'] += int(ed['samples'])
        pm['latency_total'] += ed['latency_total']

    # Merge in direct sheds (real-time feed from session)
    direct_sheds = _load_direct_sheds(root)
    for shed in direct_sheds:
        target = _normalize_target(shed.get('module', ''))
        if target:
            per_module[target]['shed_reports'].append({
                'ts': shed.get('ts', ''),
                'confidence': shed.get('confidence', 0.5),
                'note': shed.get('note', ''),
            })
            shed_count += 1

    # compute averages and rank
    module_scores = []
    for mod, data in per_module.items():
        has_sheds = len(data['shed_reports']) > 0
        total_samples = int(data['samples']) + int(data['edit_samples'])
        # include if ≥2 combined samples OR has explicit shed data
        if total_samples < 2 and not has_sheds:
            continue
        avg_H = (data['total_H'] + data['edit_total_H']) / max(total_samples, 1)
        avg_edit_H = data['edit_total_H'] / max(int(data['edit_samples']), 1) if data['edit_samples'] else None
        avg_latency = data['latency_total'] / max(int(data['edit_samples']), 1) if data['edit_samples'] else None
        # entropy from shed blocks (explicit self-reports)
        shed_scores = [s['confidence'] for s in data['shed_reports']]
        avg_shed = sum(shed_scores) / len(shed_scores) if shed_scores else None

        module_scores.append({
            'module': mod,
            'avg_entropy': round(avg_H, 4),
            'samples': total_samples,
            'behavioral_samples': int(data['samples']),
            'edit_samples': int(data['edit_samples']),
            'avg_edit_entropy': round(avg_edit_H, 4) if avg_edit_H is not None else None,
            'avg_latency_ms': round(avg_latency, 1) if avg_latency is not None else None,
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

    # rework penalties — misses inflate entropy for involved modules
    rework_penalties = _read_rework_penalties(root)

    red_layer = []
    for entry in module_scores:
        shed_conf = entry.get('shed_avg_confidence')
        rework_penalty = rework_penalties.get(entry['module'], 0.0)
        if shed_conf is not None:
            # shed confidence OVERRIDES edit-pair entropy — that's the whole point
            # blend: 70% shed signal, 30% measured entropy (shed is intentional)
            explicit_uncertainty = 1.0 - float(shed_conf)
            red = round(0.7 * explicit_uncertainty + 0.3 * float(entry['avg_entropy']) + rework_penalty, 4)
        else:
            red = round(float(entry['avg_entropy']) + rework_penalty, 4)
        red_layer.append({
            'module': entry['module'],
            'red': red,
            'avg_entropy': entry['avg_entropy'],
            'shed_avg_confidence': shed_conf,
            'samples': entry['samples'],
            'hedges': entry['hedges'],
            'shed_count': entry['shed_count'],
            'rework_penalty': round(rework_penalty, 3) if rework_penalty > 0 else None,
        })
    red_layer.sort(key=lambda item: (-float(item['red']), -int(item['hedges']), str(item['module'])))

    # recently shed modules (from direct sheds) — always include regardless of red score
    recently_shed_modules = set(s.get('module', '') for s in direct_sheds)
    recently_shed = [r for r in red_layer if r['module'] in recently_shed_modules]

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_responses': len(lines),
        'shed_blocks_found': shed_count,
        'direct_sheds_merged': len(direct_sheds),
        'tracked_modules': len(module_scores),
        'edit_pair_modules': sum(1 for m in module_scores if m.get('edit_samples', 0) > 0),
        'global_avg_entropy': round(avg_global, 4),
        'high_entropy_pct': round(high_entropy_pct * 100, 1),
        'top_entropy_modules': module_scores[:20],
        'red_layer': red_layer[:20],
        'recently_shed': recently_shed,
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

    # show recently shed modules (from direct feed this session)
    recently_shed = cast(list[dict[str, Any]], data.get('recently_shed', []))
    if recently_shed:
        lines.append('')
        lines.append('**recently shed (this session):**')
        for r in recently_shed[:5]:
            mod = str(r.get('module', '?'))
            red = float(r.get('red', 0.0))
            conf = r.get('shed_avg_confidence')
            conf_s = f'{conf:.2f}' if conf is not None else '?'
            lines.append(f'- `{mod}` red={red:.3f} conf={conf_s}')

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


# ─── REWORK → ENTROPY BRIDGE ──────────────────────────────────────
# when AI responses get reworked, the modules involved become less certain

def _read_rework_penalties(root: Path) -> dict[str, float]:
    """Read rework_log.json → per-module entropy penalties.

    Each 'miss' verdict adds +0.05 entropy to referenced modules.
    Each 'partial' adds +0.02. Capped at +0.20 per module.
    """
    rework_path = root / 'rework_log.json'
    if not rework_path.exists():
        return {}
    try:
        events = json.loads(rework_path.read_text('utf-8'))
    except Exception:
        return {}
    penalties: dict[str, float] = {}
    deltas = {'miss': 0.05, 'partial': 0.02}
    for ev in events:
        verdict = ev.get('verdict', 'ok')
        delta = deltas.get(verdict, 0)
        if delta == 0:
            continue
        # extract modules from query + response hints
        text = f"{ev.get('query_hint', '')} {ev.get('response_hint', '')}"
        modules = _extract_modules(text)
        for mod in modules:
            penalties[mod] = min(0.20, penalties.get(mod, 0) + delta)
    return penalties


# ─── ENTROPY-DRIVEN DEVELOPMENT ───────────────────────────────────
# weaponized entropy: steer development toward highest uncertainty

def get_high_entropy_targets(root, threshold=0.30, limit=10):
    """Return modules with entropy above threshold, sorted by red score.

    Used by self-fix, learning loop, and prompt injection to prioritize
    which files deserve the most scrutiny and development attention.
    """
    root = Path(root)
    map_path = root / 'logs' / 'entropy_map.json'
    if not map_path.exists():
        return []
    try:
        data = json.loads(map_path.read_text('utf-8'))
    except Exception:
        return []
    red_layer = data.get('red_layer', [])
    targets = []
    for entry in red_layer:
        red = float(entry.get('red', 0.0))
        if red >= threshold:
            targets.append({
                'module': entry['module'],
                'red': red,
                'avg_entropy': float(entry.get('avg_entropy', 0.0)),
                'shed_avg_confidence': entry.get('shed_avg_confidence'),
                'samples': int(entry.get('samples', 0)),
                'confidence_goal': round(max(0.85, 1.0 - red + 0.15), 2),
            })
    targets.sort(key=lambda x: -x['red'])
    return targets[:limit]


def build_entropy_directive(root):
    """Build actionable entropy directive for prompt injection.

    Instead of passive 'here are entropy scores', this tells Copilot:
    - WHICH files need uncertainty reduced
    - WHAT the confidence goal is for each file
    - HOW to shed entropy (specific actions)
    """
    targets = get_high_entropy_targets(root)
    if not targets:
        return ''
    root = Path(root)
    data_path = root / 'logs' / 'entropy_map.json'
    try:
        data = json.loads(data_path.read_text('utf-8'))
    except Exception:
        data = {}
    total = data.get('total_responses', 0)
    global_h = data.get('global_avg_entropy', 0.0)
    sheds = data.get('shed_blocks_found', 0)

    lines = [
        '## Entropy Development Priorities',
        '',
        f'*{total} responses · global H={global_h:.3f} · {sheds} sheds*',
        '',
        '**These modules have the highest uncertainty. When touching them:**',
        '- Read the full source BEFORE editing (don\'t guess)',
        '- Shed entropy with a confidence score AFTER every edit',
        '- If confidence < goal, explain what remains uncertain',
        '',
    ]
    for t in targets:
        mod = t['module']
        red = t['red']
        goal = t['confidence_goal']
        shed = t.get('shed_avg_confidence')
        current = f', last shed={shed}' if shed is not None else ''
        lines.append(f'- `{mod}` red={red:.3f} → **goal: conf≥{goal}**{current}')
    lines.append('')
    return '\n'.join(lines)


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
