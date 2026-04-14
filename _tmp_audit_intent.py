"""Audit task queue for reward hacking patterns."""
import json

tq = json.loads(open('task_queue.json', 'r', encoding='utf-8').read())
tasks = tq.get('tasks', [])

done = [t for t in tasks if t.get('status') == 'done']
pending = [t for t in tasks if t.get('status') == 'pending']
verify = [t for t in tasks if t.get('stage') == 'verify']

print(f'Total: {len(tasks)} | Done: {len(done)} | Pending: {len(pending)} | Verify stage: {len(verify)}')
print()

# Check for weak verifications (potential reward hacking)
print("=== REWARD HACKING AUDIT ===\n")

# Pattern 1: captured_gap with short summary
print("1. Captured gaps (should have real summaries):")
for t in done:
    reason = t.get('verification_reason', '')
    summary = t.get('verification_summary', '')
    if reason == 'captured_gap':
        if len(summary) < 50:
            print(f"   [WEAK] {t['id']}: short summary ({len(summary)} chars)")
        else:
            print(f"   [OK] {t['id']}: {summary[:60]}...")

print()

# Pattern 2: satisfied without evidence
print("2. Satisfied outcomes (should have evidence files):")
for t in done:
    reason = t.get('verification_reason', '')
    if reason == 'satisfied':
        evidence = t.get('evidence', [])
        if not evidence:
            print(f"   [WEAK] {t['id']}: no evidence files")
        else:
            print(f"   [OK] {t['id']}: {len(evidence)} evidence files")

print()

# Pattern 3: Unresolved intents sitting too long
print("3. Unresolved intents (potential abandoned work):")
for t in tasks:
    if t.get('stage') in ('pending', 'verify'):
        title = t.get('title', '')[:55]
        conf = t.get('confidence', 0)
        print(f"   {t['id']}: {title}... (conf={conf:.2f})")

print()

# Pattern 4: Check for suspiciously fast resolutions
print("4. Resolution timing (fast resolutions may be rubber-stamped):")
from datetime import datetime
for t in done[-5:]:  # last 5 completed
    created = t.get('created_ts', '')
    completed = t.get('completed_ts', '')
    if created and completed:
        try:
            c = datetime.fromisoformat(created.replace('Z', '+00:00'))
            d = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            delta = (d - c).total_seconds()
            if delta < 60:
                print(f"   [FAST] {t['id']}: resolved in {delta:.0f}s")
            else:
                print(f"   [OK] {t['id']}: resolved in {delta/60:.1f}min")
        except:
            print(f"   [?] {t['id']}: couldn't parse timestamps")

print("\nAudit complete.")
