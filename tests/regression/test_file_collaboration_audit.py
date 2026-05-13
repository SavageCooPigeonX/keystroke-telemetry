import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.file_collaboration_audit_seq001_v001 import audit_file_collaboration


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="file_collab_audit_"))
    logs = root / "logs"
    ts = datetime.now(timezone.utc).isoformat()
    (root / "MANIFEST.md").write_text("# Root Manifest\n", encoding="utf-8")
    (root / "src" / "intent").mkdir(parents=True)
    (root / "src" / "intent" / "MANIFEST.md").write_text("# Intent Manifest\n", encoding="utf-8")
    packets = [
        {
            "packet_id": "dslp-router",
            "file": "src/intent/router.py",
            "responsibility_profile": {"declared_role": "intent routing", "line_count": 180},
            "accumulated_knowledge": {
                "mail_memory": {"summary": "3 stored message(s)"},
                "history_events": 5,
            },
            "context_veins": [{"file": "src/intent/validator.py", "relation": "validator"}],
            "backward_learning_targets": [{"file": "test_router.py", "learn": "test result changes routing confidence"}],
            "verification_packet": {"validation_plan": ["py -m pytest test_router.py -q"]},
            "size_pressure": {"state": "ok", "line_count": 180, "needs_split_plan": False},
            "split_plan_request": {"needed": False},
            "overwrite_readiness": {"allowed": False},
        },
        {
            "packet_id": "dslp-validator",
            "file": "src/intent/validator.py",
            "responsibility_profile": {"declared_role": "validation gate", "line_count": 260},
            "accumulated_knowledge": {
                "mail_memory": {"summary": "1 stored message(s)"},
                "history_events": 2,
            },
            "context_veins": [{"file": "src/intent/router.py", "relation": "peer_context"}],
            "backward_learning_targets": [],
            "verification_packet": {"validation_plan": ["py -m py_compile src/intent/validator.py"]},
            "size_pressure": {"state": "warn", "line_count": 260, "needs_split_plan": True},
            "split_plan_request": {"needed": True},
            "overwrite_readiness": {"allowed": False},
        },
    ]
    graph = {
        "nodes": [
            {"file": "src/intent/router.py", "weighted_degree": 2.1},
            {"file": "src/intent/validator.py", "weighted_degree": 1.9},
        ],
        "edges": [
            {
                "from": "src/intent/router.py",
                "to": "src/intent/validator.py",
                "relation": "validator",
                "weight": 1.0,
            },
            {
                "from": "src/intent/router.py",
                "to": "test_router.py",
                "relation": "backward_target",
                "weight": 0.45,
            },
            {
                "from": "src/intent/router.py",
                "to": "src/intent/MANIFEST.md",
                "relation": "manifest",
                "weight": 0.85,
            },
        ],
    }
    latest = {
        "ts": ts,
        "intent": {
            "raw": "make files collaborate through manifest state",
            "intent_key": "src/intent:build:manifest_collaboration:patch",
        },
        "learning_packets": packets,
        "wake_order": [{"file": "src/intent/router.py"}, {"file": "src/intent/validator.py"}],
        "relationship_graph": graph,
        "overcap_split_jobs": [{"file": "src/intent/validator.py"}],
        "interlink_plan": {"near_term_jobs": [{"job": "load_manifest_state"}]},
    }
    _write_json(logs / "file_self_sim_learning_latest.json", latest)
    _write_json(logs / "file_relationship_graph.json", graph)
    _write_json(logs / "file_identity_registry.json", {
        "files": [
            {"file": "src/intent/router.py", "arch_seq": "A-001"},
            {"file": "src/intent/validator.py", "arch_seq": "A-002"},
        ]
    })
    _write_json(logs / "file_job_council_latest.json", {
        "ts": ts,
        "jobs": [],
    })
    _write_jsonl(logs / "file_self_sim_learning.jsonl", [
        {"relationship_graph": {"edges": graph["edges"][:1]}},
        {"relationship_graph": {"edges": graph["edges"]}},
    ])
    _write_jsonl(logs / "file_self_sim_learning_outcomes.jsonl", [
        {"file": "src/intent/router.py", "outcome": "actual_job_pass", "reward": 1.0},
        {"file": "src/intent/validator.py", "outcome": "actual_job_fail", "reward": 0.45},
    ])
    return root


def test_collaboration_audit_writes_manifest_state_and_comments():
    root = _repo()

    result = audit_file_collaboration(
        root,
        intent="check if file sim is leading to improving collaboration",
        write=True,
    )

    assert result["schema"] == "file_collaboration_audit/v1"
    assert result["collaboration_score"] > 0.5
    assert result["metrics"]["edge_trend"] == "rising"
    assert result["manifest_state"]["schema"] == "file_manifest_collaboration_state/v1"
    comments = result["manifest_state"]["rooms"][0]["comments"]
    assert comments
    assert comments[0]["to_files"]
    assert "plan" in comments[0]
    assert "quote" in comments[0]
    assert (root / "logs" / "file_collaboration_audit_latest.json").exists()
    assert (root / "logs" / "file_manifest_collaboration_state.json").exists()
    assert result["manifest_sync"]["changed_count"] >= 2
    rendered = (root / "logs" / "file_manifest_collaboration_state.md").read_text(encoding="utf-8")
    assert "File Manifest Collaboration State" in rendered
    assert "File Comments" in rendered
    assert "router.py" in rendered
    folder_manifest = (root / "src" / "intent" / "MANIFEST.md").read_text(encoding="utf-8")
    assert "manifest:file-sim-state" in folder_manifest
    assert "File Sim State" in folder_manifest
    assert "File Proposals" in folder_manifest
    root_manifest = (root / "MANIFEST.md").read_text(encoding="utf-8")
    assert "manifest:global-file-sim-stage" in root_manifest
    assert "Global File Sim Stage" in root_manifest


def test_collaboration_audit_reports_missing_loop_without_packets():
    root = Path(tempfile.mkdtemp(prefix="file_collab_empty_"))
    result = audit_file_collaboration(root, write=False)

    assert result["verdict"] == "no_live_file_collaboration_signal"
    assert result["collaboration_score"] == 0
    assert result["missing_loops"]
