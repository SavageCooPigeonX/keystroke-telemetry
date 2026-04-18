"""context_compressor_seq001_v001_changed_decomposed_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 65 lines | ~502 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import json
import time

def compress_changed(root, changed_files=None):
    out_dir = root / 'build' / 'compressed'
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()

    if changed_files:
        py_files = [root / f for f in changed_files
                    if f.endswith('.py') and (root / f).exists()
                    and not any(s in Path(f).parts for s in SKIP_DIRS)]
    else:
        py_files = [py for py in root.rglob('*.py')
                    if not any(s in py.parts for s in SKIP_DIRS)]

    total_orig = 0
    total_new = 0
    compressed_count = 0

    for py in py_files:
        compressed, orig_tok, new_tok = compress_file(py)
        if compressed is None:
            continue
        total_orig += orig_tok
        total_new += new_tok
        compressed_count += 1
        rel = py.relative_to(root)
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(compressed, 'utf-8')

    elapsed = time.monotonic() - t0
    ratio = total_orig / total_new if total_new > 0 else 0

    stats_path = out_dir / 'STATS.json'
    existing_stats = {}
    if stats_path.exists():
        try:
            existing_stats = json.loads(stats_path.read_text('utf-8'))
        except Exception:
            pass

    existing_stats.update({
        'last_incremental': {
            'files': compressed_count,
            'orig_tokens': total_orig,
            'compressed_tokens': total_new,
            'ratio': round(ratio, 2),
            'elapsed_ms': round(elapsed * 1000),
        }
    })
    stats_path.write_text(json.dumps(existing_stats, indent=2), 'utf-8')

    return {
        'files': compressed_count,
        'orig_tokens': total_orig,
        'compressed_tokens': total_new,
        'ratio': round(ratio, 2),
        'elapsed_ms': round(elapsed * 1000),
    }
