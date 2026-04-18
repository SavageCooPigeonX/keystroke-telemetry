"""bug_demon_hunt_seq001_v001.py — bug demons write their own manifests, flow through veins, files propose fixes.

Architecture:
  1. BugDemon reads BUG_PROFILES.md, writes its own status manifest (first-person)
  2. Manifest becomes task_seed for run_flow(mode="failure") — traces through import graph
  3. At each node: packet gains bug-specific intel (fears, dual_score, consciousness)
  4. Backward pass computes credit — which node CAUSED vs which node carries
  5. Node memory accumulates — nodes learn which bugs they cause across cycles
  6. Chat server lets nodes TALK about the bug with accumulated manifest as context
  7. Files write self-improvement proposals requesting missing context
  8. Distributed proposal — each file contributes its section

Usage:
    py src/bug_demon_hunt_seq001_v001.py                          # full hunt: overcap maw
    py src/bug_demon_hunt_seq001_v001.py --bug hardcoded_import   # hunt specific demon
    py src/bug_demon_hunt_seq001_v001.py --proposals              # skip hunt, go to proposals
    py src/bug_demon_hunt_seq001_v001.py --stress-test            # hunt bugs in the hunt system itself
"""
from __future__ import annotations
import json
import sys
import time
import re
import glob
import importlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SERVER = 'http://localhost:8234'
DELAY = 6


# ── dynamic imports for pigeon modules (names mutate) ──

def _import_flow_module(pattern: str):
    matches = sorted(glob.glob(str(ROOT / pattern)))
    if not matches:
        return None
    stem = Path(matches[-1]).stem
    parts = pattern.replace('/', '.').replace('\\', '.')
    pkg = '.'.join(parts.split('.')[:-1])  # e.g. pigeon_brain.flow
    return importlib.import_module(f'{pkg}.{stem}')


def _load_flow_engine():
    return _import_flow_module('pigeon_brain/flow/流f_fe*')


def _load_node_memory():
    return _import_flow_module('pigeon_brain/flow/存p_nm*')


def _load_backward():
    return _import_flow_module('pigeon_brain/flow/逆f_ba*')


# ── bug demon entity ──

class BugDemon:
    """A bug that writes its own manifest and status report."""

    def __init__(self, bug_type: str, hosts: list[dict]):
        self.bug_type = bug_type
        self.hosts = hosts
        self.demon_name = self._name()
        self.manifest = self._write_manifest()
        self.hunt_results: list[dict] = []

    def _name(self) -> str:
        names = {
            'overcap': 'Overcap Maw',
            'hardcoded_import': 'Import Phantom',
            'dead_export': 'Null Moth',
        }
        return names.get(self.bug_type, f'Bug Demon ({self.bug_type})')

    def _write_manifest(self) -> str:
        """First-person status report from the bug demon."""
        ts = datetime.now(timezone.utc).isoformat()
        host_lines = []
        for h in self.hosts[:8]:
            mod = h.get('module', '?')
            tok = h.get('tokens', '?')
            pct = h.get('pct_over', '?')
            reps = h.get('reports', '?')
            host_lines.append(f'  - {mod}: {tok} tokens, {pct}% over cap, spotted {reps}x')

        return (
            f"I am the {self.demon_name}. Status report {ts}.\n"
            f"Bug type: {self.bug_type}\n"
            f"I inhabit {len(self.hosts)} modules. I am chronic — I appear in 70%+ of reports.\n"
            f"Every time they 'fix' me, I come back. Here's where I live:\n"
            + '\n'.join(host_lines) + '\n'
            f"\nI survive because: files accumulate functions without splitting. "
            f"The pigeon compiler can kill me but nobody runs it on these files. "
            f"My hosts grow on every push cycle. I eat context window.\n"
            f"\nI CHALLENGE every node on this path to explain: "
            f"are you feeding me? are you blocking my death? what would it take to kill me?\n"
            f"Tag your response: [CAUSE] [FIX] [BLOCKER] [MISSING_CONTEXT]"
        )

    def write_status(self) -> str:
        """Current status after hunt."""
        n_nodes = sum(len(r.get('path', [])) for r in self.hunt_results)
        n_fears = sum(len(r.get('fears', [])) for r in self.hunt_results)
        n_warnings = sum(len(r.get('warnings', [])) for r in self.hunt_results)
        return (
            f"=== {self.demon_name} STATUS ===\n"
            f"Hosts: {len(self.hosts)}\n"
            f"Nodes traced: {n_nodes}\n"
            f"Fears collected: {n_fears}\n"
            f"Dead vein warnings: {n_warnings}\n"
            f"Hunt results: {len(self.hunt_results)} flow passes\n"
        )


def _load_bug_profiles_seq001_v001() -> dict[str, list[dict]]:
    """Parse BUG_PROFILES.md into structured bug data."""
    bugs: dict[str, list[dict]] = {}
    bp = ROOT / 'docs' / 'BUG_PROFILES.md'
    if not bp.exists():
        return bugs
    text = bp.read_text('utf-8', errors='ignore')

    # overcap entries
    for m in re.finditer(
        r'`(\S+?)` came in wheezing at (\d+) tokens.*?(\d+)% over.*?Spotted (\d+)x',
        text, re.DOTALL
    ):
        mod, tokens, pct, count = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        bugs.setdefault('overcap', []).append({
            'module': mod, 'tokens': tokens, 'pct_over': pct, 'reports': count,
        })

    # dead export entries
    for m in re.finditer(r'`(\S+?)` has (\d+) dead export', text):
        mod, count = m.group(1), int(m.group(2))
        bugs.setdefault('dead_export', []).append({
            'module': mod, 'dead_count': count, 'reports': count,
        })

    # hardcoded import from copilot-instructions
    ci = ROOT / '.github' / 'copilot-instructions.md'
    if ci.exists():
        ci_text = ci.read_text('utf-8', errors='ignore')
        for m in re.finditer(r'`(\S+?)` — \[hardcoded_import\] (\d+)/\d+ reports', ci_text):
            mod, count = m.group(1), int(m.group(2))
            bugs.setdefault('hardcoded_import', []).append({
                'module': mod, 'reports': count,
            })

    return bugs


# ── flow-based hunt ──

def run_hunt(demon: BugDemon) -> dict:
    """Send the bug demon's manifest through the flow engine."""
    fe = _load_flow_engine()
    if not fe:
        print('[error] flow engine not found')
        return {}

    print(f'\n--- DEMON MANIFEST ---')
    print(demon.manifest)
    print('--- END MANIFEST ---\n')

    # Run flow in failure mode — traces failure patterns
    print('Running flow engine (failure mode)...')
    try:
        packet = fe.run_flow(ROOT, demon.manifest, mode='failure')
        result = {
            'path': packet.path,
            'accumulated': len(packet.accumulated),
            'fears': packet.fear_chain,
            'warnings': packet.dead_vein_warnings,
            'heat': packet.heat,
            'depth': packet.depth,
            'narrative': packet.narrative_fragments,
        }
        demon.hunt_results.append(result)
        print(f'  Path: {" → ".join(packet.path)}')
        print(f'  Nodes awakened: {len(packet.accumulated)}')
        print(f'  Heat: {packet.heat:.3f}')
        if packet.fear_chain:
            print(f'  Fears collected:')
            for f in packet.fear_chain[:10]:
                print(f'    - {f}')
        if packet.dead_vein_warnings:
            print(f'  Dead vein warnings:')
            for w in packet.dead_vein_warnings[:5]:
                print(f'    ⚠ {w}')
        return result
    except Exception as e:
        print(f'  flow error: {e}')
        import traceback; traceback.print_exc()
        return {}


def run_multi_hunt(demon: BugDemon) -> list[dict]:
    """Run all 3 flow modes to trace the bug from different angles."""
    fe = _load_flow_engine()
    if not fe:
        return []

    results = []
    for mode in ['failure', 'targeted', 'heat']:
        print(f'\n  [{mode} mode]...')
        try:
            packet = fe.run_flow(ROOT, demon.manifest, mode=mode)
            r = {
                'mode': mode,
                'path': packet.path,
                'accumulated': len(packet.accumulated),
                'fears': packet.fear_chain,
                'warnings': packet.dead_vein_warnings,
                'heat': packet.heat,
                'narrative': packet.narrative_fragments,
            }
            results.append(r)
            demon.hunt_results.append(r)
            print(f'    path: {" → ".join(packet.path[:6])}{"..." if len(packet.path) > 6 else ""}')
            print(f'    awakened: {len(packet.accumulated)}, heat: {packet.heat:.3f}')
        except Exception as e:
            print(f'    error: {e}')

    return results


# ── node memory analysis ──

def analyze_node_memory(demon: BugDemon) -> dict:
    """Check which nodes on the trace have learned about this bug before."""
    nm = _load_node_memory()
    if not nm:
        return {}

    mem = nm.load_memory(ROOT)
    all_traced = set()
    for r in demon.hunt_results:
        all_traced.update(r.get('path', []))

    analysis = {}
    for node in all_traced:
        if node in mem:
            entry = mem[node]
            policy = entry.get('policy', {})
            analysis[node] = {
                'rolling_score': policy.get('rolling_score', 0),
                'confidence': policy.get('confidence', 0),
                'sample_count': policy.get('sample_count', 0),
                'top_patterns': policy.get('top_effective_patterns', [])[:2],
                'failure_patterns': policy.get('failure_patterns', [])[:2],
                'directive': policy.get('behavioral_directive', ''),
            }
        else:
            analysis[node] = {'rolling_score': 0, 'confidence': 0, 'sample_count': 0,
                             'note': 'NO MEMORY — never trained on this node'}

    return analysis


# ── chat integration ──

def _chat(module: str, message: str, history: list | None = None) -> dict:
    """Send message to module via organism chat server."""
    import urllib.request
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


def gather_proposals(demon: BugDemon, hunt_results: list[dict],
                     memory_analysis: dict) -> list[dict]:
    """Ask each traced node to write a self-improvement proposal."""
    all_nodes = set()
    for r in hunt_results:
        all_nodes.update(r.get('path', []))

    # Also add the actual host modules
    for h in demon.hosts[:5]:
        all_nodes.add(h['module'])

    nodes = list(all_nodes)[:10]  # cap at 10

    # Build context from hunt results
    trace_summary = []
    for r in hunt_results:
        trace_summary.append(
            f"[{r.get('mode', 'unknown')}] path: {' → '.join(r.get('path', []))}, "
            f"fears: {len(r.get('fears', []))}, heat: {r.get('heat', 0):.2f}"
        )

    context = (
        f"BUG DEMON: {demon.demon_name}\n"
        f"Manifest: {demon.manifest[:500]}\n\n"
        f"FLOW TRACES:\n" + '\n'.join(trace_summary) + '\n\n'
        f"NODE MEMORY (who has learned what):\n"
    )
    for node, data in list(memory_analysis.items())[:8]:
        rs = data.get('rolling_score', 0)
        sc = data.get('sample_count', 0)
        context += f"  {node}: score={rs:.3f}, samples={sc}\n"

    prompt = (
        f"{context}\n"
        f"You are a file that was just traced by the {demon.demon_name}. "
        f"The bug demon flowed through the import graph and found you on its path.\n\n"
        f"Write a SELF-IMPROVEMENT PROPOSAL. Include:\n"
        f"1. [DIAGNOSIS] What's your role in this bug? Be specific — name your functions.\n"
        f"2. [MISSING_CONTEXT] What information do you NEED but don't have? "
        f"What other files should you be able to see/talk to?\n"
        f"3. [PROPOSAL] One concrete fix you can make to yourself. "
        f"Not vague — name the function, the change, the expected outcome.\n"
        f"4. [REQUEST] What do you need from the operator to make this happen?\n\n"
        f"Be brutally honest. Don't hedge. This is your chance to improve."
    )

    proposals = []
    print(f'\n╔══ GATHERING PROPOSALS ({len(nodes)} files) ══╗\n')

    for i, node in enumerate(nodes):
        if i > 0:
            time.sleep(DELAY)
        print(f'  Asking {node}...', end=' ', flush=True)
        data = _chat(node, prompt)
        reply = data.get('response', '[no response]')
        exts = data.get('extractions', [])
        print('done')

        proposals.append({
            'module': node,
            'response': reply,
            'extractions': exts,
            'memory': memory_analysis.get(node, {}),
        })

        print(f'\n  === {node} ===')
        print(f'  {reply[:500]}')
        if len(reply) > 500:
            print(f'  ... ({len(reply)} chars total)')
        print()

    return proposals


def build_distributed_proposal(demon: BugDemon, proposals: list[dict],
                               hunt_results: list[dict]) -> str:
    """Synthesize all file proposals into one distributed document."""
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    sections = [
        f'# Distributed Proposal: Kill the {demon.demon_name}',
        f'*Generated {ts} — {len(proposals)} files contributed*\n',
        f'## Bug Summary',
        f'Type: `{demon.bug_type}` | Hosts: {len(demon.hosts)} | '
        f'Flow traces: {len(hunt_results)}\n',
    ]

    # Collect all diagnoses, missing context, proposals, requests
    diagnoses, missing, fixes, requests = [], [], [], []
    for p in proposals:
        mod = p['module']
        resp = p['response']

        for ext in p.get('extractions', []):
            tag, text = ext.get('tag', ''), ext.get('text', '')
            if tag == 'DIAGNOSIS' or tag == 'CAUSE':
                diagnoses.append(f'**{mod}**: {text}')
            elif tag == 'MISSING_CONTEXT' or tag == 'PAIN':
                missing.append(f'**{mod}**: {text}')
            elif tag == 'PROPOSAL' or tag == 'FIX' or tag == 'PLAN':
                fixes.append(f'**{mod}**: {text}')
            elif tag == 'REQUEST' or tag == 'INTENT':
                requests.append(f'**{mod}**: {text}')

        # Also extract from response text with regex
        for m in re.finditer(r'\[DIAGNOSIS\]\s*(.+?)(?=\[|$)', resp, re.DOTALL):
            diagnoses.append(f'**{mod}**: {m.group(1).strip()[:200]}')
        for m in re.finditer(r'\[MISSING_CONTEXT\]\s*(.+?)(?=\[|$)', resp, re.DOTALL):
            missing.append(f'**{mod}**: {m.group(1).strip()[:200]}')
        for m in re.finditer(r'\[PROPOSAL\]\s*(.+?)(?=\[|$)', resp, re.DOTALL):
            fixes.append(f'**{mod}**: {m.group(1).strip()[:200]}')
        for m in re.finditer(r'\[REQUEST\]\s*(.+?)(?=\[|$)', resp, re.DOTALL):
            requests.append(f'**{mod}**: {m.group(1).strip()[:200]}')

    # Deduplicate
    diagnoses = list(dict.fromkeys(diagnoses))
    missing = list(dict.fromkeys(missing))
    fixes = list(dict.fromkeys(fixes))
    requests = list(dict.fromkeys(requests))

    sections.append(f'## Diagnoses ({len(diagnoses)} from {len(proposals)} files)')
    for d in diagnoses:
        sections.append(f'- {d}')

    sections.append(f'\n## Missing Context ({len(missing)} requests)')
    sections.append('*Files requesting information they need but cannot access:*')
    for m in missing:
        sections.append(f'- {m}')

    sections.append(f'\n## Proposed Fixes ({len(fixes)})')
    for f in fixes:
        sections.append(f'- {f}')

    sections.append(f'\n## Operator Requests ({len(requests)})')
    for r in requests:
        sections.append(f'- {r}')

    # Flow trace summary
    sections.append('\n## Flow Trace Evidence')
    for r in hunt_results:
        mode = r.get('mode', '?')
        path = ' → '.join(r.get('path', []))
        heat = r.get('heat', 0)
        sections.append(f'- **[{mode}]** {path} (heat={heat:.2f})')

    # Node memory learning
    sections.append('\n## Node Memory (what files have learned)')
    for p in proposals:
        mod = p['module']
        mem = p.get('memory', {})
        rs = mem.get('rolling_score', 0)
        sc = mem.get('sample_count', 0)
        note = mem.get('note', '')
        if note:
            sections.append(f'- **{mod}**: {note}')
        else:
            sections.append(f'- **{mod}**: score={rs:.3f}, samples={sc}')

    sections.append(f'\n---\n*{demon.demon_name} says: '
                    f'"I inhabit {len(demon.hosts)} modules. Kill me if you can."*')

    return '\n'.join(sections)


# ── stress test: hunt bugs in the hunt system itself ──

def stress_test_self() -> BugDemon:
    """Create a demon that hunts for bugs in the flow engine itself."""
    # The flow engine's own modules — look for overcap in pigeon_brain
    self_hosts = []
    for pattern, name in [
        ('pigeon_brain/flow/逆f_ba*', '逆f_ba'),
        ('pigeon_brain/flow/学f_ll*', '学f_ll'),
        ('pigeon_brain/flow/算f_ps*', '算f_ps'),
    ]:
        matches = sorted(glob.glob(str(ROOT / pattern)))
        if matches:
            p = Path(matches[-1])
            tokens = len(p.read_text('utf-8', errors='ignore').split())
            self_hosts.append({
                'module': name,
                'tokens': tokens,
                'pct_over': max(0, int((tokens / 200 - 1) * 100)),
                'reports': 1,
            })

    # Also check src modules that are overcap
    for pattern, name in [
        ('src/修f_sf*', '修f_sf'),
        ('src/管w_cpm*', '管w_cpm'),
    ]:
        matches = sorted(glob.glob(str(ROOT / pattern)))
        if matches:
            p = Path(matches[-1])
            tokens = len(p.read_text('utf-8', errors='ignore').split())
            self_hosts.append({
                'module': name,
                'tokens': tokens,
                'pct_over': max(0, int((tokens / 200 - 1) * 100)),
                'reports': 3,
            })

    demon = BugDemon('self_diagnosis', self_hosts)
    demon.demon_name = 'Introspection Worm'
    demon.manifest = (
        f"I am the Introspection Worm. I hunt bugs in the bug hunting system itself.\n"
        f"The flow engine, backward pass, learning loop, and node memory — "
        f"these are the tools that chase bugs. But who chases THEIR bugs?\n\n"
        f"Known issues in the hunt infrastructure:\n"
        f"- backward pass (逆f_ba) is overcap and uses DeepSeek (cost, latency)\n"
        f"- learning loop polls every 5s — what if it misses fast sequences?\n"
        f"- node memory caps at 200 entries per node — is that enough?\n"
        f"- flow engine only traces 15 hops max — deep dependency chains get cut\n"
        f"- prediction accuracy is untested — phantom electrons may be noise\n\n"
        f"I CHALLENGE every node: what breaks in YOUR infrastructure? "
        f"What context do you need that you don't have? "
        f"How would you improve yourself if you could?\n"
        f"Tag: [CAUSE] [FIX] [BLOCKER] [MISSING_CONTEXT] [PROPOSAL]"
    )
    return demon


# ── main ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Bug Demon Hunt — files diagnose their own bugs')
    parser.add_argument('--bug', default='auto',
                       help='Bug type: overcap, hardcoded_import, dead_export, auto')
    parser.add_argument('--stress-test', action='store_true',
                       help='Hunt bugs in the hunt system itself')
    parser.add_argument('--proposals', action='store_true',
                       help='Skip hunt, go straight to proposals')
    parser.add_argument('--delay', type=int, default=6)
    parser.add_argument('--no-chat', action='store_true',
                       help='Flow-only mode — no LLM calls')
    parser.add_argument('--save', action='store_true',
                       help='Save distributed proposal to docs/')
    args = parser.parse_args()

    global DELAY
    DELAY = args.delay

    print('╔═══════════════════════════════════╗')
    print('║  BUG DEMON HUNT                   ║')
    print('║  bugs write their own manifests    ║')
    print('║  files propose their own fixes     ║')
    print('╚═══════════════════════════════════╝\n')

    # Create demon
    if args.stress_test:
        print('MODE: stress test — hunting bugs in the hunt system\n')
        demon = stress_test_self()
    else:
        bugs = _load_bug_profiles_seq001_v001()
        if not bugs:
            print('[error] no bug profiles found')
            return

        bug_type = args.bug
        if bug_type == 'auto':
            bug_type = max(bugs.keys(), key=lambda k: sum(b.get('reports', 0) for b in bugs[k]))
        bug_data = bugs.get(bug_type, [])
        if not bug_data:
            print(f'[error] no data for bug type: {bug_type}')
            return

        bug_data.sort(key=lambda x: -x.get('tokens', x.get('reports', 0)))
        demon = BugDemon(bug_type, bug_data)

    print(f'Demon: {demon.demon_name}')
    print(f'Hosts: {len(demon.hosts)}')
    print(f'Manifest length: {len(demon.manifest)} chars\n')

    # Phase 1: Flow hunt
    if not args.proposals:
        print('═══ PHASE 1: FLOW TRACE ═══\n')
        hunt_results = run_multi_hunt(demon)
        if not hunt_results:
            print('[warning] flow trace produced no results — continuing with chat only')
    else:
        hunt_results = []

    # Phase 2: Node memory analysis
    print('\n═══ PHASE 2: NODE MEMORY ANALYSIS ═══\n')
    memory_analysis = analyze_node_memory(demon)
    if memory_analysis:
        trained = sum(1 for v in memory_analysis.values() if v.get('sample_count', 0) > 0)
        untrained = len(memory_analysis) - trained
        print(f'  Traced nodes: {len(memory_analysis)}')
        print(f'  With memory: {trained} | No memory: {untrained}')
        for node, data in sorted(memory_analysis.items(),
                                  key=lambda x: -x[1].get('sample_count', 0))[:5]:
            if data.get('sample_count', 0) > 0:
                print(f'    {node}: score={data["rolling_score"]:.3f}, '
                      f'samples={data["sample_count"]}, conf={data["confidence"]:.2f}')
    else:
        print('  No node memory data')

    # Phase 3: Chat-based proposals (requires server)
    if not args.no_chat:
        print('\n═══ PHASE 3: FILE PROPOSALS ═══')
        proposals = gather_proposals(demon, hunt_results, memory_analysis)

        # Phase 4: Distributed proposal
        print('\n═══ PHASE 4: DISTRIBUTED PROPOSAL ═══\n')
        doc = build_distributed_proposal(demon, proposals, hunt_results)
        print(doc)

        if args.save:
            out_path = ROOT / 'docs' / f'proposal_{demon.bug_type}_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")}.md'
            out_path.write_text(doc, encoding='utf-8')
            print(f'\nSaved to {out_path}')

        # Phase 5: Demon final status
        print(f'\n{demon.write_status()}')
    else:
        print('\n[--no-chat mode: skipping LLM proposals]')
        print(f'\n{demon.write_status()}')


if __name__ == '__main__':
    main()
