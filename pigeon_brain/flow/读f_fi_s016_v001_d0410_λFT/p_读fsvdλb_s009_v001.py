"""读f_fi_s016_v001_d0410_λFT_briefing_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 19 lines | ~246 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, os, re, hashlib, urllib.request, urllib.error

def print_agent_briefing(root: Path, node_name: str) -> None:
    u = get_file_understanding(root, node_name)
    if not u:
        print(f"No understanding for '{node_name}' — run interrogate_file() first.")
        return
    print(f"\n{'='*60}")
    print(f"AGENT BRIEFING: {node_name}")
    print(f"{'='*60}")
    print(f"Intent:     {u.get('intent','?')}")
    print(f"Critical:   {u.get('critical_path','?')}")
    print(f"Fix:       ", "\n            ".join(u.get('what_to_fix', ['?'])))
    print(f"Break risk:", "\n            ".join(u.get('break_risk', ['?'])))
    print(f"\nDIRECTIVE:  {u.get('autonomous_directive','?')}")
    print(f"Why:        {u.get('reasoning','?')}")
    print(f"\nModel: {u.get('model','?')} | Hash: {u.get('source_hash','?')} | At: {u.get('interrogated_at','?')[:19]}")
