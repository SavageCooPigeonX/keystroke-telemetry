"""codex_compat_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq016_v001 import _deepseek_default_model
from pathlib import Path
from typing import Any
import os
import re
import subprocess

def _deepseek_api_key_present(root: Path) -> bool:
    if os.environ.get("DEEPSEEK_API_KEY"):
        return True
    env_path = Path(root) / ".env"
    if not env_path.exists():
        return False
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("DEEPSEEK_API_KEY=") and line.split("=", 1)[1].strip():
                return True
    except Exception:
        return False
    return False


def launch_deepseek_daemon(root: Path, dry_run: bool = False) -> dict[str, Any]:
    root = Path(root)
    script = root / "src" / "deepseek_daemon_seq001_v001.py"
    if not script.exists():
        return {"status": "missing", "target": str(script)}
    key_present = _deepseek_api_key_present(root)
    if not key_present and not dry_run:
        return {
            "status": "blocked",
            "reason": "DEEPSEEK_API_KEY missing; use --dry-run to smoke-test without API calls",
            "model": _deepseek_default_model(),
            "target": str(script),
        }
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    cmd = ["py", str(script), "--cycle-s", "12"]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.Popen(cmd, cwd=root, creationflags=flags)
    return {
        "status": "started",
        "pid": proc.pid,
        "dry_run": dry_run,
        "model": _deepseek_default_model(),
        "target": str(script),
    }
