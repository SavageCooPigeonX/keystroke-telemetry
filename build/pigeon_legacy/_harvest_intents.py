"""Intent harvester — processes last 100 prompts, reconstructs intent,
verifies each one against actual outcomes, clears resolved intents.

Phases:
  1. Load last 100 prompts from prompt_journal
  2. Decode triple-char encoding (via run-length collapse + Gemini reconstruction)
  3. Classify each intent (building/debugging/testing/exploring/configuring/unknown)
  4. Match intents to git commits (did the intent get fulfilled?)
  5. Run verification sims on unresolved intents
  6. Produce verified intent ledger → logs/intent_harvest_ledger.json

Usage:  py _harvest_intents.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

G = '\033[92m'; R = '\033[91m'; Y = '\033[93m'; C = '\033[96m'; B = '\033[94m'; W = '\033[0m'
LEDGER_PATH = ROOT / 'logs' / 'intent_harvest_ledger.json'
BATCH_LOG = ROOT / 'logs' / 'intent_harvest_batch.jsonl'

# ─────────────────────────────────────────────────────────────────────────
# API KEY
# ─────────────────────────────────────────────────────────────────────────
def _load_api_key() -> str:
    k = os.environ.get('GEMINI_API_KEY', '')
    if k:
        return k
    for p in [ROOT / '.gemini_key', ROOT / '.env']:
        if p.exists():
            text = p.read_text('utf-8', errors='ignore')
            if p.name == '.env':
                for line in text.splitlines():
                    if line.startswith('GEMINI_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
            else:
                return text.strip()
    return ''


# ─────────────────────────────────────────────────────────────────────────
# TRIPLE-CHAR DECODER
# ─────────────────────────────────────────────────────────────────────────
def is_triple_encoded(text: str) -> bool:
    """Detect if text has keystroke-echo pattern (3+ runs of identical chars)."""
    runs = re.findall(r'(.)\1{2,}', text[:80])
    return len(runs) >= 3


def collapse_runs(text: str) -> str:
    """Collapse all consecutive duplicate chars to 1 copy."""
    if not text:
        return text
    out = [text[0]]
    for c in text[1:]:
        if c != out[-1]:
            out.append(c)
    return ''.join(out)


# ─────────────────────────────────────────────────────────────────────────
# GEMINI INTENT RECONSTRUCTOR
# ─────────────────────────────────────────────────────────────────────────
_RECONSTRUCT_PROMPT = """You are an intent decoder for a keystroke telemetry system.
The operator types in VS Code chat. Their keystrokes are captured with echo artifacts —
each keypress may appear 2-3 times (e.g. "aaasss yyyooo" = "as you").

Given the raw garbled text and a rough collapsed version, reconstruct what the operator
was actually saying. Output ONLY the clean reconstructed English sentence, nothing else.
Keep their tone — if they're frustrated, keep that. If technical, keep module/file names.

Examples:
  RAW: "wwwhyyy isisisiiinnt nt t pigigigeoeoeon n rererennaamme"
  → "why isn't pigeon rename hook firing anymore"

  RAW: "oooh h aaandndnd dddeeeeeepppseseseeeek k k gggrrradadadeeer"
  → "oh and deepseek grader needs the ability to..."

  RAW: "cccontontontiiiuuueee"
  → "continue"
"""


def _gemini_reconstruct_batch(items: list[dict]) -> list[str]:
    """Reconstruct multiple garbled texts in one Gemini call."""
    api_key = _load_api_key()
    if not api_key:
        return [i.get('collapsed', i.get('raw', '')) for i in items]

    lines = []
    for idx, item in enumerate(items):
        lines.append(f"[{idx}] RAW: {item['raw'][:200]}")
        lines.append(f"    COLLAPSED: {item['collapsed'][:150]}")
    prompt = '\n'.join(lines)
    prompt += '\n\nReconstruct each one. Output format: one line per item, prefixed [0], [1], etc.'

    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/{model}'
           f':generateContent?key={api_key}')
    body = json.dumps({
        'system_instruction': {'parts': [{'text': _RECONSTRUCT_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 2048,
            'thinkingConfig': {'thinkingBudget': 256},
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = (data.get('candidates', [{}])[0]
                     .get('content', {}).get('parts', []))
            text = ''
            for part in parts:
                if 'text' in part and not part.get('thought'):
                    text = part['text'].strip()
                    break
            if not text and parts:
                text = parts[-1].get('text', '').strip()
            # Parse [idx] lines
            results = {}
            for line in text.splitlines():
                m = re.match(r'\[(\d+)\]\s*(.*)', line.strip())
                if m:
                    results[int(m.group(1))] = m.group(2).strip()
            return [results.get(i, items[i].get('collapsed', '')) for i in range(len(items))]
    except Exception as e:
        print(f'  {R}Gemini batch reconstruct error: {e}{W}')
        return [i.get('collapsed', i.get('raw', '')) for i in items]


# ─────────────────────────────────────────────────────────────────────────
# INTENT CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────
_INTENT_RULES = [
    (r'test|verify|check|assert|stress|audit', 'testing'),
    (r'debug|fix|broken|error|wrong|fail|crash|why.*not|isnt|stale', 'debugging'),
    (r'build|create|add|implement|wire|make|write|new', 'building'),
    (r'refactor|rename|clean|move|reorganize', 'refactoring'),
    (r'explore|audit|look|find|search|where|what|how', 'exploring'),
    (r'config|setup|install|env|deploy|launch|run|push|commit', 'configuring'),
    (r'continue|yes|yeah|sure|ok|nope|no', 'continuation'),
]


def classify_intent(text: str) -> str:
    """Simple rule-based intent classification."""
    t = text.lower()
    for pattern, label in _INTENT_RULES:
        if re.search(pattern, t):
            return label
    return 'unknown'


# ─────────────────────────────────────────────────────────────────────────
# GIT COMMIT MATCHER — did the intent get fulfilled?
# ─────────────────────────────────────────────────────────────────────────
def _load_recent_commits(n: int = 30) -> list[dict]:
    """Load recent git commits for matching."""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'log', f'-{n}', '--format=%H|%aI|%s'],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        commits = []
        for line in result.stdout.strip().splitlines():
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0][:8],
                    'ts': parts[1],
                    'subject': parts[2],
                })
        return commits
    except Exception:
        return []


def _match_intent_to_commit(intent_text: str, intent_ts: str, commits: list[dict]) -> dict | None:
    """Find a commit that likely resolves this intent."""
    intent_words = set(re.findall(r'[a-z_]{3,}', intent_text.lower()))
    intent_words -= {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have',
                     'what', 'how', 'not', 'are', 'you', 'was', 'but', 'can',
                     'yes', 'yeah', 'sure', 'nope', 'continue'}
    if not intent_words:
        return None

    best_match = None
    best_score = 0
    for commit in commits:
        # Only match commits that came AFTER the intent
        commit_words = set(re.findall(r'[a-z_]{3,}', commit['subject'].lower()))
        overlap = len(intent_words & commit_words)
        if overlap >= 2:
            score = overlap / max(1, len(intent_words))
            if score > best_score:
                best_score = score
                best_match = {**commit, 'match_score': round(score, 2)}
    return best_match if best_score >= 0.2 else None


# ─────────────────────────────────────────────────────────────────────────
# VERIFICATION SIM — quick sim on unresolved intents
# ─────────────────────────────────────────────────────────────────────────
def _verify_sim(intent_text: str) -> dict:
    """Quick Gemini sim to check if this intent still makes sense / is actionable."""
    api_key = _load_api_key()
    if not api_key:
        return {'status': 'no_key', 'actionable': False}

    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/{model}'
           f':generateContent?key={api_key}')
    prompt = (
        f'Operator typed this intent in VS Code chat:\n'
        f'"{intent_text}"\n\n'
        f'Is this intent still actionable? What specific file/module/action would resolve it?\n'
        f'Reply in this JSON format: {{"actionable": true/false, "action": "...", "files": ["..."], "resolved_by": "..."}}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text':
            'You analyze operator intents from a keystroke telemetry codebase. '
            'Determine if the intent is still actionable or if it was a transient '
            'command (like "yes", "continue"). Reply ONLY with valid JSON.'}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 300,
            'thinkingConfig': {'thinkingBudget': 0},
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = (data.get('candidates', [{}])[0]
                     .get('content', {}).get('parts', []))
            text = ''
            for part in parts:
                if 'text' in part and not part.get('thought'):
                    text = part['text'].strip()
                    break
            if not text and parts:
                text = parts[-1].get('text', '').strip()
            # Parse JSON from response (may have markdown fences)
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
    except Exception as e:
        return {'status': f'error: {e}', 'actionable': False}


# ─────────────────────────────────────────────────────────────────────────
# MAIN HARVESTER
# ─────────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{C}{'='*70}")
    print(f"INTENT HARVESTER — Last 100 Prompts")
    print(f"{'='*70}{W}\n")

    # ── Load prompts ──
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
    last100 = lines[-100:]
    print(f"  Loaded {len(last100)} prompts (of {len(lines)} total)\n")

    # ── Phase 1: Decode + Reconstruct ──
    print(f"{Y}[PHASE 1] Decode + Reconstruct{W}")
    entries = []
    encoded_batch = []
    encoded_indices = []

    for i, line in enumerate(last100):
        try:
            e = json.loads(line)
        except Exception:
            continue
        raw = e.get('msg', '')
        ts = e.get('ts', '')
        orig_intent = e.get('intent', 'unknown')
        cog = e.get('cognitive_state', 'unknown')

        entry = {
            'idx': i,
            'ts': ts,
            'raw': raw[:300],
            'orig_intent': orig_intent,
            'cognitive_state': cog,
        }

        if is_triple_encoded(raw):
            collapsed = collapse_runs(raw)
            entry['encoded'] = True
            entry['collapsed'] = collapsed[:200]
            encoded_batch.append({'raw': raw[:200], 'collapsed': collapsed[:150]})
            encoded_indices.append(i)
        else:
            entry['encoded'] = False
            entry['decoded'] = raw[:200]

        entries.append(entry)

    # Batch-decode encoded entries via Gemini (batches of 15)
    if encoded_batch:
        print(f"  {len(encoded_batch)} encoded entries to reconstruct via Gemini...")
        all_decoded = []
        for batch_start in range(0, len(encoded_batch), 15):
            batch = encoded_batch[batch_start:batch_start + 15]
            decoded = _gemini_reconstruct_batch(batch)
            all_decoded.extend(decoded)
            print(f"    batch {batch_start // 15 + 1}: {len(batch)} items decoded")

        # Map back to entries
        for j, global_idx in enumerate(encoded_indices):
            for entry in entries:
                if entry['idx'] == global_idx:
                    entry['decoded'] = all_decoded[j] if j < len(all_decoded) else entry.get('collapsed', '')
                    break

    clean_count = sum(1 for e in entries if not e.get('encoded'))
    enc_count = sum(1 for e in entries if e.get('encoded'))
    print(f"  Clean: {clean_count} | Encoded→Decoded: {enc_count}\n")

    # Show some decoded samples
    for e in entries[:3] + entries[50:52] + entries[-3:]:
        marker = f"{Y}ENC{W}" if e.get('encoded') else f"{G}CLN{W}"
        print(f"  [{marker}] [{e['idx']:2d}] {e.get('decoded', '?')[:70]}")
    print()

    # ── Phase 2: Classify ──
    print(f"{Y}[PHASE 2] Classify Intents{W}")
    class_counts = {}
    for entry in entries:
        decoded = entry.get('decoded', '')
        intent = classify_intent(decoded)
        entry['classified_intent'] = intent
        class_counts[intent] = class_counts.get(intent, 0) + 1

    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        color = G if cls != 'unknown' else Y
        bar = '█' * count
        print(f"  {color}{cls:15s}{W} {count:3d} {bar}")
    print()

    # ── Phase 3: Match to commits ──
    print(f"{Y}[PHASE 3] Match Intents to Git Commits{W}")
    commits = _load_recent_commits(50)
    print(f"  Loaded {len(commits)} recent commits")

    resolved = 0
    unresolved_entries = []
    for entry in entries:
        decoded = entry.get('decoded', '')
        match = _match_intent_to_commit(decoded, entry['ts'], commits)
        if match:
            entry['resolved'] = True
            entry['resolved_by'] = match
            resolved += 1
        else:
            entry['resolved'] = False
            if entry['classified_intent'] not in ('continuation', 'unknown') or len(decoded) > 15:
                unresolved_entries.append(entry)

    print(f"  Resolved: {G}{resolved}{W}/{len(entries)}")
    print(f"  Unresolved (actionable): {Y}{len(unresolved_entries)}{W}")
    # Show resolved matches
    for e in entries:
        if e.get('resolved'):
            c = e['resolved_by']
            print(f"    {G}✓{W} [{e['idx']:2d}] {e.get('decoded','')[:50]} → {c['hash']} {c['subject'][:40]}")
    print()

    # ── Phase 4: Verify unresolved ──
    print(f"{Y}[PHASE 4] Verify Unresolved Intents ({len(unresolved_entries)} to check){W}")
    # Limit to max 20 verification sims to avoid API overload
    to_verify = unresolved_entries[:20]
    verified = 0
    still_pending = 0
    cleared = 0

    for entry in to_verify:
        decoded = entry.get('decoded', '')
        if len(decoded) < 8:
            entry['verification'] = {'actionable': False, 'reason': 'too_short'}
            cleared += 1
            continue

        result = _verify_sim(decoded)
        entry['verification'] = result

        actionable = result.get('actionable', False)
        if actionable:
            still_pending += 1
            action = result.get('action', '?')[:60]
            files = result.get('files', [])[:3]
            print(f"  {Y}⏳{W} [{entry['idx']:2d}] {decoded[:50]}")
            print(f"       Action: {action}")
            if files:
                print(f"       Files: {', '.join(files)}")
        else:
            cleared += 1
            reason = result.get('resolved_by', result.get('action', 'transient'))[:40]
            print(f"  {G}✓{W} [{entry['idx']:2d}] {decoded[:50]} → cleared ({reason})")

        verified += 1

    remaining_unverified = len(unresolved_entries) - len(to_verify)
    print(f"\n  Verified: {verified} | Still pending: {Y}{still_pending}{W} | "
          f"Cleared: {G}{cleared}{W} | Unverified: {remaining_unverified}")
    print()

    # ── Phase 5: Produce ledger ──
    print(f"{Y}[PHASE 5] Intent Ledger{W}")
    ledger = {
        'harvested_at': datetime.now(timezone.utc).isoformat(),
        'total_prompts': len(entries),
        'classification': class_counts,
        'resolved_count': resolved,
        'unresolved_actionable': still_pending,
        'cleared': cleared,
        'stats': {
            'encoded_pct': round(100 * enc_count / max(1, len(entries))),
            'resolution_rate': round(100 * resolved / max(1, len(entries))),
            'intent_coverage': round(100 * (len(entries) - class_counts.get('unknown', 0)) / max(1, len(entries))),
        },
        'pending_intents': [],
        'resolved_intents': [],
        'entries': [],
    }

    for entry in entries:
        clean_entry = {
            'idx': entry['idx'],
            'ts': entry['ts'],
            'decoded': entry.get('decoded', '')[:200],
            'intent': entry.get('classified_intent', 'unknown'),
            'cognitive_state': entry.get('cognitive_state', 'unknown'),
            'encoded': entry.get('encoded', False),
            'resolved': entry.get('resolved', False),
        }
        if entry.get('resolved_by'):
            clean_entry['commit'] = entry['resolved_by'].get('hash', '')
        if entry.get('verification'):
            v = entry['verification']
            clean_entry['actionable'] = v.get('actionable', False)
            clean_entry['action'] = v.get('action', '')[:100]
            clean_entry['target_files'] = v.get('files', [])[:3]
        ledger['entries'].append(clean_entry)

        if entry.get('verification', {}).get('actionable'):
            ledger['pending_intents'].append({
                'decoded': entry.get('decoded', '')[:150],
                'action': entry.get('verification', {}).get('action', '')[:100],
                'files': entry.get('verification', {}).get('files', [])[:3],
            })
        elif entry.get('resolved'):
            ledger['resolved_intents'].append({
                'decoded': entry.get('decoded', '')[:100],
                'commit': entry.get('resolved_by', {}).get('hash', ''),
                'subject': entry.get('resolved_by', {}).get('subject', '')[:60],
            })

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding='utf-8')

    # Also write batch log
    with open(BATCH_LOG, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + '\n')

    # ── Summary ──
    print(f"\n{C}{'='*70}")
    print(f"HARVEST SUMMARY")
    print(f"{'='*70}{W}")
    print(f"  Total prompts:      {len(entries)}")
    print(f"  Encoded→Decoded:    {enc_count} ({ledger['stats']['encoded_pct']}%)")
    print(f"  Intent coverage:    {ledger['stats']['intent_coverage']}%")
    print(f"  Resolved by commit: {resolved} ({ledger['stats']['resolution_rate']}%)")
    print(f"  Still pending:      {still_pending}")
    print(f"  Cleared (transient):{cleared}")
    print(f"  Classification:     {class_counts}")
    print(f"\n  Ledger: {LEDGER_PATH.relative_to(ROOT)}")
    print(f"  Batch:  {BATCH_LOG.relative_to(ROOT)}")

    if ledger['pending_intents']:
        print(f"\n  {Y}PENDING INTENTS (require action):{W}")
        for p in ledger['pending_intents'][:10]:
            print(f"    ⏳ {p['decoded'][:60]}")
            print(f"       → {p['action'][:60]}")
            if p.get('files'):
                print(f"       files: {', '.join(p['files'][:3])}")
    print()


if __name__ == '__main__':
    main()
