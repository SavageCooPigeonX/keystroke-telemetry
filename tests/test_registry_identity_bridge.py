import json
import tempfile
from pathlib import Path

from src.registry_identity_bridge_seq001_v002_d0605__seq_pairing_aliases_md_anchors_lc_patch_registry import (
    ALIASES_JSON,
    audit_registry_pairing,
    merge_rename_alias,
    patch_registry,
    prefer_legacy_filename,
    resolve_registry_path,
)


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="registry_bridge_"))
    (root / "src").mkdir()
    (root / "logs").mkdir()
    target = root / "src" / "noise_filter_seq007_v001_d0601__filter_noise_lc_wire_bridge.py"
    target.write_text('"""Filter noise."""\n\ndef filter_noise():\n    return True\n', encoding="utf-8")
    return root


def test_patch_registry_bootstraps_from_disk():
    root = _root()
    result = patch_registry(root, write=True, rebuild=True)

    assert result["action"] == "bootstrapped"
    assert result["entry_count"] >= 1
    assert (root / "pigeon_registry.json").exists()
    registry = json.loads((root / "pigeon_registry.json").read_text(encoding="utf-8"))
    paths = [row["path"] for row in registry.get("files", [])]
    assert any("noise_filter_seq007" in p for p in paths)


def test_merge_rename_alias_records_stable_identity():
    root = _root()
    patch_registry(root, write=True, rebuild=True)
    entry = {
        "name": "noise_filter",
        "seq": 7,
        "ver": 2,
        "desc": "filter_noise",
        "intent": "wire_bridge",
    }
    old = "src/noise_filter_seq007_v001_d0601__filter_noise_lc_wire_bridge.py"
    new = "src/noise_filter_seq007_v002_d0601__filter_noise_lc_wire_bridge.py"
    merge_rename_alias(root, old, new, entry, write=True)

    aliases = json.loads((root / ALIASES_JSON).read_text(encoding="utf-8"))
    assert aliases["aliases"][old]["current_file"] == new
    assert aliases["aliases"][old].get("parent_lineage", {}).get("path") == old
    assert resolve_registry_path(root, old) == new


def test_prefer_legacy_filename_for_semantic_name():
    entry = {
        "name": "noise_filter",
        "semantic_name": "noise_filter",
        "seq": 7,
        "ver": 2,
        "date": "0601",
        "desc": "filter_noise",
        "intent": "wire_bridge",
    }
    name = prefer_legacy_filename(entry, date="0601", desc="filter_noise", intent="wire_bridge")
    assert name.startswith("noise_filter_seq007_v002")
    assert "_lc_wire_bridge" in name


def test_audit_registry_pairing_healthy_on_fresh_bootstrap():
    root = _root()
    patch_registry(root, write=True, rebuild=True)
    from pigeon_compiler.rename_engine import load_registry

    audit = audit_registry_pairing(root, load_registry(root))
    assert audit["matched"] >= 1
    assert audit["healthy"] is True
