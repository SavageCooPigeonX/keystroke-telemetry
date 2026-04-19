"""
Persona intent synthesizer — reads file_memories/*.json,
extracts accumulated operator intents from file chat conversations,
and produces a compact block for injection into copilot-instructions.md.

Called by: dynamic_prompt pipeline, post-chat hooks
Outputs: logs/persona_intents_latest.json + copilot-injectable block
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from pathlib import Path
import json
from datetime import datetime, timezone

def load_all_memories(root: Path) -> dict:
    """Load all file persona memories from logs/file_memories/."""
    mem_dir = root / "logs" / "file_memories"
    if not mem_dir.exists():
        return {}
    result = {}
    for f in mem_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            module = data.get("module", f.stem)
            result[module] = data
        except Exception:
            continue
    return result

def extract_intents(memories: dict) -> list[dict]:
    """Extract all known intents across all file personas, ranked by recency."""
    intents = []
    for module, mem in memories.items():
        for intent_text in mem.get("known_intents", []):
            intents.append({
                "module": module,
                "intent": intent_text,
                "conversations": mem.get("conversation_count", 0),
                "updated": mem.get("updated", ""),
            })
        # Also pull from entries tagged as extracted_intent
        for entry in mem.get("entries", []):
            if entry.get("type") == "extracted_intent":
                intents.append({
                    "module": module,
                    "intent": entry["content"],
                    "conversations": mem.get("conversation_count", 0),
                    "updated": entry.get("ts", ""),
                })
    # Sort by most recent
    intents.sort(key=lambda x: x.get("updated", ""), reverse=True)
    return intents

def extract_frustrations(memories: dict) -> list[dict]:
    """Extract operator frustration signals across all file personas."""
    frustrations = []
    for module, mem in memories.items():
        for signal in mem.get("operator_frustration_signals", []):
            frustrations.append({"module": module, "signal": signal})
    return frustrations

def extract_open_tasks(memories: dict) -> list[dict]:
    """Extract pending tasks across all file personas."""
    tasks = []
    for module, mem in memories.items():
        for task in mem.get("pending_tasks", []):
            tasks.append({"module": module, "task": task})
    return tasks

def extract_relationships(memories: dict) -> list[dict]:
    """Extract cross-module relationship observations."""
    rels = []
    for module, mem in memories.items():
        for partner, note in mem.get("relationship_notes", {}).items():
            rels.append({"from": module, "to": partner, "note": note})
    return rels

def build_copilot_block(root: Path) -> str:
    """Build a compact block for injection into copilot-instructions.md."""
    memories = load_all_memories(root)
    if not memories:
        return ""
    intents = extract_intents(memories)
    frustrations = extract_frustrations(memories)
    tasks = extract_open_tasks(memories)
    rels = extract_relationships(memories)

    lines = [
        "<!-- pigeon:persona-intents -->",
        "## Extracted Operator Intents (from file conversations)",
        "",
        f"*{len(memories)} file(s) with memory · {sum(m.get('conversation_count', 0) for m in memories.values())} total conversations*",
        "",
    ]

    if intents:
        lines.append("**Intents (most recent first):**")
        for i in intents[:15]:  # cap at 15
            lines.append(f"- `{i['module']}`: {i['intent']}")
        lines.append("")

    if frustrations:
        lines.append("**Operator frustrations:**")
        for f in frustrations[:10]:
            lines.append(f"- `{f['module']}`: {f['signal']}")
        lines.append("")

    if tasks:
        lines.append("**Open tasks from file conversations:**")
        for t in tasks[:10]:
            lines.append(f"- `{t['module']}`: {t['task']}")
        lines.append("")

    if rels:
        lines.append("**Cross-module observations:**")
        for r in rels[:10]:
            lines.append(f"- `{r['from']}` → `{r['to']}`: {r['note']}")
        lines.append("")

    lines.append("<!-- /pigeon:persona-intents -->")
    return "\n".join(lines)

def write_intent_snapshot(root: Path) -> Path:
    """Write a JSON snapshot of all extracted intents for downstream consumers."""
    memories = load_all_memories(root)
    snapshot = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "module_count": len(memories),
        "total_conversations": sum(m.get("conversation_count", 0) for m in memories.values()),
        "intents": extract_intents(memories)[:30],
        "frustrations": extract_frustrations(memories)[:15],
        "open_tasks": extract_open_tasks(memories)[:15],
        "relationships": extract_relationships(memories)[:15],
    }
    out = root / "logs" / "persona_intents_latest.json"
    out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return out

def inject_into_copilot_instructions(root: Path) -> bool:
    """Inject/update the persona-intents block in copilot-instructions.md."""
    ci_path = root / ".github" / "copilot-instructions.md"
    if not ci_path.exists():
        return False
    content = ci_path.read_text(encoding="utf-8")
    block = build_copilot_block(root)
    if not block:
        return False

    start_marker = "<!-- pigeon:persona-intents -->"
    end_marker = "<!-- /pigeon:persona-intents -->"

    if start_marker in content:
        # Replace existing block
        before = content[:content.index(start_marker)]
        after = content[content.index(end_marker) + len(end_marker):]
        content = before + block + after
    else:
        # Append before the auto-index
        anchor = "<!-- pigeon:auto-index -->"
        if anchor in content:
            idx = content.index(anchor)
            content = content[:idx] + block + "\n" + content[idx:]
        else:
            content += "\n" + block + "\n"

    ci_path.write_text(content, encoding="utf-8")
    return True

if __name__ == "__main__":
    root = Path(".")
    snap = write_intent_snapshot(root)
    print(f"wrote {snap}")
    ok = inject_into_copilot_instructions(root)
    print(f"injected into copilot-instructions: {ok}")
