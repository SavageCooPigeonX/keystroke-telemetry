"""Block pushes that add or worsen changed-file Pigeon line violations."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pigeon_compiler.pigeon_limits_seq003_v001_d0730__central_compliance_thresholds_and_exclude_lc_organism_health_refactor import PIGEON_MAX, explain_exclusion


def _git(root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc


def _comparison_ref(root: Path) -> str:
    upstream = _git(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], check=False)
    if upstream.returncode == 0 and upstream.stdout.strip():
        return upstream.stdout.strip()
    parent = _git(root, ["rev-parse", "--verify", "HEAD~1"], check=False)
    return "HEAD~1" if parent.returncode == 0 else ""


def _changed_paths(root: Path, base_ref: str) -> list[str]:
    if base_ref:
        args = ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...HEAD"]
    else:
        args = ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
    return [line.strip().replace("\\", "/") for line in _git(root, args).stdout.splitlines() if line.strip()]


def _line_count_text(text: str) -> int:
    return len(text.splitlines())


def _file_lines(path: Path) -> int:
    return _line_count_text(path.read_text(encoding="utf-8", errors="replace"))


def _base_lines(root: Path, base_ref: str, rel: str) -> int | None:
    if not base_ref:
        return None
    proc = _git(root, ["show", f"{base_ref}:{rel}"], check=False)
    return _line_count_text(proc.stdout) if proc.returncode == 0 else None


def audit_changed_file_compliance(root: Path) -> dict[str, Any]:
    base_ref = _comparison_ref(root)
    checked: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for rel in _changed_paths(root, base_ref):
        path = root / rel
        if path.suffix != ".py" or not path.exists():
            continue
        decision = explain_exclusion(path, root)
        if decision.get("excluded"):
            continue
        current = _file_lines(path)
        previous = _base_lines(root, base_ref, rel)
        row = {"path": rel, "current_lines": current, "previous_lines": previous, "status": "ok"}
        if current > PIGEON_MAX:
            if previous and previous > PIGEON_MAX and current <= previous:
                row["status"] = "existing_overcap_not_worse"
            else:
                row["status"] = "new_overcap" if not previous or previous <= PIGEON_MAX else "worsened_overcap"
                violations.append(row)
        checked.append(row)
    return {
        "schema": "pigeon_changed_file_gate/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "pigeon_max": PIGEON_MAX,
        "base_ref": base_ref,
        "checked_count": len(checked),
        "violation_count": len(violations),
        "checked": checked,
        "violations": violations,
        "ok": not violations,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        f"Pigeon changed-file gate: {report['violation_count']} violation(s) / {report['checked_count']} checked",
    ]
    for row in report["violations"][:20]:
        lines.append(
            f"- {row['path']}: {row['status']} "
            f"previous={row['previous_lines']} current={row['current_lines']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = audit_changed_file_compliance(root)
    logs = root / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "pigeon_changed_file_gate_latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
