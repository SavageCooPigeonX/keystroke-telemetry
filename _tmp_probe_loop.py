"""Live probe loop test — resolve complex probes against real operator telemetry.

This tests whether the probe resolver can reconstruct operator intent
from prompt_journal, unsaid_recon, file_consciousness, and push_narrative
well enough to autonomously steer copilot's next actions.
"""
import json
from pathlib import Path
from src.probe_surface_seq001_v001_seq001_v001 import parse_probe_blocks, write_resolution, build_resolution_block
from src.probe_resolver_seq001_v001_seq001_v001 import (
    resolve_probe,
    _load_recent_prompts,
    _load_unsaid_threads,
    _load_file_profiles,
    _load_push_narratives,
)

root = Path('.')

# ── PHASE 1: Understand what signal we have ──────────────────────
print('=' * 60)
print('PHASE 1: Signal inventory')
print('=' * 60)

prompts = _load_recent_prompts(root, limit=50)
threads = _load_unsaid_threads(root, limit=20)
profiles = _load_file_profiles(root)
narratives = _load_push_narratives(root, limit=5)

print(f'  prompt_journal: {len(prompts)} entries')
print(f'  unsaid_recon:   {len(threads)} threads')
print(f'  file_profiles:  {len(profiles)} modules profiled')
print(f'  push_narrative: {len(narratives)} recent narratives')

if prompts:
    print(f'\n  Last 5 prompts:')
    for p in prompts[-5:]:
        msg = p.get('msg', p.get('preview', ''))[:100]
        intent = p.get('intent', '?')
        state = p.get('state', '?')
        print(f'    [{intent}/{state}] {msg}')

if threads:
    print(f'\n  Last 3 unsaid threads:')
    for t in threads[-3:]:
        print(f'    deleted: {t.get("deleted_words", [])}')
        print(f'    intent: {t.get("reconstructed_intent", "?")[:100]}')

# ── PHASE 2: Emit complex probes from real decision forks ────────
print('\n' + '=' * 60)
print('PHASE 2: Complex probes (real ambiguity)')
print('=' * 60)

# These are genuine questions about what to build next based on codebase signals
probes = [
    {
        'module': 'probe_resolver_seq001_v001',
        'question': 'should probe resolution happen synchronously during refresh or async via streaming layer?',
        'candidates': ['sync_during_refresh', 'async_streaming', 'both_with_fallback'],
        'confidence': 0.40,
        'context': 'operator mentioned live sync layer and 10x query volume',
    },
    {
        'module': 'query_memory',
        'question': 'operator keeps query_memory as a clot — should it be split, deleted, or repurposed for probe history?',
        'candidates': ['split', 'delete', 'repurpose_for_probes'],
        'confidence': 0.35,
        'context': 'self-fix flagged query_memory as dead_imports + oversize + dead_exports',
    },
    {
        'module': 'cognitive_reactor',
        'question': 'should the reactor fire probes instead of patches when it detects frustration?',
        'candidates': ['keep_patches', 'switch_to_probes', 'hybrid_both'],
        'confidence': 0.30,
        'context': 'operator described intent feedback loop between thought completer and copilot',
    },
    {
        'module': 'entropy_shedding_seq001_v001',
        'question': 'what is the operator target entropy floor — should system optimize for 0.15 or lower?',
        'candidates': ['floor_0.15', 'floor_0.05', 'adaptive_per_module'],
        'confidence': 0.45,
        'context': 'operator asked about near-zero entropy, copilot said 0.15 realistic',
    },
    {
        'module': 'streaming_layer',
        'question': 'should probe cards be added to the dashboard for operator tap-to-answer?',
        'candidates': ['yes_dashboard_cards', 'no_keep_async', 'terminal_prompt_instead'],
        'confidence': 0.25,
        'context': 'operator described live operator sync layer for uncertain queries',
    },
    {
        'module': 'self_fix',
        'question': 'should self-fix autonomous cycle run after every probe resolution or only on commit?',
        'candidates': ['after_probe_resolution', 'on_commit_only', 'periodic_timer'],
        'confidence': 0.50,
        'context': 'operator ran self-fix manually last session, wants autonomous loop',
    },
    {
        'module': 'probe_surface_seq001_v001',
        'question': 'should probes accumulate as a managed block or replace each cycle?',
        'candidates': ['accumulate_with_ttl', 'replace_each_refresh', 'sliding_window_10'],
        'confidence': 0.55,
        'context': 'entropy:shed blocks accumulate, but probes are questions not declarations',
    },
]

# ── PHASE 3: Resolve each probe against live telemetry ───────────
print('\n' + '=' * 60)
print('PHASE 3: Resolution attempts')
print('=' * 60)

resolved_actions = []
needs_operator = []

for i, probe in enumerate(probes, 1):
    result = resolve_probe(root, probe)
    status = 'RESOLVED' if result else 'NEEDS OPERATOR'
    print(f'\n  Probe {i}: [{probe["module"]}] {probe["question"][:60]}...')
    print(f'    candidates: {probe["candidates"]}')
    
    if result:
        print(f'    >> {status} via {result["source"]} (conf={result["confidence"]:.2f})')
        print(f'    >> answer: {result["answer"][:150]}')
        resolved_actions.append({
            'probe': probe,
            'resolution': result,
        })
        # write to real resolution log
        write_resolution(root, probe, result)
    else:
        print(f'    >> {status}')
        needs_operator.append(probe)

# ── PHASE 4: Build action plan from resolutions ──────────────────
print('\n' + '=' * 60)
print('PHASE 4: Auto-generated action plan')
print('=' * 60)

print(f'\n  Resolved: {len(resolved_actions)}/{len(probes)}')
print(f'  Needs operator: {len(needs_operator)}/{len(probes)}')

if resolved_actions:
    print(f'\n  STEERING ACTIONS (from resolved probes):')
    for ra in resolved_actions:
        p = ra['probe']
        r = ra['resolution']
        print(f'    → [{p["module"]}] {r["source"]}: {r["answer"][:120]}')

if needs_operator:
    print(f'\n  QUESTIONS FOR OPERATOR (unresolved):')
    for p in needs_operator:
        print(f'    ? [{p["module"]}] {p["question"]}')
        print(f'      options: {" | ".join(p["candidates"])}')

# ── PHASE 5: Build resolution block for injection ────────────────
print('\n' + '=' * 60)
print('PHASE 5: Generated copilot-instructions block')
print('=' * 60)

block = build_resolution_block(root)
print(block)

print('\n' + '=' * 60)
print('PROBE LOOP COMPLETE')
print('=' * 60)
