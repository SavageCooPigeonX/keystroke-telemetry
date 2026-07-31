"""organization_pass_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq002_v001 import _collect_python_files
from .organization_pass_seq001_v001_compiled_seq003_v001 import _file_info
from .organization_pass_seq001_v001_compiled_seq004_v001 import _folder_rows
from .organization_pass_seq001_v001_compiled_seq005_v001 import _move_plan
from .organization_pass_seq001_v001_compiled_seq006_v001 import _module_name
from .organization_pass_seq001_v001_compiled_seq006_v001 import _now
from .organization_pass_seq001_v001_compiled_seq006_v001 import _summary
from .organization_pass_seq001_v001_compiled_seq006_v001 import _write_outputs
from .organization_pass_seq001_v001_compiled_seq007_v001 import HISTORY
from .organization_pass_seq001_v001_compiled_seq007_v001 import LATEST
from .organization_pass_seq001_v001_compiled_seq007_v001 import MARKDOWN
from .organization_pass_seq001_v001_compiled_seq007_v001 import SCHEMA
from pathlib import Path
from typing import Any
import re

def build_organization_plan(
    root: Path,
    *,
    write: bool = True,
    file_limit: int | None = None,
) -> dict[str, Any]:
    """Scan the repo and produce a plan for folder-independent code rooms."""
    root = Path(root)
    files = _collect_python_files(root, file_limit=file_limit)
    module_index = {_module_name(root, path): path.relative_to(root).as_posix() for path in files}
    infos = [_file_info(root, path, module_index) for path in files]
    folder_rows = _folder_rows(root, infos)
    move_plan = _move_plan(root, infos)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "mode": "plan_only_no_moves",
        "root": str(root),
        "summary": _summary(infos, folder_rows, move_plan),
        "folder_rankings": folder_rows,
        "move_plan": move_plan,
        "compiler_policy": {
            "goal": "folders should be independently compilable rooms with explicit external edges",
            "canonical_rule": "imports and manifests bind to real paths; operator labels and mutation keys are metadata",
            "execution_rule": "apply moves only after import map, manifest update, py_compile, and focused tests",
            "pigeon_code_rule": "new extracted modules target <=200 lines and carry seq/version allocated from local siblings",
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_outputs(root, result)
    return result
