"""git_plugin_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
import os
import re

def _registry_churn(registry: dict, top_n: int = 8) -> list[dict]:
    """Return top_n most-versioned modules — these are the pain points."""
    entries = list(registry.values())
    entries.sort(key=lambda e: e.get('ver', 1), reverse=True)
    return [
        {'module': e['name'], 'seq': e.get('seq'), 'ver': e.get('ver', 1),
         'tokens': e.get('tokens', 0), 'desc': e.get('desc', ''), 'intent': e.get('intent', '')}
        for e in entries[:top_n]
    ]
