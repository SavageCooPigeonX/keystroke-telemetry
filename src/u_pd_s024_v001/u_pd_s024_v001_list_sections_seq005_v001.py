"""u_pd_s024_v001_list_sections_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 12 lines | ~146 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def list_sections(snapshots: list[dict]) -> None:
    print('Sections present across all snapshots:')
    all_sections: dict[str, int] = {}
    for snap in snapshots:
        for s in snap.get('sections', []):
            all_sections[s] = all_sections.get(s, 0) + 1
    for s, cnt in sorted(all_sections.items(), key=lambda x: -x[1]):
        print(f'  [{cnt:3d}x] {s}')
    print(f'\nTotal snapshots: {len(snapshots)}')
    print('Usage: py -m src.u_pd_s024_v001 "<section name>" [N snapshots]')
