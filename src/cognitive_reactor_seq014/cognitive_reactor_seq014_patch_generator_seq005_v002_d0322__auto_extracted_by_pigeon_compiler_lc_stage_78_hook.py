"""cognitive_reactor_seq014_patch_generator_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v002 | 94 lines | ~781 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import json
import os
import re
import urllib.request

def _generate_patch(
    module_key: str,
    avg_hes: float,
    dominant_state: str,
    streak_count: int,
    problems: list,
    cross_context: dict,
    source_snippet: str,
    registry_entry: dict | None,
) -> str | None:
    """DeepSeek call: generate a targeted fix based on cognitive load data."""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return None

    prob_block = '\n'.join(
        f'- [{p["severity"]}] {p["type"]}: {p.get("fix","")}'
        for p in problems[:5]
    ) or 'No static problems detected.'

    cross_block = ''
    for rel, ctx in cross_context.items():
        if module_key in rel:
            deps = ', '.join(Path(d).stem.split('_seq')[0]
                             for d in ctx.get('imports_from', []))
            users = ', '.join(Path(u).stem.split('_seq')[0]
                              for u in ctx.get('imported_by', []))
            if deps:
                cross_block += f'Imports from: {deps}\n'
            if users:
                cross_block += f'Used by: {users}\n'

    ver = registry_entry.get('ver', '?') if registry_entry else '?'
    tokens = registry_entry.get('tokens', '?') if registry_entry else '?'

    prompt = f"""You are an autonomous code reactor. An operator has been struggling with module `{module_key}` for {streak_count} consecutive typing sessions.

COGNITIVE DATA:
- Average hesitation: {avg_hes} (threshold: {HESITATION_THRESHOLD})
- Dominant state: {dominant_state}
- Module version: v{ver}, ~{tokens} tokens

STATIC ANALYSIS PROBLEMS:
{prob_block}

CROSS-FILE DEPENDENCIES:
{cross_block or 'None detected.'}

SOURCE (first 80 lines):
```python
{source_snippet[:2000]}
```

Generate a COGNITIVE PATCH — specific code changes that would reduce the operator's cognitive load on this module. Focus on:
1. Simplifying the interface (fewer params, clearer names)
2. Breaking apart complex logic the operator keeps re-reading
3. Adding inline comments at hesitation hotspots
4. Fixing any detected static problems

Output format:
- Brief diagnosis (2 sentences: why this module causes cognitive load)
- Concrete code changes as unified diff or replacement blocks
- One sentence: what this patch prevents in future sessions

Max 300 words. Be surgical."""

    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.3,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None
