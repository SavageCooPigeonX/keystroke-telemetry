"""codex_compat_run_sim_buffer_seq018_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 018 | VER: v002 | 42 lines | ~364 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import re
import subprocess

def _run_sim_buffer(root: Path, buffer: str, timeout_s: int = 45) -> dict[str, Any]:
    """Run the existing thought-completer sim path for a buffer.

    This is intentionally subprocess-based because the sim module has package
    imports and global paths tuned for the repo runtime.
    """
    if not buffer.strip():
        return {"status": "skipped", "reason": "empty_buffer"}
    script = root / "src" / "thought_completer.py"
    if not script.exists():
        return {"status": "missing", "reason": str(script)}
    try:
        result = subprocess.run(
            ["py", str(script), "--sim-buffer", buffer],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "timeout_s": timeout_s,
            "stdout": (exc.stdout or "")[-2000:],
            "stderr": (exc.stderr or "")[-2000:],
        }
    except OSError as exc:
        return {"status": "error", "error": str(exc)}

    return {
        "status": "ok" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }
