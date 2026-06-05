import json
import tempfile
from pathlib import Path

from pigeon_compiler.rename_engine import load_registry, parse_pigeon_stem
from src.intent_identity_naming_seq001_v001 import (
    build_intent_filename,
    itid_from_intent_key,
    lineage_hash,
    parse_intent_stem,
    stamp_intent_touch,
)

SESSION_FILES = [
    "src/registry_identity_bridge_seq001_v001.py",
    "src/intent_attention_grader_seq001_v001.py",
    "src/intent_identity_naming_seq001_v001.py",
]

SESSION_INTENTS = {
    "src/registry_identity_bridge_seq001_v001.py": (
        "src/registry_identity_bridge_seq001_v001:build:patch_registry:patch",
        "patch_registry",
    ),
    "src/intent_attention_grader_seq001_v001.py": (
        "src/intent_attention_grader_seq001_v001:build:wire_grader:patch",
        "wire_itid_naming",
    ),
    "src/intent_identity_naming_seq001_v001.py": (
        "src/intent_identity_naming_seq001_v001:build:replace_seq:patch",
        "replace_seq_with_itid",
    ),
}


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="intent_identity_naming_"))
    (root / "src").mkdir()
    (root / "logs").mkdir()
    for rel in SESSION_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'"""{Path(rel).stem}."""\n', encoding="utf-8")
    (root / "pigeon_registry.json").write_text('{"files": []}\n', encoding="utf-8")
    return root


def test_itid_from_intent_key():
    key = "src/foo_seq001:build:wire_grader:patch"
    assert itid_from_intent_key(key) == "build-wire-grader"


def test_build_and_parse_intent_filename():
    name = build_intent_filename(
        "registry_identity_bridge",
        "patch-registry",
        3,
        date="0605",
        desc="identity_bridge",
        last_change="patch_registry",
    )
    assert "_it-patch-registry_" in name
    assert "_lc_patch_registry" in name
    parsed = parse_intent_stem(Path(name).stem)
    assert parsed
    assert parsed["itid"] == "patch-registry"
    assert parsed["last_change"] == "patch_registry"
    assert parsed["naming"] == "intent_itid"


def test_lineage_hash_stable():
    assert lineage_hash("registry_identity_bridge", "src") == lineage_hash(
        "registry_identity_bridge", "src"
    )


def test_parse_pigeon_stem_reads_intent_format():
    stem = "registry_identity_bridge_it-patch-registry_v003__bridge_lc_touch"
    parsed = parse_pigeon_stem(stem)
    assert parsed
    assert parsed.get("itid") == "patch-registry"
    assert parsed.get("naming") == "intent_itid"


def test_touched_session_files_have_itid_and_last_change():
    root = _root()
    for rel, (intent_key, last_change) in SESSION_INTENTS.items():
        stamp_intent_touch(
            root,
            rel,
            intent_key=intent_key,
            last_change=last_change,
            reason="session_touch",
            write=True,
        )

    registry = load_registry(root)
    for rel, (intent_key, last_change) in SESSION_INTENTS.items():
        entry = registry[rel]
        assert entry.get("itid"), f"missing itid for {rel}"
        assert entry.get("lh"), f"missing lh for {rel}"
        assert int(entry.get("eci") or 0) >= 1, f"missing eci for {rel}"
        assert entry.get("intent_key") == intent_key
        assert entry.get("last_change") == last_change
        assert entry.get("identity_anchor", "").startswith(entry.get("identity_id", "x"))
