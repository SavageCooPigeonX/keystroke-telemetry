"""Install local Git hooks that wake the Pigeon compiler.

Git does not version files under .git/hooks, so a fresh clone can have the
compiler package but no trigger. This script restores the same hook shape used
by the working LinkRouter checkout:

    post-commit -> python -m pigeon_compiler.git_plugin
    pre-commit  -> python -m pigeon_compiler.pre_commit_audit
    pre-push    -> python scripts/refresh_push_manifests.py + maintain_compliance.py
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


POST_COMMIT = """#!/bin/sh
# Pigeon Git Plugin -- post-commit auto-rename daemon.
# Renames touched pigeon files with living desc + intent from commit msg.
# Safe: if it fails, the commit is already done.

# Skip if this commit is already [pigeon-auto]
MSG=$(git log -1 --format=%B)
case "$MSG" in
  *\\[pigeon-auto\\]*) exit 0 ;;
esac

# Find Python
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

"$PYTHON" -m pigeon_compiler.git_plugin || true
"""

PRE_COMMIT = """#!/bin/sh
# Pigeon Compiler pre-commit hook.
# Runs pigeon compliance audit on every commit.
# Advisory only - exit 0 always, never blocks commits.

# Find Python
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

"$PYTHON" -m pigeon_compiler.pre_commit_audit || true

exit 0
"""

PRE_PUSH = """#!/bin/sh
# Pigeon Compiler pre-push compliance gate.
# Blocks pushes while non-excluded Python files exceed PIGEON_MAX.
# Set PIGEON_COMPLIANCE_APPLY=1 to generate low-risk split packages before blocking.
# Raise PIGEON_COMPLIANCE_MAX_RISK=medium/high only when ready for facade tests.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCRIPT="$ROOT/scripts/maintain_compliance.py"

if [ ! -f "$SCRIPT" ]; then
    echo "Pigeon compliance gate skipped: scripts/maintain_compliance.py is not present in this worktree."
    echo "Commit the helper script or push from a worktree that contains it to enforce the gate."
    exit 0
fi

# Find Python. Windows installs in this repo commonly expose only the `py`
# launcher, so check it before falling back to a bare `python`.
if [ -f "$ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON="$ROOT/.venv/Scripts/python.exe"
elif [ -f "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
elif command -v py >/dev/null 2>&1; then
    PYTHON="py"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "Pigeon compliance gate skipped: no Python interpreter found."
    exit 0
fi

if [ "${PIGEON_COMPLIANCE_APPLY:-0}" = "1" ]; then
    "$PYTHON" "$SCRIPT" --all --apply --max-files "${PIGEON_COMPLIANCE_MAX_FILES:-0}" --max-risk "${PIGEON_COMPLIANCE_MAX_RISK:-low}"
else
    "$PYTHON" "$SCRIPT" --all
fi
status=$?
if [ -f "$ROOT/scripts/refresh_push_manifests.py" ]; then
    "$PYTHON" "$ROOT/scripts/refresh_push_manifests.py" --fail-on-write
    manifest_status=$?
    if [ "$manifest_status" -ne 0 ]; then
        echo "Pigeon manifest refresh updated MANIFEST.md files. Commit them, then push again."
        exit "$manifest_status"
    fi
fi
if [ "$status" -ne 0 ]; then
    echo "Pigeon compliance gate blocked push. See logs/pigeon_compliance_push_latest.json"
    exit "$status"
fi

exit 0
"""


def _repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(proc.stdout.strip())


def _install(path: Path, content: str, check: bool) -> bool:
    normalized = content.replace("\r\n", "\n")
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current.replace("\r\n", "\n") == normalized:
        return False
    if check:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8", newline="\n")
    try:
        mode = path.stat().st_mode
        os.chmod(path, mode | 0o111)
    except OSError:
        pass
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    root = _repo_root()
    hooks = root / ".git" / "hooks"
    changed = {
        "post-commit": _install(hooks / "post-commit", POST_COMMIT, args.check),
        "pre-commit": _install(hooks / "pre-commit", PRE_COMMIT, args.check),
        "pre-push": _install(hooks / "pre-push", PRE_PUSH, args.check),
    }
    for name, drifted in changed.items():
        state = "would update" if args.check and drifted else "updated" if drifted else "ok"
        print(f"{name}: {state}")
    return 1 if args.check and any(changed.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
