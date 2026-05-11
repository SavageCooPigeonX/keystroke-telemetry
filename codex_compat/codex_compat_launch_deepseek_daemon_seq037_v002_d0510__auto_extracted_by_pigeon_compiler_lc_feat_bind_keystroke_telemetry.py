"""codex_compat_launch_deepseek_daemon_seq037_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 037 | VER: v002 | 34 lines | ~375 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_deepseek_api_key_present_seq036_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _deepseek_api_key_present
from .codex_compat_deepseek_default_model_seq035_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _deepseek_default_model
from pathlib import Path
from typing import Any
import os
import re
import subprocess

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
