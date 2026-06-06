"""codex_compat_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
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


def _latest_json(path: Path) -> dict[str, Any] | None:
    rows = _load_jsonl_tail(path, max_lines=1)
    return rows[-1] if rows else None


def _replace_managed_block(text: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _match: block, text)
    return text.rstrip() + "\n\n" + block + "\n"
