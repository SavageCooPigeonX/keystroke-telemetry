"""codebase_transmuter_seq001_v001_narrative_mirror_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 30 lines | ~245 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import time

def build_narrative_mirror(root):
    out_dir = root / 'build' / 'narrative'
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    files_done = 0

    telem = _load_telemetry(root)

    for f in _py_files(root):
        profile = _extract_file_profile(f)
        if profile is None:
            continue

        mod_name = f.stem
        base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', mod_name)
        t_entry = telem.get(base, telem.get(mod_name, {}))

        narrative = _narrate_file(f, profile, t_entry)
        rel = f.relative_to(root)
        dest = out_dir / rel.with_suffix('.narrative.py')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(narrative, encoding='utf-8')
        files_done += 1

    elapsed = round((time.monotonic() - t0) * 1000)
    return {'files': files_done, 'elapsed_ms': elapsed}
