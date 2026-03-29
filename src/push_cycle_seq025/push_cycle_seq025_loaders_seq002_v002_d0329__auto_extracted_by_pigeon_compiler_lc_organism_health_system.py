"""push_cycle_seq025_loaders_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 49 lines | ~401 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_pigeon_module(root: Path, folder: str, pattern: str):
    """Dynamically import a pigeon module by glob (filenames mutate)."""
    import importlib.util
    matches = sorted((root / folder).glob(f'{pattern}.py'))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location(matches[-1].stem, matches[-1])
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_state(root: Path) -> dict:
    p = root / CYCLE_STATE_PATH
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:
            pass
    return {"last_journal_line": 0, "total_cycles": 0, "last_commit": None}


def _save_state(root: Path, state: dict) -> None:
    p = root / CYCLE_STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2) + "\n", "utf-8")


def _load_journal_since(root: Path, after_line: int) -> list[dict]:
    """Load all prompt_journal entries since the last push."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return []
    entries = []
    with open(p, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if i <= after_line or not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries
