"""module_identity_diagnose_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _diagnose_patterns(name: str, entry: dict, lk: dict, memory: dict) -> list[str]:
    """Self-diagnose recurring issues by comparing current state to memory."""
    diags = []
    bugs_now = set(entry.get('bug_keys', []))
    bugs_prev = set(memory.get('last_bugs', []))

    # Bug recurrence
    recurring = bugs_now & bugs_prev
    if recurring:
        diags.append(f'recurring bugs across passes: {", ".join(recurring)}')

    new_bugs = bugs_now - bugs_prev
    if new_bugs:
        diags.append(f'new since last pass: {", ".join(new_bugs)}')

    fixed = bugs_prev - bugs_now
    if fixed:
        diags.append(f'fixed since last: {", ".join(fixed)}')

    # Token growth
    prev_tokens = memory.get('last_tokens', 0)
    curr_tokens = entry.get('tokens', 0)
    if prev_tokens and curr_tokens > prev_tokens * 1.2:
        diags.append(f'growing: {prev_tokens}→{curr_tokens} tokens (+{curr_tokens - prev_tokens})')

    # Death recurrence
    resolve = lk.get('_resolve', lambda x: x)
    alias = resolve(name)
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    if len(deaths) >= 2:
        causes = [d['cause'] for d in deaths]
        from collections import Counter
        top = Counter(causes).most_common(1)
        if top and top[0][1] >= 2:
            diags.append(f'keeps dying from: {top[0][0]} ({top[0][1]}x)')

    return diags
