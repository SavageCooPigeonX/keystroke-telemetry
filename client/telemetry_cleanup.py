"""One-shot telemetry cleanup for legacy logs and polluted operator history.

Actions:
  1. Archive logs/keystroke_live.jsonl if it exists.
  2. Backup operator_profile.md.
  3. Remove known artifact records from the embedded operator history.
  4. Re-render operator_profile.md using the current OperatorStats module.

Usage:
  py client/telemetry_cleanup.py <repo_root>
  py client/telemetry_cleanup.py <repo_root> --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_operator_stats_module(root: Path):
    matches = sorted(root.glob("src/控w_ops_s008*.py"))
    if not matches:
        raise FileNotFoundError("operator_stats module not found under src/")
    module_path = matches[-1]
    spec = importlib.util.spec_from_file_location("_operator_stats_cleanup", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_profile_history(profile_path: Path) -> list[dict]:
    if not profile_path.exists():
        return []
    text = profile_path.read_text(encoding="utf-8")
    match = re.search(r"<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->", text, re.DOTALL)
    if not match:
        return []
    payload = json.loads(match.group(1).strip())
    return payload.get("history", [])


def _is_artifact_record(record: dict) -> bool:
    if not isinstance(record, dict):
        return True

    keys = int(record.get("keys", 0) or 0)
    wpm = float(record.get("wpm", 0) or 0)
    hesitation = float(record.get("hesitation", 0) or 0)
    del_ratio = float(record.get("del_ratio", 0) or 0)
    submitted = bool(record.get("submitted", True))

    old_micro_batch = (
        not submitted
        and keys <= 3
        and wpm >= 180
        and hesitation >= 0.95
        and del_ratio >= 0.3
    )
    impossible_scale = keys > 5000 or wpm > 1000
    return old_micro_batch or impossible_scale


def _archive_file(path: Path, archive_dir: Path, label: str, dry_run: bool) -> str | None:
    if not path.exists():
        return None
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / f"{path.stem}.{label}.{_timestamp_slug()}{path.suffix}"
    if not dry_run:
        shutil.move(str(path), str(target))
    return str(target)


def cleanup(root: Path, dry_run: bool = False) -> dict:
    root = root.resolve()
    logs_dir = root / "logs"
    archive_dir = logs_dir / "archive"
    legacy_log = logs_dir / "keystroke_live.jsonl"
    profile_path = root / "operator_profile.md"

    history = _load_profile_history(profile_path)
    cleaned_history = [record for record in history if not _is_artifact_record(record)]
    removed_count = len(history) - len(cleaned_history)

    archived_legacy = _archive_file(legacy_log, archive_dir, "legacy", dry_run)
    archived_profile = _archive_file(profile_path, archive_dir, "pre_cleanup", dry_run)

    if not dry_run and cleaned_history:
        operator_stats = _load_operator_stats_module(root)
        stats = operator_stats.OperatorStats(str(profile_path), write_every=1)
        stats._history = cleaned_history
        stats._msg_count = len(cleaned_history)
        stats.flush()

    return {
        "dry_run": dry_run,
        "legacy_log_archived": archived_legacy,
        "profile_backup": archived_profile,
        "history_before": len(history),
        "history_after": len(cleaned_history),
        "history_removed": removed_count,
        "profile_rebuilt": bool(cleaned_history) and not dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive legacy telemetry logs and rebuild operator history.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without modifying files")
    args = parser.parse_args()

    result = cleanup(Path(args.root), dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())