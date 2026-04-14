"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_edit_events_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 37 lines | ~321 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_edit_events(root: Path) -> list[dict]:
    """Load Copilot edit events from edit_pairs.jsonl only.

    This is the edit-only ground truth: prompt-linked file mutations harvested
    from telemetry pulses. No response-text heuristics.
    """
    ep = root / 'logs' / 'edit_pairs.jsonl'
    if not ep.exists():
        return []

    events = []
    for line in ep.read_text('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        raw_file = entry.get('file', '')
        if not raw_file:
            continue
        events.append({
            'file': raw_file,
            'module': _module_key(raw_file),
            'region': _region_from_path(raw_file),
            'edit_ts': entry.get('edit_ts') or entry.get('ts', ''),
            'latency_ms': max(0, int(entry.get('latency_ms', 0) or 0)),
            'edit_why': (entry.get('edit_why') or 'auto').strip(),
            'state': (entry.get('state') or 'unknown').strip(),
        })
    return events
