"""push_cycle_seq025_signal_extractors_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path

def _extract_operator_signal(entries: list[dict]) -> dict:
    """Aggregate operator signal from all prompts in this push cycle."""
    if not entries:
        return {"prompt_count": 0}
    wpms = [e.get("signals", {}).get("wpm", 0) or e.get("wpm", 0) for e in entries]
    dels = [e.get("signals", {}).get("deletion_ratio", 0) or e.get("deletion_ratio", 0) for e in entries]
    hess = [e.get("signals", {}).get("hesitation_count", 0) for e in entries]
    intents = {}
    for e in entries:
        intent = e.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
    module_refs = set()
    for e in entries:
        for m in e.get("module_refs", []):
            module_refs.add(m)
    deleted_words = []
    for e in entries:
        for w in e.get("deleted_words", []):
            if isinstance(w, str):
                deleted_words.append(w)
            elif isinstance(w, dict):
                deleted_words.append(w.get("word", ""))
    states = {}
    for e in entries:
        s = e.get("cognitive_state", "unknown")
        states[s] = states.get(s, 0) + 1
    avg = lambda xs: sum(xs) / len(xs) if xs else 0
    return {
        "prompt_count": len(entries),
        "avg_wpm": round(avg(wpms), 1),
        "avg_deletion": round(avg(dels), 3),
        "total_hesitations": sum(hess),
        "intent_distribution": intents,
        "dominant_intent": max(intents, key=intents.get) if intents else "unknown",
        "module_refs": sorted(module_refs),
        "deleted_words": deleted_words[-20:],
        "cognitive_states": states,
        "dominant_state": max(states, key=states.get) if states else "unknown",
    }


def _extract_copilot_signal(changed_files: list[str]) -> dict:
    """Extract copilot signal from the git diff (files changed = copilot wrote)."""
    py_files = [f for f in changed_files if f.endswith(".py")]
    modules_touched = set()
    for f in py_files:
        stem = Path(f).stem
        # Strip pigeon suffix to get base module name
        parts = stem.split("_seq")
        if parts:
            modules_touched.add(parts[0])
    return {
        "files_changed": len(changed_files),
        "py_files_changed": len(py_files),
        "modules_touched": sorted(modules_touched),
        "non_py_files": [f for f in changed_files if not f.endswith(".py")],
    }
