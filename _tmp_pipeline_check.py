"""Quick diagnostic: check if composition pipeline is live."""
import json
from pathlib import Path

root = Path('.')

# 1. Check composition data
comp = root / 'logs' / 'chat_compositions.jsonl'
if comp.exists():
    lines = comp.read_text('utf-8', errors='ignore').strip().splitlines()
    print(f'=== chat_compositions.jsonl: {len(lines)} entries ===')
    for line in lines[-5:]:
        try:
            d = json.loads(line)
            ts = str(d.get('ts', '?'))[:19]
            keys = d.get('total_keystrokes', 0)
            dels = d.get('deletion_ratio', 0)
            dw = d.get('deleted_words', [])
            rw = d.get('rewrites', [])
            print(f'  {ts} | keys={keys} del={dels:.3f} | deleted_words={dw[:3]} | rewrites={len(rw)}')
        except:
            pass
else:
    print('NO chat_compositions.jsonl')

print()

# 2. Check composition_recon
recon = root / 'logs' / 'composition_recon.jsonl'
if recon.exists():
    lines = recon.read_text('utf-8', errors='ignore').strip().splitlines()
    print(f'=== composition_recon.jsonl: {len(lines)} entries ===')
    for line in lines[-5:]:
        try:
            d = json.loads(line)
            ts = str(d.get('ts', '?'))[:19]
            matched = d.get('matched', False)
            dw = d.get('deleted_words', [])
            print(f'  {ts} | matched={matched} | deleted_words={dw[:3]}')
        except:
            pass
else:
    print('NO composition_recon.jsonl')

print()

# 3. Check vscdb freshness (composition source)
vscdb_state = root / 'logs' / 'vscdb_state.json'
if vscdb_state.exists():
    d = json.loads(vscdb_state.read_text('utf-8'))
    print(f'=== vscdb_state.json ===')
    print(f'  last_poll: {d.get("last_poll", "?")}')
    print(f'  db_path: {str(d.get("db_path", "?"))[:60]}')
else:
    print('NO vscdb_state.json')

print()

# 4. Check enricher status
enricher_errors = root / 'logs' / 'enricher_errors.jsonl'
if enricher_errors.exists():
    lines = enricher_errors.read_text('utf-8', errors='ignore').strip().splitlines()
    print(f'=== enricher_errors.jsonl: {len(lines)} errors ===')
    # last error
    if lines:
        last = json.loads(lines[-1])
        print(f'  LAST ERROR: {last.get("ts", "?")} — {last.get("error", "?")}')
else:
    print('NO enricher_errors.jsonl')

print()

# 5. Check prompt_telemetry age
pt = root / 'logs' / 'prompt_telemetry_latest.json'
if pt.exists():
    d = json.loads(pt.read_text('utf-8'))
    lp = d.get('latest_prompt', {})
    ts = lp.get('ts', '?')
    sn = lp.get('session_n', 0)
    sig = d.get('signals', {})
    dw = d.get('deleted_words', [])
    rw = d.get('rewrites', [])
    cb = d.get('composition_binding', {})
    print(f'=== prompt_telemetry_latest.json ===')
    print(f'  session_n: {sn}')
    print(f'  ts: {ts}')
    print(f'  signals: {sig}')
    print(f'  deleted_words: {dw}')
    print(f'  rewrites: {rw}')
    print(f'  binding matched: {cb.get("matched")}')
    print(f'  binding age_ms: {cb.get("age_ms")}')

print()

# 6. Check if the enricher module exists and has current API
print('=== enricher module check ===')
try:
    import importlib, glob
    enricher_files = glob.glob('src/*enricher*')
    print(f'  enricher files: {enricher_files}')
    for ef in enricher_files:
        print(f'  checking: {ef}')
except Exception as e:
    print(f'  error: {e}')

# 7. Check copilot-instructions.md block freshness
ci = root / '.github' / 'copilot-instructions.md'
if ci.exists():
    text = ci.read_text('utf-8', errors='ignore')
    # find current-query block timestamp
    import re
    m = re.search(r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', text)
    if m:
        print(f'\n=== copilot-instructions.md current-query freshness ===')
        print(f'  enriched at: {m.group(1)} UTC')
    # find prompt-telemetry block
    m2 = re.search(r'"updated_at":\s*"([^"]+)"', text)
    if m2:
        print(f'  prompt_telemetry updated: {m2.group(1)[:19]}')
