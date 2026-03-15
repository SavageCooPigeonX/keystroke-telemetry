"""run_compiler_test_seq007_v001.py — Self-test: Pigeon Compiler on its own codebase.

Runs the state extractor on folder_auditor.py and master_auditor.py,
saves ether maps, then sends them to DeepSeek for cut plans.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v003 | 59 lines | ~531 tokens
# DESC:   self_test_pigeon_compiler_on
# INTENT: desc_upgrade
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, sys, os, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.state_extractor.ether_map_builder_seq006_v003_d0314__assemble_full_ether_map_json_lc_desc_upgrade import (
    build_ether_map, save_ether_map)

TARGETS = [
    PROJECT_ROOT / "codebase_auditor" / "folder_auditor.py",
    PROJECT_ROOT / "codebase_auditor" / "master_auditor.py",
]

OUT_DIR = Path(__file__).parent / "compiler_output"


def run_ether_maps():
    """Phase 1: Build ether maps for both targets."""
    OUT_DIR.mkdir(exist_ok=True)
    maps = {}
    for target in TARGETS:
        stem = target.stem
        print(f"\n{'='*60}")
        print(f"  ETHER MAP: {stem}")
        print(f"{'='*60}")
        try:
            em = build_ether_map(target)
            out_path = OUT_DIR / f"{stem}_ether_map.json"
            save_ether_map(em, out_path)
            maps[stem] = em
            print(f"  Lines:      {em['total_lines']}")
            print(f"  Functions:  {len(em['functions'])}")
            print(f"  Classes:    {len(em['classes'])}")
            print(f"  Constants:  {len(em['constants'])}")
            print(f"  Clusters:   {len(em['clusters'])}")
            print(f"  Coupling:   {em['coupling_score']}")
            r = em['resistance']
            print(f"  Resistance: {r['score']} ({r['verdict']})")
            print(f"  Patterns:   {[p['pattern'] for p in r['patterns']]}")
            print(f"  Saved:      {out_path}")
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
    return maps


if __name__ == "__main__":
    print("=" * 60)
    print("  PIGEON COMPILER SELF-TEST v0.1.0")
    print("  Layer 1: State Extractor → Ether Maps")
    print("=" * 60)
    maps = run_ether_maps()
    print(f"\n✓ Phase 1 complete — {len(maps)} ether maps generated")
