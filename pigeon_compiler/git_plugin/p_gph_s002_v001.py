"""git_plugin_helpers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 52 lines | ~415 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import os
import re
import subprocess

def _load_dotenv() -> None:
    """Load .env from repo root into os.environ (no external deps)."""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _estimate_tokens(text: str) -> int:
    """Estimate LLM token count from raw text (1 tok ≈ 4 chars)."""
    return max(1, len(text) // TOKEN_RATIO)


def _root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _git(*args: str) -> str:
    r = subprocess.run(
        ['git', *args],
        capture_output=True, text=True, encoding='utf-8',
        cwd=str(_root()), timeout=30,
    )
    return r.stdout.strip()


def _load_glob_module(root: Path, folder: str, pattern: str):
    """Dynamically import a pigeon module by glob pattern (filenames mutate)."""
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
