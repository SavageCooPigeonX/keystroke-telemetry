import json
import tempfile
from pathlib import Path

from src.file_self_sim_learning_seq001_v001 import (
    record_file_learning_outcome,
    simulate_file_self_learning,
)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="file_self_learning_"))
    (root / "logs" / "file_memory").mkdir(parents=True)
    (root / "src" / "intent").mkdir(parents=True)
    (root / "src" / "intent" / "MANIFEST.md").write_text(
        "# Intent\nrouter owns intent selection\nvalidator owns safety gates\n",
        encoding="utf-8",
    )
    router = "def route_intent(prompt):\n    return {'prompt': prompt, 'scope': 'src/intent'}\n"
    (root / "src" / "intent" / "router.py").write_text(router, encoding="utf-8")
    (root / "src" / "intent" / "validator.py").write_text(
        "def validate(packet):\n    return bool(packet.get('intent_key'))\n",
        encoding="utf-8",
    )
    (root / "test_router.py").write_text(
        "from src.intent.router import route_intent\n\n"
        "def test_route_intent():\n"
        "    assert route_intent('x')['scope'] == 'src/intent'\n",
        encoding="utf-8",
    )
    (root / "logs" / "batch_rewrite_sim_latest.json").write_text(json.dumps({
        "intent": {
            "raw": "compile intent self splitting interlinked validation",
            "intent_key": "src/intent:build:self_splitting_learning:major",
            "scope": "src/intent",
            "target": "self_splitting_learning",
            "scale": "major",
        },
        "proposals": [
            {
                "path": "src/intent/router.py",
                "confidence": 0.7,
                "interlink_score": 0.8,
                "approval_gate": "operator_required",
                "context_injection": [
                    "src/intent/router.py",
                    "src/intent/validator.py",
                    "src/intent/MANIFEST.md",
                ],
                "validation_plan": [
                    "py -m py_compile src/intent/router.py",
                    "py -m pytest test_router.py -q",
                ],
                "cross_file_validation": {
                    "exists": True,
                    "dirty": False,
                    "imports": [],
                    "referenced_by": ["test_router.py"],
                },
                "ten_q": {"passed": True, "score": 9},
            }
        ],
    }), encoding="utf-8")
    (root / "logs" / "file_job_council_latest.json").write_text(json.dumps({
        "jobs": [
            {
                "captain": "src/intent/router.py",
                "files": ["src/intent/router.py", "src/intent/validator.py"],
                "context_files": ["src/intent/MANIFEST.md", "test_router.py"],
            }
        ],
        "context_packs": [
            {
                "pack_id": "pack-primary",
                "files": ["src/intent/router.py", "src/intent/validator.py", "test_router.py"],
            }
        ],
        "relationships": [
            {
                "from": "src/intent/router.py",
                "to": "src/intent/validator.py",
                "type": "friendship",
            }
        ],
    }), encoding="utf-8")
    memory_path = root / "logs" / "file_memory" / "src__intent__router.py.json"
    memory_path.write_text(json.dumps({
        "messages": [
            {
                "commands": {
                    "remember": ["router owns intent wake order"],
                    "use": ["src/intent/validator.py before rewrite"],
                    "avoid": ["self-overwrite without validation"],
                    "style": ["specific and operator-aligned"],
                },
                "body_preview": "router remembers it should wake validator before rewrite",
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "file_memory_index.json").write_text(json.dumps({
        "files": [
            {
                "file": "src/intent/router.py",
                "messages": 1,
                "path": "logs/file_memory/src__intent__router.py.json",
                "markdown": "logs/file_memory/src__intent__router.py.md",
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "file_identity_growth.jsonl").write_text(
        json.dumps({
            "file": "src/intent/router.py",
            "growth_tags": ["compile", "intent", "self", "splitting", "interlinked"],
            "interlink_score": 0.8,
        }) + "\n",
        encoding="utf-8",
    )
    (root / "logs" / "dead_token_collective_pairs.jsonl").write_text(
        json.dumps({
            "new_path": "src/intent/router.py",
            "subject": "route intent through validator",
            "intent_key": "src/intent:patch:route_intent:patch",
        }) + "\n",
        encoding="utf-8",
    )
    (root / "logs" / "intent_vocab.json").write_text(json.dumps({
        "word_to_id": {
            "compile": 1,
            "intent": 2,
            "self": 3,
            "splitting": 4,
            "interlinked": 5,
            "validation": 6,
        }
    }), encoding="utf-8")
    (root / "logs" / "intent_matrix.json").write_text(json.dumps({
        "matrix": {"router": {"1": 0.2, "2": 0.4, "3": 0.2, "4": 0.2, "5": 0.1, "6": 0.2}}
    }), encoding="utf-8")
    return root


def test_file_self_learning_writes_deepseek_packets_and_profiles():
    root = _repo()
    original = (root / "src" / "intent" / "router.py").read_text(encoding="utf-8")

    result = simulate_file_self_learning(
        root,
        "compile intent self splitting interlinked validation",
        limit=4,
        write=True,
    )

    assert result["schema"] == "file_self_sim_learning/v1"
    assert result["mode"] == "learning_only_no_overwrite"
    assert result["wake_order"]
    assert result["wake_order"][0]["file"] == "src/intent/router.py"
    assert result["wake_order"][0]["role"] == "top_waker"
    assert result["learning_packets"]
    packet = result["learning_packets"][0]
    assert packet["schema"] == "deepseek_file_learning_packet/v1"
    assert packet["overwrite_readiness"]["allowed"] is False
    assert packet["verification_packet"]["validation_plan"]
    assert packet["backward_learning_targets"]
    assert "Do not overwrite source" in packet["deepseek_instruction"]
    assert (root / "src" / "intent" / "router.py").read_text(encoding="utf-8") == original
    assert (root / "logs" / "file_self_sim_learning_latest.json").exists()
    assert (root / "logs" / "deepseek_learning_packets.jsonl").exists()
    assert (root / "logs" / "file_self_sim_learning_email.md").exists()
    rendered = (root / "logs" / "file_self_sim_learning.md").read_text(encoding="utf-8")
    assert "File Self-Sim Learning Mode" in rendered
    assert "Backward Learning Pass" in rendered
    email = (root / "logs" / "file_self_sim_learning_email.md").read_text(encoding="utf-8")
    assert "emergency rewrite meeting" in email
    assert "grader" in email.lower()
    assert "What the files learned while arguing:" in email
    assert "Overheard in the file room:" in email
    assert "I woke first" in email
    assert "What DeepSeek should receive" in email
    assert "Routing crumbs under the floorboards:" in email
    profiles = json.loads((root / "file_profiles.json").read_text(encoding="utf-8"))
    assert profiles["router"]["self_sim_profile"]["file"] == "src/intent/router.py"
    assert profiles["router"]["learning_history"]


def test_file_learning_outcome_records_backward_learning():
    root = _repo()
    result = simulate_file_self_learning(root, "compile intent self splitting", limit=2, write=True)
    packet_id = result["learning_packets"][0]["packet_id"]

    record = record_file_learning_outcome(
        root,
        packet_id,
        outcome="compile_pass",
        reward=0.82,
        details={"tests": "passed"},
    )

    assert record["schema"] == "file_self_sim_learning_outcome/v1"
    assert record["packet_id"] == packet_id
    profiles = json.loads((root / "file_profiles.json").read_text(encoding="utf-8"))
    assert profiles["router"]["learning_outcomes"][-1]["outcome"] == "compile_pass"
    assert profiles["validator"]["learning_outcomes"]


def test_file_learning_emits_relationship_graph_registry_and_split_jobs():
    root = _repo()
    big_path = root / "src" / "intent" / "big_router_seq009_v002.py"
    big_path.write_text(
        "\n".join(f"def route_part_{i}():\n    return {i}\n" for i in range(18)),
        encoding="utf-8",
    )
    (root / "test_big_router.py").write_text(
        "from src.intent.big_router_seq009_v002 import route_part_0\n\n"
        "def test_route_part_0():\n"
        "    assert route_part_0() == 0\n",
        encoding="utf-8",
    )
    latest = json.loads((root / "logs" / "batch_rewrite_sim_latest.json").read_text(encoding="utf-8"))
    latest["proposals"].append({
        "path": "src/intent/big_router_seq009_v002.py",
        "confidence": 0.8,
        "interlink_score": 0.7,
        "approval_gate": "operator_required",
        "context_injection": [
            "src/intent/big_router_seq009_v002.py",
            "src/intent/validator.py",
            "src/intent/MANIFEST.md",
        ],
        "validation_plan": [
            "py -m py_compile src/intent/big_router_seq009_v002.py",
            "py -m pytest test_big_router.py -q",
        ],
        "cross_file_validation": {
            "exists": True,
            "dirty": False,
            "imports": [],
            "referenced_by": ["test_big_router.py"],
        },
        "ten_q": {"passed": True, "score": 9},
    })
    (root / "logs" / "batch_rewrite_sim_latest.json").write_text(json.dumps(latest), encoding="utf-8")

    result = simulate_file_self_learning(
        root,
        "split over cap architecture sequence big router validation",
        limit=5,
        write=True,
        source_result=latest,
        config={"soft_line_cap": 20, "warn_line_cap": 30, "hard_line_cap": 40},
    )

    registry = result["architecture_sequence_registry"]
    big_identity = next(item for item in registry["files"] if item["file"] == "src/intent/big_router_seq009_v002.py")
    assert big_identity["arch_seq"].startswith("A-")
    assert big_identity["local_seq"] == "seq009"
    assert big_identity["version"] == "v002"
    assert big_identity["size_state"] == "critical"
    assert (root / "logs" / "file_identity_registry.json").exists()

    graph = result["relationship_graph"]
    assert graph["edges"]
    assert any(edge["relation"] in {"friendship", "context_pack", "backward_target"} for edge in graph["edges"])
    assert (root / "logs" / "file_relationship_graph.json").exists()

    split_job = next(job for job in result["overcap_split_jobs"] if job["file"] == "src/intent/big_router_seq009_v002.py")
    assert split_job["deepseek_mode"] == "split_plan_only_no_source_write"
    assert split_job["approval_gate"] == "operator_required"
    assert split_job["proposed_children"]
    assert "facade" in " ".join(child["role"] for child in split_job["proposed_children"])
    assert (root / "logs" / "overcap_split_jobs.json").exists()

    packet = next(packet for packet in result["learning_packets"] if packet["file"] == "src/intent/big_router_seq009_v002.py")
    assert packet["split_plan_request"]["needed"] is True
    assert packet["relationship_weight"] > 0
    assert packet["validation_confidence"] > 0
    profiles = json.loads((root / "file_profiles.json").read_text(encoding="utf-8"))
    assert profiles["big_router"]["self_sim_profile"]["split_plan_request"]["needed"] is True
