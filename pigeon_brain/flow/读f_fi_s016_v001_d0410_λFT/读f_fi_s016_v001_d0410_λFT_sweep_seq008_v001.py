"""读f_fi_s016_v001_d0410_λFT_sweep_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 37 lines | ~407 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, os, re, hashlib, urllib.request, urllib.error

def run_interrogation_sweep(
    root: Path, n: int = 10, force: bool = False
) -> list[dict]:
    """Interrogate top N files by bug priority. Each call costs 1 LLM request."""
    reg = json.loads((root / "pigeon_registry.json").read_text("utf-8"))
    entries = reg.get("files", reg) if isinstance(reg, dict) else reg
    entries = sorted(entries, key=_priority, reverse=True)

    results = []
    skipped = 0
    for entry in entries:
        if len(results) >= n:
            break
        path = entry.get("path", "")
        name = entry.get("name", Path(path).stem)
        if not path:
            continue
        bugs = [c for m in _BETA_RE.findall(path) for c in re.findall(r"[a-z]{2}", m)]
        if not bugs and not force:
            skipped += 1
            continue  # skip clean files unless forced
        result = interrogate_file(root, path, name, bugs, force=force)
        if result:
            directive = result.get("autonomous_directive", "?")
            intent = result.get("intent", "?")
            cached = "CACHE" if result.get("source_hash") and not force else "LLM"
            print(f"  [{cached}] {name[:35]:<35} bugs={bugs}")
            print(f"         intent: {intent[:70]}")
            print(f"         directive: {directive[:80]}")
            results.append({"node": name, "bugs": bugs, **result})

    print(f"\nSweep complete: {len(results)} interrogated, {skipped} clean files skipped.")
    return results
