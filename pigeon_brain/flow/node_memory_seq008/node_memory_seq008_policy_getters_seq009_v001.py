"""node_memory_seq008_policy_getters_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any

def get_policy(root: Path, node: str) -> dict[str, Any]:
    """Get the compressed policy for a specific node."""
    memory = load_memory(root)
    record = memory.get(node, {})
    return record.get("policy", {})


def get_all_policies(root: Path) -> dict[str, dict]:
    """Get policies for all nodes that have learning history."""
    memory = load_memory(root)
    return {
        node: record.get("policy", {})
        for node, record in memory.items()
        if record.get("policy")
    }
