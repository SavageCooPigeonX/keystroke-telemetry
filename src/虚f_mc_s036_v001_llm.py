"""虚f_mc LLM layer — prompt building, Gemini calls, response parsing."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 15


def get_api_key(root: Path) -> str | None:
    env_path = root / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


def build_void_prompt(module_name: str, profile: dict) -> str:
    source = profile.get('source', '(source not found)')
    ver = profile.get('version', '?')
    tokens = profile.get('tokens', '?')
    arch = profile.get('archetype', 'unknown')
    hes = profile.get('hesitation', 0)

    partners_str = '\n'.join(
        f"  - {p['name']} (coupling={p.get('score', 0)}, {p.get('reason', '')})"
        for p in profile.get('partners', [])
    ) or '  (no known coupling partners)'

    fears_str = ', '.join(profile.get('fears', [])) or 'none declared'
    bugs_str = ', '.join(profile.get('current_bugs', [])) or 'none'

    chronic_str = '\n'.join(
        f"  - {b['type']} (appeared {b['appearances']}/{b.get('last_report', '?')} reports, status={b['status']})"
        for b in profile.get('chronic_bugs', [])
    ) or '  (no chronic bugs)'

    entropy = profile.get('entropy', 'not tracked')
    emotion = profile.get('emotion', 'unknown')
    pass_count = profile.get('pass_count', 0)

    bug_hist = profile.get('bug_history', [])
    bug_hist_str = ' → '.join(str(b) if b else '[]' for b in bug_hist) or 'no history'

    return f"""You are {module_name}. You are a Python module in a living codebase organism.

Here is your source code:
```python
{source}
```

YOUR IDENTITY:
- Version: v{ver} | Tokens: {tokens} | Archetype: {arch} | Emotion: {emotion}
- Seen in {pass_count} audit passes
- Operator hesitation on you: {hes} (0=easy, 1=maximum struggle)

YOUR COUPLING PARTNERS:
{partners_str}

YOUR FEARS: {fears_str}

YOUR CURRENT BUGS: {bugs_str}
YOUR CHRONIC BUG HISTORY:
{chronic_str}

YOUR BUG HISTORY (last 5 passes): {bug_hist_str}

YOUR ENTROPY: {entropy}

Based on YOUR code and YOUR dependencies and YOUR history:
What CONTEXT are you missing to do your job properly?

Think about:
- What data do you need that you don't have access to?
- What events from other modules should you subscribe to but don't?
- What interface contracts are unclear between you and your partners?
- What knowledge about yourself (your own behavior, your own failure modes) is missing?

Format EACH missing context as a JSON object in a JSON array:
```json
[
  {{
    "what": "short description of missing context",
    "why": "why you need it - what breaks or degrades without it",
    "who_has_it": "module name that probably has this data",
    "confidence": 0.0-1.0,
    "type": "integration_gap|interface_gap|data_gap|self_knowledge_gap"
  }}
]
```

Return ONLY the JSON array. No preamble. 2-5 items max. Be specific — cite actual function names, actual import paths, actual data formats when you can."""


def call_gemini(api_key: str, prompt: str) -> str:
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text':
            'You are a code module performing self-analysis. '
            'You speak as the module itself — first person. '
            'Output ONLY valid JSON. No markdown fences in output.'}]},
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.3,
            'maxOutputTokens': 1024,
            'thinkingConfig': {'thinkingBudget': 512},
        },
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
    for part in reversed(parts):
        if 'text' in part:
            return part['text'].strip()
    return ''


def parse_blocks(raw: str) -> list[dict]:
    cleaned = re.sub(r'```json\s*', '', raw)
    cleaned = re.sub(r'```\s*$', '', cleaned).strip()
    try:
        blocks = json.loads(cleaned)
        if isinstance(blocks, list):
            valid = []
            for b in blocks:
                if isinstance(b, dict) and 'what' in b:
                    valid.append({
                        'what': str(b.get('what', '')),
                        'why': str(b.get('why', '')),
                        'who_has_it': str(b.get('who_has_it', '')),
                        'confidence': min(1.0, max(0.0, float(b.get('confidence', 0.5)))),
                        'type': str(b.get('type', 'unknown')),
                    })
            return valid
    except (json.JSONDecodeError, ValueError):
        pass
    return []
