"""Resolve a single probe inline — test the feedback loop."""
import json, sys
from pathlib import Path
sys.path.insert(0, '.')
from src.probe_resolver_seq001_v001_seq001_v001 import resolve_probe

root = Path('.')
probe = {
    'module': 'query_memory',
    'question': 'should query_memory be fixed by wiring decomposed sub-file imports or collapsed back to a clean monolith',
    'candidates': 'fix_decomposition | collapse_to_monolith',
    'confidence': '0.45',
    'context': 'decomposed files lost internal dependencies, main file has duplicate definitions'
}
result = resolve_probe(root, probe)
if result:
    print(f"RESOLVED via {result['source']} (conf={result['confidence']})")
    print(f"Answer: {result['answer']}")
else:
    print("NEEDS OPERATOR — no signal in telemetry")
    # Check what's in prompt journal for related keywords
    pj = root / 'logs' / 'prompt_journal.jsonl'
    if pj.exists():
        lines = pj.read_text(encoding='utf-8').strip().split('\n')[-50:]
        hits = []
        for line in lines:
            try:
                entry = json.loads(line)
                msg = entry.get('msg', '').lower()
                if any(kw in msg for kw in ['split', 'monolith', 'decompos', 'collapse', 'wire', 'query_memory', 'clot']):
                    hits.append(entry.get('msg', '')[:120])
            except:
                pass
        if hits:
            print(f"Related prompt mentions ({len(hits)}):")
            for h in hits:
                print(f"  > {h}")
        else:
            print("No related keywords in last 50 prompts")

    # Also check unsaid for related signal
    unsaid = root / 'logs' / 'unsaid_reconstructions.jsonl'
    if unsaid.exists():
        lines = unsaid.read_text(encoding='utf-8').strip().split('\n')[-30:]
        hits2 = []
        for line in lines:
            try:
                entry = json.loads(line)
                deleted = ' '.join(entry.get('deleted_fragments', []))
                intent = entry.get('reconstructed_intent', '')
                combined = (deleted + ' ' + intent).lower()
                if any(kw in combined for kw in ['split', 'decompos', 'monolith', 'wire', 'fix', 'collapse', 'pigeon']):
                    hits2.append(intent[:120] if intent else deleted[:120])
            except:
                pass
        if hits2:
            print(f"\nRelated unsaid threads ({len(hits2)}):")
            for h in hits2:
                print(f"  > {h}")

# Second probe — about the broader approach
probe2 = {
    'module': 'probe_resolver_seq001_v001',
    'question': 'the resolver only resolved 1 of 7 probes - is the operator satisfied with keyword matching or wants semantic similarity',
    'candidates': 'keyword_matching_ok | need_semantic | need_more_signals',
    'confidence': '0.30',
}
result2 = resolve_probe(root, probe2)
if result2:
    print(f"\nProbe 2 RESOLVED via {result2['source']} (conf={result2['confidence']})")
    print(f"Answer: {result2['answer']}")
else:
    print("\nProbe 2: NEEDS OPERATOR — no signal about resolver quality preferences")

# Third probe — what should I actually work on
probe3 = {
    'module': 'self_fix',
    'question': 'the codebase has 97 over-cap files and 4 clots - should autonomous work prioritize over-cap splits or clot removal',
    'candidates': 'over_cap_splits | clot_removal | fix_broken_decompositions',
    'confidence': '0.40',
}
result3 = resolve_probe(root, probe3)
if result3:
    print(f"\nProbe 3 RESOLVED via {result3['source']} (conf={result3['confidence']})")
    print(f"Answer: {result3['answer']}")
else:
    print("\nProbe 3: NEEDS OPERATOR — no clear signal on work priority")
    # Check if organism health has a directive
    pj = root / 'logs' / 'prompt_journal.jsonl'
    if pj.exists():
        lines = pj.read_text(encoding='utf-8').strip().split('\n')[-50:]
        for line in lines:
            try:
                entry = json.loads(line)
                msg = entry.get('msg', '').lower()
                if any(kw in msg for kw in ['priority', 'over-cap', 'clot', 'split', 'fix first']):
                    print(f"  hint: {entry.get('msg', '')[:120]}")
            except:
                pass
