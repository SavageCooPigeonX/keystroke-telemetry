"""Install the operator data guard as the local pre-push hook."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


HOOK_TEXT = """#!/bin/sh
# Keystroke Telemetry: block operator-private runtime data from git pushes.

if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v py >/dev/null 2>&1; then
    PYTHON="py"
else
    PYTHON="python"
fi

"$PYTHON" scripts/operator_data_guard_seq001_v001__block_operator_data_git_storage_lc_data_storage_operator_happens.py --pre-push
"""


def install_hook(root: Path) -> Path:
    hooks_dir = root / ".git" / "hooks"
    if not hooks_dir.exists():
        raise FileNotFoundError(f"missing git hooks directory: {hooks_dir}")
    hook = hooks_dir / "pre-push"
    hook.write_text(HOOK_TEXT, encoding="utf-8", newline="\n")
    try:
        current_mode = hook.stat().st_mode
        os.chmod(hook, current_mode | 0o111)
    except OSError:
        pass
    return hook


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    hook = install_hook(Path(args.root).resolve())
    print(f"installed {hook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
