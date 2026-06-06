"""file_self_sim_learning_seq001_seq034_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq039_v001 import _estimate_tokens
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import re

def _tests_for_file(root: Path, rel: str, proposal: dict[str, Any]) -> list[str]:
    tests = []
    for step in proposal.get("validation_plan") or []:
        for match in re.findall(r"((?:tests?/)?test[a-zA-Z0-9_./\\-]+\.py)", str(step)):
            tests.append(_clean_rel(match))
    stem = _stem_key(rel)
    candidates = [
        root / f"test_{stem}.py",
        root / "tests" / f"test_{stem}.py",
    ]
    for path in candidates:
        if path.exists():
            tests.append(path.relative_to(root).as_posix())
    return _dedupe(tests)


def _nearest_manifest(root: Path, rel: str) -> str:
    current = (root / rel).parent
    while current != root and root in current.parents:
        manifest = current / "MANIFEST.md"
        if manifest.exists():
            return manifest.relative_to(root).as_posix()
        current = current.parent
    manifest = root / "src" / "MANIFEST.md"
    if manifest.exists():
        return manifest.relative_to(root).as_posix()
    return ""


def _context_pack_files(root: Path, wake_order: list[dict[str, Any]]) -> list[str]:
    files = []
    for node in wake_order[:4]:
        files.append(node["file"])
        if node.get("manifest"):
            files.append(node["manifest"])
        files.extend(node.get("tests") or [])
        files.extend(node.get("known_neighbors") or [])
    budget = 24000
    total = 0
    packed = []
    for rel in _dedupe(files):
        tokens = _estimate_tokens(root, rel)
        if total + tokens > budget and packed:
            continue
        packed.append(rel)
        total += tokens
    return packed[:16]
