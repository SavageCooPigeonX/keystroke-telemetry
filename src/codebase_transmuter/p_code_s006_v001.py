"""codebase_transmuter_seq001_v001_numerical_mirror_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 60 lines | ~442 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import re
import time

def build_numerical_mirror(root):
    out_dir = root / 'build' / 'numerical'
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    telem = _load_telemetry(root)
    total_orig = 0
    total_num = 0
    files_done = 0
    global_map = {}

    for f in _py_files(root):
        code, name_map = numerify_file(f)
        if code is None:
            continue

        rel = f.relative_to(root)
        mod_name = f.stem
        # strip pigeon suffixes for telemetry lookup
        base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', mod_name)

        # build telemetry vector header
        vec = _telemetry_header(base, telem)
        # also try full stem
        if base not in telem and mod_name in telem:
            vec = _telemetry_header(mod_name, telem)

        code = f'{vec}\n{code}'

        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code, encoding='utf-8')

        orig_text = f.read_text('utf-8', errors='ignore')
        total_orig += _tok(orig_text)
        total_num += _tok(code)
        files_done += 1

        for name, num_id in name_map.items():
            global_map[name] = num_id

    elapsed = round((time.monotonic() - t0) * 1000)

    # write the symbol map
    map_path = out_dir / '_SYMBOL_MAP.json'
    map_path.write_text(json.dumps(global_map, indent=1), encoding='utf-8')

    return {
        'files': files_done,
        'orig_tokens': total_orig,
        'numerical_tokens': total_num,
        'ratio': round(total_orig / max(total_num, 1), 2),
        'unique_symbols': len(global_map),
        'elapsed_ms': elapsed,
    }
