"""operator_probes — synthesize questions copilot should ask the operator.

Reads all live signals (cognitive state, unsaid threads, escalation, file
personas, hot modules, open bugs) AND intent predictions (1wk/1mo/3mo forward
projections) to generate 2-4 targeted probes.

The loop: push → predict → probe → operator answers → tune intent → predict again.
Prediction-driven probes are highest priority — they validate/invalidate the
forward model, making every conversation a calibration event.

These get injected into copilot-instructions.md so the LLM asks the operator
instead of waiting to be asked.
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone


def _load_json(p: Path) -> dict | list:
    try:
        return json.loads(p.read_text('utf-8'))
    except Exception:
        return {}


def _load_predictions(root: Path) -> dict:
    """Load intent projections. Tries intent_projection.json first,
    falls back to parsing INTENT_SIMULATION.md."""
    proj = root / 'logs' / 'intent_projection.json'
    if proj.exists():
        return _load_json(proj)
    # fallback: parse the markdown report
    md = root / 'docs' / 'INTENT_SIMULATION.md'
    if not md.exists():
        return {}
    text = md.read_text('utf-8')
    result = {'projection': {}, 'trajectory': {}, 'patterns': {}}
    # extract trajectory
    dom = re.search(r'\*\*Dominant:\s*`([^`]+)`', text)
    if dom:
        result['trajectory']['dominant'] = dom.group(1)
    emg = re.search(r'\*\*emerging:\*\*\s*(.+)', text)
    if emg:
        result['trajectory']['emerging'] = [
            s.strip().strip('`') for s in emg.group(1).split(',')]
    dec = re.search(r'\*\*declining:\*\*\s*(.+)', text)
    if dec:
        result['trajectory']['declining'] = [
            s.strip().strip('`') for s in dec.group(1).split(',')]
    # extract projections
    for horizon, key in [('1 Week', 'week'), ('1 Month', 'month'), ('3 Months', 'quarter')]:
        block = re.search(
            rf'### {re.escape(horizon)}.*?\n(.*?)(?=###|\Z)', text, re.DOTALL)
        if not block:
            continue
        chunk = block.group(1)
        p = {}
        conf = re.search(r'confidence:\s*(\w+)', chunk)
        if conf:
            p['confidence'] = conf.group(1)
        pri = re.search(r'primary:\s*`([^`]+)`', chunk)
        if pri:
            p['primary_intent'] = pri.group(1)
        sec = re.search(r'secondary:\s*`([^`]+)`', chunk)
        if sec:
            p['secondary_intent'] = sec.group(1)
        risk = re.search(r'risk of abandonment:\*\*\s*`([^`]+)`', chunk)
        if risk:
            p['abandoned_risk'] = risk.group(1)
        themes = re.findall(r'from deleted words:\*\*\s*(.+)', chunk)
        if themes:
            p['emerging_themes'] = [
                s.strip().strip('`') for s in themes[0].split(',')]
        mods = re.findall(r'predicted module focus:\s*(.+)', chunk)
        if mods:
            p['module_prediction'] = [
                s.strip().strip('`') for s in mods[0].split(',')]
        result['projection'][key] = p
    # extract deleted themes
    arch = re.search(r'Deleted Thought Archaeology.*?\n(.*?)(?=##|\Z)', text, re.DOTALL)
    if arch:
        result['patterns']['deleted_themes'] = re.findall(
            r'"([^"]+)"', arch.group(1))
    return result


def _prediction_probes(predictions: dict) -> list[str]:
    """Generate probes from forward projections. Highest priority source."""
    probes = []
    proj = predictions.get('projection', {})
    traj = predictions.get('trajectory', {})
    patterns = predictions.get('patterns', {})

    # 3-month probe — validate long-range intent
    q = proj.get('quarter', {})
    themes = q.get('emerging_themes', [])
    q_focus = q.get('primary_intent', '')
    q_mods = q.get('module_prediction', [])
    if themes:
        theme_str = ', '.join(f'"{t}"' for t in themes[:3])
        probes.append(
            f'Your deleted words predict these themes in 3 months: {theme_str}. '
            f'Are any of these actually where you\'re headed — or has your thinking shifted?'
        )
    elif q_mods:
        mod_str = ', '.join(f'`{m}`' for m in q_mods[:3])
        probes.append(
            f'3-month projection puts focus on {mod_str}. '
            f'Is that still the plan or are you pivoting?'
        )

    # 1-month abandonment risk
    m = proj.get('month', {})
    risk = m.get('abandoned_risk')
    if risk:
        probes.append(
            f'`{risk}` is trending toward abandonment. '
            f'Intentional deprioritization or just hasn\'t come up yet?'
        )

    # intent trajectory divergence — emerging vs dominant
    emerging = traj.get('emerging', [])
    dominant = traj.get('dominant', '')
    if emerging and emerging[0] != dominant:
        probes.append(
            f'`{emerging[0]}` is emerging while `{dominant}` dominates. '
            f'Are you context-switching or is {emerging[0]} becoming the main thread?'
        )

    # deleted thought archaeology — unsaid intent
    del_themes = patterns.get('deleted_themes', [])
    long_del = [t for t in del_themes if len(t) > 8]
    if long_del and not themes:
        probes.append(
            f'You\'ve deleted "{long_del[0]}" from prompts before. '
            f'Is this something you want to build but haven\'t committed to yet?'
        )

    return probes[:2]  # cap prediction probes at 2


def _synthesize_probes(root: Path) -> list[str]:
    """Generate 2-4 probes from live signals. Zero LLM calls.
    Prediction-driven probes come FIRST — they close the loop."""
    probes = []

    # === PREDICTION PROBES (highest priority) ===
    predictions = _load_predictions(root)
    probes.extend(_prediction_probes(predictions))

    # === SIGNAL-DRIVEN PROBES ===
    telem = _load_json(root / 'logs' / 'prompt_telemetry_latest.json')

    # 1. Unsaid threads — operator deleted words are design decisions
    if len(probes) < 4:
        deleted = telem.get('deleted_words', [])
        if deleted:
            longest = max(deleted, key=len) if deleted else ''
            if len(longest) > 4:
                probes.append(
                    f'You deleted "{longest}" while typing. What were you about to ask? '
                    f'Deleted words are design decisions — say it out loud.'
                )

    # 2. Escalation — modules at level 2+ need operator decision
    if len(probes) < 4:
        esc = _load_json(root / 'logs' / 'escalation_state.json')
        if isinstance(esc, dict):
            critical = [(k, v) for k, v in esc.items()
                        if isinstance(v, dict) and v.get('level', 0) >= 2]
            if critical:
                mod, state = critical[0]
                probes.append(
                    f'`{mod}` has been escalating for {state.get("passes_ignored", 0)} passes '
                    f'({state.get("bug_type", "unknown")} bug). '
                    f'Should I fix it autonomously or do you have a different plan for this module?'
                )

    # 3. Hot modules — high cognitive load means operator struggles
    if len(probes) < 4:
        hot = telem.get('hot_modules', [])
        if hot:
            top = hot[0]
            if top.get('hes', 0) > 0.6:
                probes.append(
                    f'You hesitate most around `{top["module"]}` (hes={top["hes"]:.2f}). '
                    f'What about this module is unclear — the API, the architecture, or something else?'
                )

    # 4. Persona memory — open tasks from file conversations
    if len(probes) < 4:
        intents_path = root / 'logs' / 'persona_intents_latest.json'
        if intents_path.exists():
            intents = _load_json(intents_path)
            tasks = intents.get('open_tasks', [])
            if tasks:
                t = tasks[0]
                probes.append(
                    f'From your chat with `{t["module"]}`: "{t["task"]}". '
                    f'Is this still a priority or has your thinking changed?'
                )

    # 5. Cognitive state — frustrated operator gets direct question
    if len(probes) < 4:
        latest = telem.get('latest_prompt', {})
        state = latest.get('state', '')
        if state == 'frustrated' and not any('frustrat' in p.lower() for p in probes):
            probes.append(
                'You seem frustrated. What specifically broke or isn\'t working? '
                'Be blunt — I\'ll match your energy.'
            )

    # 6. Stale focus — no module refs in recent prompts
    if len(probes) < 4:
        latest = telem.get('latest_prompt', {})
        refs = latest.get('module_refs', [])
        if not refs and len(probes) < 3:
            probes.append(
                'You haven\'t named a specific module recently. '
                'What are you actually trying to build or fix right now?'
            )

    return probes[:4]  # cap at 4


def build_probe_block(root: Path) -> str:
    """Build the managed prompt block with operator probes."""
    probes = _synthesize_probes(root)
    if not probes:
        return ''

    lines = [
        '<!-- pigeon:operator-probes -->',
        '## Operator Probes',
        '',
        f'*Auto-generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC '
        f'· {len(probes)} probe(s) from live signals*',
        '',
        '**ASK these questions naturally in your next response '
        '(pick 1-2, weave into context):**',
        '',
    ]
    for i, probe in enumerate(probes, 1):
        lines.append(f'{i}. {probe}')
    lines.append('')
    lines.append('*Probes are generated from: intent predictions (1wk/1mo/3mo), '
                 'unsaid threads, escalation state, cognitive heat, persona memory, '
                 'and operator state.*')
    lines.append('<!-- /pigeon:operator-probes -->')
    return '\n'.join(lines)


def inject_probes(root: Path) -> bool:
    """Inject/update the operator-probes block in copilot-instructions.md."""
    ci_path = root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return False
    content = ci_path.read_text('utf-8')
    block = build_probe_block(root)
    if not block:
        return False

    start = '<!-- pigeon:operator-probes -->'
    end = '<!-- /pigeon:operator-probes -->'

    if start in content:
        before = content[:content.index(start)]
        after = content[content.index(end) + len(end):]
        content = before + block + after
    else:
        # Insert before engagement hooks or auto-index
        for anchor in ['<!-- pigeon:hooks -->', '<!-- pigeon:auto-index -->']:
            if anchor in content:
                idx = content.index(anchor)
                content = content[:idx] + block + '\n' + content[idx:]
                break
        else:
            content += '\n' + block + '\n'

    ci_path.write_text(content, 'utf-8')
    return True
