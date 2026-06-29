"""Compatibility installer for the operator data pre-push guard.

The canonical hook installer is scripts/install_pigeon_hooks.py because pre-push
must keep both the operator-data guard and the Pigeon compliance gate.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def install_hook(root: Path) -> Path:
    installer = root / "scripts" / "install_pigeon_hooks.py"
    if not installer.exists():
        raise FileNotFoundError(f"missing canonical hook installer: {installer}")
    subprocess.run([sys.executable, str(installer)], cwd=root, check=True)
    return root / ".git" / "hooks" / "pre-push"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    hook = install_hook(Path(args.root).resolve())
    print(f"installed {hook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
