"""engagement_hooks_seq001_v001_context_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 55 lines | ~517 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

def _load_context(root):
    root = Path(root)
    reg = _json(root / "pigeon_registry.json") or {}
    files = reg.get("files", [])

    ctx = {
        "root": root,
        "reg_files": files,
        "profiles": _json(root / "file_profiles.json") or {},
        "dossier": _json(root / "logs" / "active_dossier.json") or {},
        "reactor": _json(root / "logs" / "cognitive_reactor_state.json") or {},
        "rework": _json(root / "rework_log.json"),
        "compositions": _jsonl_tail(root / "logs" / "chat_compositions.jsonl", 15),
        "journal": _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 30),
        "edit_pairs": _jsonl_tail(root / "logs" / "edit_pairs.jsonl", 20),
        "veins": _json(root / "pigeon_brain" / "context_veins_seq001_v001.json") or {},
        "mutations": _json(root / "logs" / "copilot_prompt_mutations.json") or {},
        "hour": datetime.now().hour,
    }

    # Derived signals
    ctx["bugged"] = [f for f in files if f.get("bug_keys")]
    ctx["overcap"] = [f for f in files if f.get("tokens", 0) > 2000]
    ctx["neglected"] = sorted(
        [(f, _hours_since(f.get("last_touch", f.get("date", ""))))
         for f in files],
        key=lambda x: x[1], reverse=True,
    )

    # Deleted words from compositions
    ctx["all_deleted_words"] = []
    for c in ctx["compositions"]:
        for w in c.get("intent_deleted_words", []):
            word = w.get("word", w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3:
                ctx["all_deleted_words"].append(word)

    # Module reference counts from journal
    refs = []
    for j in ctx["journal"]:
        refs.extend(j.get("module_refs", []))
    ctx["ref_counts"] = Counter(refs)
    referenced = set(refs)
    ctx["avoided"] = [
        f for f in files
        if f.get("ver", 1) >= 3 and f["name"] not in referenced
    ]

    return ctx
