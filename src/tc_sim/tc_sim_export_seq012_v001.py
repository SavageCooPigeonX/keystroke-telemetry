"""tc_sim_export_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 26 lines | ~263 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import os
import re

def export_results(results: list[SimResult], path: Path):
    """Export sim results to JSONL for analysis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for r in results:
            entry = {
                'buffer': r.pause.buffer,
                'prediction': r.prediction,
                'actual': r.continuation_captured,
                'word_overlap': r.word_overlap,
                'prefix_match': r.prefix_match_len,
                'exact': r.exact_match,
                'latency_ms': r.latency_ms,
                'pause_ms': r.pause.pause_ms,
                'position_pct': r.pause.position_pct,
                'context_files': r.context_files,
                'final_text': r.pause.final_text[:200],
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f'\nexported {len(results)} results to {path}')
