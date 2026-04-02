"""u_pe_s024_v002_d0402_λC_enricher_core_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from src._resolve import src_import
import json
import os
import re
import urllib.request

def enrich_prompt(root: Path, raw_query: str,
                  deleted_words: list | None = None,
                  cognitive_state: dict | None = None) -> str:
    """Call DeepSeek to enrich a raw prompt. Returns the enriched interpretation text."""
    root = Path(root)

    # Route memory shards
    shard_text = ''
    try:
        route_context, format_shard_context = src_import("context_router_seq027", "route_context", "format_shard_context")
        routed = route_context(root, raw_query)
        shard_text = format_shard_context(routed, root=root)
    except Exception:
        pass

    context = {
        'hot_files':          _hot_files(root),
        'rework_history':     _rework_for_query(root, raw_query),
        'past_attempts':      _recent_ai_attempts(root, raw_query),
        'deleted_words':      deleted_words or _deleted_words_from_journal(root),
        'cognitive_state':    cognitive_state or _cognitive_state(root),
        'registry_hits':      _registry_touches(root, raw_query),
        'journal_trajectory': _recent_journal_context(root),
        'shard_context':      shard_text,
    }

    ds_prompt = _build_deepseek_prompt(raw_query, context)

    # Load API key from .env
    api_key = None
    env_path = root / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return ''

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text':
            'You are a concise developer context interpreter. Output only the structured block, no prose.'}]},
        'contents': [{'parts': [{'text': ds_prompt}]}],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 2048,
            'thinkingConfig': {'thinkingBudget': 256},
        },
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        return f'(enrichment unavailable: {e})'
