"""loop_killswitch_sim_seq001_v001.py — files diagnose why the learning loop died.

The learning loop ran 52 cycles on March 27, then stopped. 414 journal
entries sit unprocessed. The code has no killswitch (while True). So what killed it?

This sim asks every module in the learning loop's dependency chain to diagnose
the stoppage from their own perspective, using personality + consciousness.

Usage:
    py src/loop_killswitch_sim_seq001_v001.py
"""
from __future__ import annotations
import json
import sys
import time
import glob
import importlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SERVER = 'http://localhost:8234'
DELAY = 15  # gemini rate limit — 503s at 8s
RETRIES = 2


def _chat(module: str, message: str) -> dict:
    import urllib.request
    payload = {'module': module, 'message': message}
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(
                f'{SERVER}/chat',
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=120)
            return json.loads(resp.read())
        except Exception as e:
            err = str(e)
            if ('503' in err or '429' in err) and attempt < RETRIES:
                wait = DELAY * (attempt + 1)
                print(f'  [retry {attempt+1}, wait {wait}s...]', flush=True)
                time.sleep(wait)
                continue
            return {'response': f'[error: {e}]', 'extractions': []}


def _build_evidence() -> str:
    """Gather hard evidence about the stoppage."""
    # Learning loop state
    state_path = ROOT / 'pigeon_brain' / 'learning_loop_state.json'
    state = json.loads(state_path.read_text('utf-8')) if state_path.exists() else {}

    # Journal stats
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    journal_lines = 0
    if journal.exists():
        journal_lines = len(journal.read_text('utf-8').strip().splitlines())

    unprocessed = journal_lines - state.get('last_processed_line', 0)

    # Node memory stats
    nm_path = ROOT / 'pigeon_brain' / 'node_memory.json'
    node_count = 0
    if nm_path.exists():
        nm = json.loads(nm_path.read_text('utf-8'))
        node_count = len(nm)

    # Reactor state
    reactor_path = ROOT / 'logs' / 'cognitive_reactor_state.json'
    reactor_fires = 0
    reactor_patches = 0
    if reactor_path.exists():
        rs = json.loads(reactor_path.read_text('utf-8'))
        reactor_fires = rs.get('total_fires', 0)
        reactor_patches = rs.get('total_patches_generated', 0)

    # Check the learning loop source for clues
    loop_files = sorted(glob.glob(str(ROOT / 'pigeon_brain/flow/学f_ll*')))
    loop_src = ''
    if loop_files:
        loop_src = Path(loop_files[-1]).read_text('utf-8', errors='ignore')

    # Extract key facts from the source
    has_while_true = 'while True' in loop_src
    has_once_flag = '--once' in loop_src or 'once: bool' in loop_src
    has_catch_up = 'catch_up' in loop_src
    poll_interval = '5.0' if 'POLL_INTERVAL = 5.0' in loop_src else '?'

    # Check the CLI entry point
    cli_files = sorted(glob.glob(str(ROOT / 'pigeon_brain/令*')))
    cli_src = ''
    if cli_files:
        cli_src = Path(cli_files[-1]).read_text('utf-8', errors='ignore')

    # Does the CLI wire the loop command?
    loop_wired_in_cli = 'loop' in cli_src and 'run_loop' in cli_src

    # Check git log for when it was last run
    import subprocess
    try:
        git_log = subprocess.run(
            ['git', 'log', '--all', '--oneline', '--grep=learning', '-5'],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        ).stdout.strip()
    except Exception:
        git_log = '[git unavailable]'

    return f"""=== LEARNING LOOP AUTOPSY ===

STATE FILE (pigeon_brain/learning_loop_state.json):
  last_processed_line: {state.get('last_processed_line', '?')}
  last_processed_ts: {state.get('last_processed_ts', '?')}
  total_cycles: {state.get('total_cycles', '?')}
  total_forward: {state.get('total_forward', '?')}
  total_backward: {state.get('total_backward', '?')}
  total_predictions: {state.get('total_predictions', '?')}
  total_cost: ${state.get('total_cost', '?')}
  started_at: {state.get('started_at', '?')}
  updated_at: {state.get('updated_at', '?')}

JOURNAL:
  total entries: {journal_lines}
  unprocessed: {unprocessed}
  gap: loop stopped at line {state.get('last_processed_line', '?')}, journal is now at line {journal_lines}

CODE FACTS:
  has while True: {has_while_true}
  has --once flag: {has_once_flag}
  has catch_up mode: {has_catch_up}
  poll interval: {poll_interval}s
  loop wired in CLI: {loop_wired_in_cli}

DOWNSTREAM:
  node_memory entries: {node_count}
  cognitive_reactor fires: {reactor_fires}
  cognitive_reactor patches generated: {reactor_patches}

GIT (mentions of 'learning'):
{git_log}

KEY QUESTION: The code is while True + sleep(5). There is NO killswitch.
So WHY did it stop? Was it run with --once? Was the terminal closed? 
Was there an exception that crashed it? Did something upstream break?
The operator was NEVER NOTIFIED that it died. 414 entries are rotting."""


def run_sim():
    evidence = _build_evidence()

    # Modules in the learning loop dependency chain
    # Use names the chat server identity system can resolve
    # These match graph_cache nodes or module identity stems
    targets = [
        ('learning_loop', 'You ARE the learning loop. You ran 52 cycles then died on March 27. Diagnose yourself. 414 journal entries sit unprocessed.'),
        ('flow_engine', 'The learning loop calls your run_flow() on every cycle. Did you break? Did you throw an exception that killed the loop?'),
        ('backward_pass', 'The learning loop calls your backward_pass() for DeepSeek analysis. Did you fail silently? Did DeepSeek timeout and crash the loop?'),
        ('predictor', 'The loop fires you every 10 cycles via predict_next_needs(). You fired 0 predictions in 52 cycles. Why? PREDICT_EVERY=10, so cycle 10,20,30,40,50 should have triggered you.'),
        ('cognitive_reactor', 'You fired 524 times but generated 0 patches. The learning loop is dead and you never noticed. Why didnt you detect this?'),
    ]

    prompt_template = (
        "{evidence}\n\n"
        "YOU ARE: {module_name}\n"
        "{role_context}\n\n"
        "TASK: Diagnose why the learning loop stopped. Be specific:\n"
        "1. [CAUSE] What do you think killed it? Name the exact failure mode.\n"
        "2. [EVIDENCE] What evidence from the autopsy supports your theory?\n"
        "3. [YOUR_ROLE] Did YOU contribute to the death? Be honest.\n"
        "4. [FIX] What's the one thing that would prevent this from happening again?\n"
        "5. [NOTIFICATION] How should the operator have been notified?\n\n"
        "Don't hedge. Finger-point. Name names. The operator was never told."
    )

    results = []

    print('╔══════════════════════════════════════════════╗')
    print('║   LEARNING LOOP KILLSWITCH INVESTIGATION    ║')
    print(f'║   {len(targets)} modules simulating their own diagnosis    ║')
    print('╚══════════════════════════════════════════════╝')
    print(f'\nEvidence gathered. {len(targets)} modules will testify.\n')

    for i, (module, role_context) in enumerate(targets):
        if i > 0:
            time.sleep(DELAY)

        prompt = prompt_template.format(
            evidence=evidence,
            module_name=module,
            role_context=role_context,
        )

        print(f'┌─── {module} testifying... ───')
        data = _chat(module, prompt)
        reply = data.get('response', '[no response]')
        extractions = data.get('extractions', [])

        print(f'│ {reply[:500]}')
        if len(reply) > 500:
            print(f'│ ... [{len(reply)} chars total]')
        if extractions:
            print(f'│ Extractions: {extractions}')
        print(f'└───\n')

        results.append({
            'module': module,
            'response': reply,
            'extractions': extractions,
        })

    # Synthesize
    print('\n╔══ SYNTHESIS ══╗')
    causes = []
    fixes = []
    for r in results:
        resp = r['response']
        for line in resp.split('\n'):
            if '[CAUSE]' in line:
                causes.append(f"  {r['module']}: {line.split('[CAUSE]')[-1].strip()[:120]}")
            if '[FIX]' in line:
                fixes.append(f"  {r['module']}: {line.split('[FIX]')[-1].strip()[:120]}")

    if causes:
        print('\nCAUSES identified:')
        for c in causes:
            print(c)
    if fixes:
        print('\nFIXES proposed:')
        for f in fixes:
            print(f)

    # Write report
    report_path = ROOT / 'docs' / f'loop_killswitch_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    report_path.parent.mkdir(exist_ok=True)

    report = ['# Learning Loop Killswitch Diagnosis\n']
    report.append(f'*{datetime.now(timezone.utc).isoformat()} — 8 modules testifying*\n')
    report.append('## Evidence\n')
    report.append(f'```\n{evidence}\n```\n')
    report.append('## Module Testimonies\n')
    for r in results:
        report.append(f'### {r["module"]}\n')
        report.append(f'{r["response"]}\n\n')
        if r['extractions']:
            report.append(f'**Extractions:** {r["extractions"]}\n\n')
    report.append('## Causes\n')
    for c in causes:
        report.append(f'{c}\n')
    report.append('\n## Fixes\n')
    for f in fixes:
        report.append(f'{f}\n')

    report_path.write_text('\n'.join(report), encoding='utf-8')
    print(f'\n[saved] {report_path}')

    return results


if __name__ == '__main__':
    run_sim()
