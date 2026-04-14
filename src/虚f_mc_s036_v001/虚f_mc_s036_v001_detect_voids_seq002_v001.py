"""虚f_mc_s036_v001_detect_voids_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 31 lines | ~334 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import defaultdict

def _detect_voids(all_blocks: dict[str, list[dict]]) -> list[dict]:
    source_requests: dict[str, list[dict]] = defaultdict(list)
    for file_name, blocks in all_blocks.items():
        for b in blocks:
            who = b.get('who_has_it', '').strip()
            if who:
                source_requests[who].append({
                    'requester': file_name,
                    'what': b['what'],
                    'confidence': b['confidence'],
                    'type': b['type'],
                })

    voids = []
    for source_module, requests in source_requests.items():
        if len(requests) >= 2:
            avg_conf = sum(r['confidence'] for r in requests) / len(requests)
            voids.append({
                'source_module': source_module,
                'void_score': len(requests),
                'avg_confidence': round(avg_conf, 3),
                'requesters': requests,
                'diagnosis': (
                    f'{source_module} is a SILO — {len(requests)} files need data '
                    f'from it but none have access. Architectural integration gap.'
                ),
            })
    return sorted(voids, key=lambda v: v['void_score'], reverse=True)
