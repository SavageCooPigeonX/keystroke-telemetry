"""predictor_seq009_trend_extractor_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

from collections import Counter
from pathlib import Path
from typing import Any
import json

def extract_cognitive_trend(journal_path: Path, n_recent: int = 10) -> dict[str, Any]:
    """Extract cognitive trends from recent prompt journal entries + live telemetry."""
    if not journal_path.exists():
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}

    entries = []
    for line in journal_path.read_text(encoding="utf-8").strip().splitlines()[-n_recent:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not entries:
        return {"states": [], "modules": [], "avg_del": 0.0, "avg_wpm": 0.0}

    states = [e.get("cognitive_state", "unknown") for e in entries]
    all_modules: list[str] = []
    for e in entries:
        all_modules.extend(e.get("module_refs", []))
        for hm in e.get("hot_modules", []):
            all_modules.append(hm.get("module", ""))

    # Inject live hot_modules from prompt_telemetry + file_heat_map
    root = journal_path.parent.parent  # logs/ -> project root
    try:
        telem_path = root / "logs" / "prompt_telemetry_latest.json"
        if telem_path.exists():
            telem = json.loads(telem_path.read_text(encoding="utf-8"))
            for hm in telem.get("hot_modules", []):
                mod = hm.get("module", "")
                if mod:
                    all_modules.append(mod)
                    all_modules.append(mod)  # double-weight live signal
    except Exception:
        pass
    try:
        heat_path = root / "file_heat_map.json"
        if heat_path.exists():
            hm_data = json.loads(heat_path.read_text(encoding="utf-8"))
            for entry in hm_data.get("files", [])[:5]:
                mod = entry.get("file", "").replace(".py", "")
                mod = mod.split("/")[-1].split("_seq")[0] if mod else ""
                if mod:
                    all_modules.append(mod)
    except Exception:
        pass

    # Inject recently-edited modules from edit_pairs (actual edits > hesitation)
    try:
        pairs_path = root / "logs" / "edit_pairs.jsonl"
        if pairs_path.exists():
            for line in pairs_path.read_text(encoding="utf-8").strip().splitlines()[-10:]:
                try:
                    ep = json.loads(line)
                    mod = ep.get("file", "").replace(".py", "")
                    mod = mod.split("/")[-1].split("_seq")[0] if mod else ""
                    if mod:
                        all_modules.extend([mod, mod, mod])  # triple-weight
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    module_counts = Counter(m for m in all_modules if m)
    # Lower threshold: top-5 modules regardless of count (was: count >= 2 only)
    clusters = [m for m, _c in module_counts.most_common(5)]
    signals = [e.get("signals", {}) for e in entries]
    avg_del = sum(s.get("deletion_ratio", 0) for s in signals) / max(len(signals), 1)
    avg_wpm = sum(s.get("wpm", 0) for s in signals) / max(len(signals), 1)
    return {
        "states": states, "modules": clusters,
        "avg_del": round(avg_del, 4), "avg_wpm": round(avg_wpm, 1),
        "dominant_state": Counter(states).most_common(1)[0][0] if states else "unknown",
        "n_entries": len(entries),
    }
