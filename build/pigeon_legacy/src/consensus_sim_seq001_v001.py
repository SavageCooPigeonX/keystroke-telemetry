"""consensus_sim_seq001_v001.py — multi-file consensus debugging via the organism chat server.

Picks a chronic bug, selects relevant modules, has each one diagnose the problem
in character, synthesizes a consensus verdict, then drops into interactive mode
where the operator can talk to any file.

Usage:
    py src/consensus_sim_seq001_v001.py                     # auto-pick worst chronic bug
    py src/consensus_sim_seq001_v001.py --bug overcap       # target specific bug type
    py src/consensus_sim_seq001_v001.py --modules a,b,c     # override module selection
    py src/consensus_sim_seq001_v001.py --interactive-only   # skip consensus, go straight to chat

Loop: pick bug → context-select relevant modules → each file speaks →
      consensus → interactive operator chat → per-file follow-ups
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = 'http://localhost:8234'
DELAY = 6  # seconds between Gemini calls to avoid 503


# ── data loading ──

def _load_bug_profiles_seq001_v001() -> dict:
    """Load chronic bug data from BUG_PROFILES.md + copilot-instructions."""
    bugs = {}
    # Parse overcap data from copilot-instructions auto-index
    ci = ROOT / '.github' / 'copilot-instructions.md'
    if ci.exists():
        text = ci.read_text('utf-8', errors='ignore')
        # Extract overcap modules from bug-voices section
        import re
        for m in re.finditer(r'`(\S+?)` — \[(\w+)\] (\d+)/\d+ reports\. chronic', text):
            mod, bug_type, count = m.group(1), m.group(2), int(m.group(3))
            bugs.setdefault(bug_type, []).append({'module': mod, 'reports': count})
    # Also check organism-health for over-cap
    bp = ROOT / 'docs' / 'BUG_PROFILES.md'
    if bp.exists():
        text = bp.read_text('utf-8', errors='ignore')
        import re
        for m in re.finditer(r'`(\S+?)` came in wheezing at (\d+) tokens.*?(\d+)% over', text):
            mod, tokens, pct = m.group(1), int(m.group(2)), int(m.group(3))
            bugs.setdefault('overcap', []).append({
                'module': mod, 'tokens': tokens, 'pct_over': pct,
            })
    return bugs


def _load_identities_fast() -> dict:
    """Quick load — get module names from the server."""
    try:
        resp = urllib.request.urlopen(f'{SERVER}/state', timeout=10)
        return json.loads(resp.read())
    except Exception:
        return {}


def _chat(module: str, message: str, history: list | None = None) -> dict:
    """Send a chat message to a module via the organism server."""
    payload = {'module': module, 'message': message}
    if history:
        payload['history'] = history
    try:
        req = urllib.request.Request(
            f'{SERVER}/chat',
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=90)
        return json.loads(resp.read())
    except Exception as e:
        return {'response': f'[error: {e}]', 'extractions': []}


def _get_available_modules() -> list[str]:
    """Get list of all module names the server knows about."""
    try:
        sys.path.insert(0, str(ROOT))
        from src.module_identity_seq001_v001 import build_identities
        ids = build_identities(ROOT, include_consciousness=False)
        return [i['name'] for i in ids]
    except Exception:
        return []


# ── context selection ──

def _select_modules_for_bug(bug_type: str, bug_data: list[dict],
                            all_modules: list[str]) -> list[str]:
    """Pick modules relevant to a bug — the affected ones + modules that could fix it."""
    selected = []
    # Affected modules (up to 5 worst)
    if bug_type == 'overcap':
        bug_data.sort(key=lambda x: -x.get('tokens', 0))
    elif bug_type == 'hardcoded_import':
        bug_data.sort(key=lambda x: -x.get('reports', 0))
    affected = [b['module'] for b in bug_data[:5]]

    # Map pigeon short names to full identity names
    for short in affected:
        for full in all_modules:
            if short == full or short in full:
                if full not in selected:
                    selected.append(full)
                    break

    # Add fixer/diagnostic modules
    fixer_keywords = {
        'overcap': ['self_fix', 'compliance', 'resplit', 'run_clean_split'],
        'hardcoded_import': ['import_rewriter', 'self_fix', 'compliance', 'import_fixer'],
        'dead_export': ['self_fix', 'compliance', 'context_veins_seq001_v001'],
    }
    for kw in fixer_keywords.get(bug_type, ['self_fix']):
        for full in all_modules:
            if kw in full and full not in selected:
                selected.append(full)
                break

    return selected[:8]


# ── consensus engine ──

def _build_bug_briefing(bug_type: str, bug_data: list[dict]) -> str:
    """Build a debug briefing prompt for the bug."""
    if bug_type == 'overcap':
        victims = ', '.join(f"`{b['module']}` ({b['tokens']}tok, {b['pct_over']}% over)"
                           for b in bug_data[:5])
        return (
            f"ORGANISM EMERGENCY: the Overcap Maw is eating us alive. "
            f"These modules are bloated past the 2000-token hard cap: {victims}. "
            f"This is chronic — it shows up in every self-fix report and never dies. "
            f"As a file in this codebase, diagnose WHY this keeps happening. "
            f"What's YOUR role in this? Are you part of the problem or part of the solution? "
            f"What specific function of yours contributes to bloat or could help fix it? "
            f"Be brutally honest. Name names. Tag your diagnosis: [CAUSE], [FIX], [BLOCKER]."
        )
    elif bug_type == 'hardcoded_import':
        victims = ', '.join(f"`{b['module']}` ({b['reports']} reports)"
                           for b in bug_data[:5])
        return (
            f"CHRONIC BUG ALERT: hardcoded_import keeps coming back. "
            f"Worst offenders: {victims}. This has been flagged in 70%+ of self-fix reports. "
            f"Every time it gets 'fixed' it comes right back next push. "
            f"What do YOU know about why this never stays fixed? "
            f"Are any of YOUR imports hardcoded? Do you import from pigeon_brain directly? "
            f"Tag: [CAUSE], [FIX], [BLOCKER]."
        )
    else:
        return (
            f"Bug type `{bug_type}` keeps recurring. "
            f"What do you know about it? How are you involved? "
            f"Tag: [CAUSE], [FIX], [BLOCKER]."
        )


def _synthesize_consensus(responses: list[dict]) -> str:
    """Aggregate all file responses into a consensus verdict."""
    causes, fixes, blockers = [], [], []
    for r in responses:
        for ext in r.get('extractions', []):
            tag, text = ext['tag'], ext['text']
            if tag == 'CAUSE':
                causes.append(f"{r['module']}: {text}")
            elif tag == 'FIX':
                fixes.append(f"{r['module']}: {text}")
            elif tag == 'BLOCKER':
                blockers.append(f"{r['module']}: {text}")

    lines = ['╔══ CONSENSUS VERDICT ══╗', '']
    if causes:
        lines.append(f'CAUSES ({len(causes)} identified):')
        for c in causes:
            lines.append(f'  → {c}')
        lines.append('')
    if fixes:
        lines.append(f'PROPOSED FIXES ({len(fixes)}):')
        for f in fixes:
            lines.append(f'  ✓ {f}')
        lines.append('')
    if blockers:
        lines.append(f'BLOCKERS ({len(blockers)}):')
        for b in blockers:
            lines.append(f'  ✗ {b}')
        lines.append('')

    # Vote counting — which fix was mentioned most
    if fixes:
        lines.append('STRONGEST SIGNAL:')
        lines.append(f'  {fixes[0]}')

    lines.append('')
    lines.append(f'Files consulted: {len(responses)}')
    lines.append(f'Total diagnoses: {len(causes)} causes, {len(fixes)} fixes, {len(blockers)} blockers')
    lines.append('╚═══════════════════════╝')
    return '\n'.join(lines)


# ── function selector ──

def _select_functions(module: str, all_modules: list[str]) -> list[dict]:
    """Context-select: find the module's functions from identity data."""
    try:
        sys.path.insert(0, str(ROOT))
        from src.module_identity_seq001_v001 import build_identities
        ids = build_identities(ROOT, include_consciousness=False)
        by_name = {i['name']: i for i in ids}
        ident = by_name.get(module, {})
        fns = ident.get('code', {}).get('functions', [])
        return fns
    except Exception:
        return []


# ── interactive mode ──

def _interactive_loop(modules: list[str], histories: dict[str, list]):
    """Drop into interactive chat with any of the selected modules."""
    print('\n╔══ INTERACTIVE MODE ══╗')
    print(f'Talk to any of these files: {", ".join(modules)}')
    print('Commands:')
    print('  /list          — show available modules')
    print('  /fns <module>  — show functions in a module (context select)')
    print('  /to <module>   — switch who you\'re talking to')
    print('  /all <msg>     — broadcast message to ALL modules')
    print('  /consensus     — re-run consensus from current conversation')
    print('  /quit          — exit')
    print('╚═════════════════════╝\n')

    current = modules[0] if modules else ''
    all_mods = _get_available_modules()

    while True:
        try:
            prompt = input(f'[you → {current}] > ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n[exiting]')
            break

        if not prompt:
            continue

        if prompt == '/quit':
            break

        if prompt == '/list':
            for i, m in enumerate(modules):
                marker = ' ←' if m == current else ''
                print(f'  {i+1}. {m}{marker}')
            continue

        if prompt.startswith('/fns'):
            parts = prompt.split(maxsplit=1)
            target = parts[1].strip() if len(parts) > 1 else current
            # Find matching module
            match = None
            for m in modules + all_mods:
                if target == m or target in m:
                    match = m
                    break
            if not match:
                print(f'  [module "{target}" not found]')
                continue
            fns = _select_functions(match, all_mods)
            if fns:
                print(f'\n  Functions in {match}:')
                for f in fns:
                    vis = '🔓' if not f['name'].startswith('_') else '🔒'
                    print(f'    {vis} {f["name"]}()')
                print()
            else:
                print(f'  [no functions found for {match}]')
            continue

        if prompt.startswith('/to'):
            parts = prompt.split(maxsplit=1)
            if len(parts) < 2:
                print('  usage: /to <module_name>')
                continue
            target = parts[1].strip()
            match = None
            for m in modules:
                if target == m or target in m:
                    match = m
                    break
            # Also allow switching to any module in the codebase
            if not match:
                for m in all_mods:
                    if target == m or target in m:
                        match = m
                        if match not in modules:
                            modules.append(match)
                            histories.setdefault(match, [])
                            print(f'  [added {match} to panel]')
                        break
            if match:
                current = match
                print(f'  [now talking to {current}]')
            else:
                print(f'  [module "{target}" not found]')
            continue

        if prompt.startswith('/all'):
            msg = prompt[4:].strip()
            if not msg:
                print('  usage: /all <message>')
                continue
            print(f'\n  Broadcasting to {len(modules)} modules...\n')
            responses = []
            for i, mod in enumerate(modules):
                if i > 0:
                    time.sleep(DELAY)
                hist = histories.get(mod, [])
                data = _chat(mod, msg, hist)
                reply = data.get('response', '[no response]')
                hist.append({'who': 'user', 'text': msg})
                hist.append({'who': 'file', 'text': reply})
                responses.append({'module': mod, 'response': reply,
                                 'extractions': data.get('extractions', [])})
                print(f'  === {mod} ===')
                print(f'  {reply}\n')
            # Auto-consensus after broadcast
            verdict = _synthesize_consensus(responses)
            print(verdict)
            continue

        if prompt == '/consensus':
            # Rebuild consensus from histories
            print('\n  [rebuilding consensus from conversation histories...]\n')
            responses = []
            for mod in modules:
                hist = histories.get(mod, [])
                file_msgs = [h['text'] for h in hist if h.get('who') == 'file']
                if file_msgs:
                    # Re-extract tags from last response
                    import re
                    last = file_msgs[-1]
                    extractions = []
                    for m in re.finditer(
                        r'\[(CAUSE|FIX|BLOCKER|INTENT|PAIN|DECISION|PLAN|UNKNOWN)\]\s*(.+?)(?=\[(?:CAUSE|FIX|BLOCKER|INTENT|PAIN|DECISION|PLAN|UNKNOWN)\]|[.!?]\s|$)',
                        last, re.DOTALL
                    ):
                        extractions.append({'tag': m.group(1), 'text': m.group(2).strip()[:200]})
                    responses.append({'module': mod, 'response': last, 'extractions': extractions})
            if responses:
                verdict = _synthesize_consensus(responses)
                print(verdict)
            else:
                print('  [no conversation data yet — talk to files first]')
            continue

        # Regular message to current module
        hist = histories.get(current, [])
        data = _chat(current, prompt, hist)
        reply = data.get('response', '[no response]')
        hist.append({'who': 'user', 'text': prompt})
        hist.append({'who': 'file', 'text': reply})
        print(f'\n  [{current}]: {reply}\n')

        # Show extractions if any
        for ext in data.get('extractions', []):
            print(f'    [{ext["tag"]}] {ext["text"]}')
        if data.get('extractions'):
            print()


# ── main ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Multi-file consensus debugging')
    parser.add_argument('--bug', default='auto',
                       help='Bug type to investigate (overcap, hardcoded_import, or auto)')
    parser.add_argument('--modules', default='',
                       help='Comma-separated module names (overrides auto-select)')
    parser.add_argument('--interactive-only', action='store_true',
                       help='Skip consensus round, go straight to interactive chat')
    parser.add_argument('--delay', type=int, default=6,
                       help='Seconds between Gemini calls (rate limit protection)')
    args = parser.parse_args()

    global DELAY
    DELAY = args.delay

    print('╔══════════════════════════════════╗')
    print('║  ORGANISM CONSENSUS DEBUGGER     ║')
    print('║  files diagnose their own bugs   ║')
    print('╚══════════════════════════════════╝')
    print()

    # Load bug data
    bugs = _load_bug_profiles_seq001_v001()
    if not bugs:
        print('[warning] no bug data found — running in interactive-only mode')
        args.interactive_only = True

    # Pick bug
    bug_type = args.bug
    if bug_type == 'auto' and bugs:
        # Pick the one with most entries
        bug_type = max(bugs.keys(), key=lambda k: len(bugs[k]))
        print(f'Auto-selected bug: {bug_type} ({len(bugs[bug_type])} modules affected)')
    bug_data = bugs.get(bug_type, [])

    # Get available modules
    print('Loading module identities...')
    all_modules = _get_available_modules()
    if not all_modules:
        print('[error] cannot load identities — is the server running on :8234?')
        return
    print(f'  {len(all_modules)} modules available')

    # Select modules
    if args.modules:
        selected = []
        for name in args.modules.split(','):
            name = name.strip()
            for full in all_modules:
                if name == full or name in full:
                    selected.append(full)
                    break
    else:
        selected = _select_modules_for_bug(bug_type, bug_data, all_modules)

    if not selected:
        print('[error] no matching modules found')
        return

    print(f'\nSelected {len(selected)} modules for consensus:')
    for i, m in enumerate(selected):
        print(f'  {i+1}. {m}')

    # Initialize conversation histories
    histories: dict[str, list] = {m: [] for m in selected}

    if not args.interactive_only and bug_data:
        # Consensus round — each file diagnoses the bug
        briefing = _build_bug_briefing(bug_type, bug_data)
        print(f'\n── BRIEFING ──')
        print(f'{briefing}\n')
        print(f'── GATHERING DIAGNOSES ({len(selected)} files) ──\n')

        responses = []
        for i, mod in enumerate(selected):
            if i > 0:
                time.sleep(DELAY)
            print(f'  Asking {mod}...', end=' ', flush=True)
            data = _chat(mod, briefing)
            reply = data.get('response', '[no response]')
            histories[mod].append({'who': 'user', 'text': briefing})
            histories[mod].append({'who': 'file', 'text': reply})
            responses.append({
                'module': mod,
                'response': reply,
                'extractions': data.get('extractions', []),
            })
            print('done')
            print(f'\n  === {mod} ===')
            print(f'  {reply}\n')

        # Synthesize consensus
        print('\n── CONSENSUS ──\n')
        verdict = _synthesize_consensus(responses)
        print(verdict)

    # Interactive mode
    _interactive_loop(selected, histories)


if __name__ == '__main__':
    main()
