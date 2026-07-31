import json
import tempfile
from pathlib import Path

from src.tc_intent_keys_seq001_v001 import generate_intent_graph
from tests.regression.test_tc_intent_keys_seq004_v001_d0730 import _root


def test_domain_splitting_routes_each_segment_to_its_own_domain():
    root = _root()

    graph = generate_intent_graph(
        root,
        "hush shard memory should update writeback, "
        "irt artifact probe should emit pulse, "
        "pigeon compiler should preserve rename imports, "
        "context select should route typing deletion telemetry",
    )

    assert graph["domain_selection"]["schema"] == "domain_split/v1"
    assert graph["domain_selection"]["split_count"] >= 3
    domains = [intent["domain_id"] for intent in graph["intents"]]
    assert "project.hush" in domains
    assert "project.irt" in domains
    assert "project.pigeon_code_compiler" in domains
    assert "project.keystroke_telemetry" in domains

    by_domain = {intent["domain_id"]: intent for intent in graph["intents"]}
    assert any(file.startswith("hush_runtime/hush_v38/") for file in by_domain["project.hush"]["files"])
    assert by_domain["project.hush"]["intent_key"].startswith("project.hush:")
    assert any(file.startswith("src/irt_") for file in by_domain["project.irt"]["files"])
    assert any(file.startswith("pigeon_compiler/") for file in by_domain["project.pigeon_code_compiler"]["files"])
    assert any("domain_match" in score["reasons"] for intent in graph["intents"] for score in intent["file_scores"])


def test_missing_external_domain_does_not_backfill_from_cross_domain_docs():
    root = _root()
    (root / "hush_runtime" / "hush_v38" / "pipeline" / "hush_router.py").unlink()
    doc = root / "docs" / "HUSH_ARCHITECTURE.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# Hush\nhush shard memory writeback recall architecture\n", encoding="utf-8")

    graph = generate_intent_graph(root, "hush shard memory should update writeback")

    intent = graph["intents"][0]
    assert intent["domain_id"] == "project.hush"
    assert intent["files"] == []
    assert "domain_files_unavailable:project.hush" in intent["missing"]
    assert all(score["domain_id"] != "cross_domain.audit" for score in intent["file_scores"])


def test_domain_manifest_external_root_routes_missing_hush_to_declared_repo():
    root = _root()
    (root / "hush_runtime" / "hush_v38" / "pipeline" / "hush_router.py").unlink()
    external = Path(tempfile.mkdtemp(prefix="tc_hush_external_"))
    external_file = external / "hush_runtime" / "hush_v38" / "memory" / "distributed_memory_seq002_v001.py"
    external_file.parent.mkdir(parents=True, exist_ok=True)
    external_file.write_text("# hush distributed memory shard writeback recall\n", encoding="utf-8")
    (root / "logs").mkdir(exist_ok=True)
    (root / "logs" / "domain_manifest.json").write_text(
        json.dumps({
            "schema": "domain_manifest/v1",
            "domains": [{
                "domain_id": "project.hush",
                "roots": [{
                    "root": external.as_posix(),
                    "source": "external_project",
                    "path_prefixes": ["hush_runtime/"],
                }],
            }],
        }),
        encoding="utf-8",
    )

    graph = generate_intent_graph(root, "hush shard memory should update writeback")

    intent = graph["intents"][0]
    assert intent["domain_id"] == "project.hush"
    assert intent["intent_key"].startswith("project.hush:")
    assert external_file.resolve().as_posix() in intent["files"]
    assert intent["missing"] == []
    assert any(score.get("external") for score in intent["file_scores"])
    assert graph["domain_manifest_written"]["json"] == "logs/domain_manifest.json"
    assert graph["domain_manifest_written"]["markdown"] == "logs/domain_manifest.md"
    manifest = json.loads((root / "logs" / "intent_map_manifest.json").read_text(encoding="utf-8"))
    assert any(
        row["file"] == external_file.resolve().as_posix()
        and row["intent_key"] == intent["intent_key"]
        and row["external"] is True
        for row in manifest["file_pairings"]
    )
    assert (root / "logs" / "domain_manifest.md").exists()
