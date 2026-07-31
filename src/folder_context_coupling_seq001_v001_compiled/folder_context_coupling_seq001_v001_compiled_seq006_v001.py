"""folder_context_coupling_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path

def _line_count_over(path: Path, limit: int) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for idx, _line in enumerate(handle, start=1):
                if idx > limit:
                    return idx
        return idx if "idx" in locals() else 0
    except Exception:
        return 0
