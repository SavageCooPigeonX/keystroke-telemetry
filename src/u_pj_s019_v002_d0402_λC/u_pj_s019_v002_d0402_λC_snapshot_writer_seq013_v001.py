"""u_pj_s019_v002_d0402_λC_snapshot_writer_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _write_latest_snapshot(root: Path, snapshot: dict) -> None:
    snapshot_path = root / SNAPSHOT_PATH
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
