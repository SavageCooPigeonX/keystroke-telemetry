"""file_self_sim_learning_seq001_seq032_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import re

def _local_import_neighbors(root: Path, rel: str) -> list[str]:
    path = root / rel
    if not path.exists() or path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+import\s+", stripped)
        if not match:
            match = re.match(r"import\s+([A-Za-z_][A-Za-z0-9_\.]*)", stripped)
        if not match:
            continue
        module = match.group(1)
        if not module.startswith(("src.", "client.", "pigeon_brain.", "pigeon_compiler.")):
            continue
        rel_path = module.replace(".", "/") + ".py"
        if (root / rel_path).exists():
            candidates.append(rel_path)
        init_path = module.replace(".", "/") + "/__init__.py"
        if (root / init_path).exists():
            candidates.append(init_path)
    return _dedupe(candidates)[:12]


def _proposal_for_file(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    for proposal in (sources.get("latest") or {}).get("proposals") or []:
        if _clean_rel(proposal.get("path")) == rel:
            return proposal
    return {}
