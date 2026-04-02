"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_io_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def registry_path(root: Path) -> Path:
    return Path(root) / REGISTRY_FILE


def load_registry(root: Path) -> dict:
    """Load pigeon_registry.json. Returns {path: entry} dict."""
    rp = registry_path(root)
    if not rp.exists():
        return {}
    try:
        data = json.loads(rp.read_text(encoding='utf-8'))
        return {e['path']: e for e in data.get('files', [])}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_registry(root: Path, entries: dict):
    """Write pigeon_registry.json atomically."""
    rp = registry_path(root)
    data = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total': len(entries),
        'files': sorted(entries.values(), key=lambda e: e['path']),
    }
    rp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                  encoding='utf-8')
