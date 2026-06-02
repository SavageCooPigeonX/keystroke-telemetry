import json
from pathlib import Path

from src.hush_maif_interface_seq001_v001 import build_hush_maif_interface


def _root(tmp_path: Path) -> Path:
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "repo_fingerprint_maif_auditor.json").write_text(json.dumps({
        "schema": "repo_fingerprint/v1",
        "label": "maif_auditor",
        "privacy": "closed",
        "files_indexed": 3,
        "files": [
            {"identity": "maif_auditor_directory_route_entity"},
            {"identity": "maif_auditor_production_auditor_pipeline"},
            {"identity": "maif_auditor_hush_chat_core"},
        ],
    }), encoding="utf-8")
    return tmp_path


def test_hush_maif_interface_builds_entity_sim_frontend_packet(tmp_path: Path):
    root = _root(tmp_path)

    packet = build_hush_maif_interface(
        root,
        "Hush entity sim for Audit SavageCooPigeonX marked staged docs copy file",
    )

    assert packet["surface"] == "myaifingerprint.com"
    assert packet["role"] == "maif_information_interface"
    assert packet["frontend_intent"] == "entity_sim"
    assert packet["first_run_notice"]["required"] is True
    assert packet["entity_sim"]
    assert packet["entity_sim"][0]["schema"] == "hush_entity_sim/v1"
    assert packet["entity_sim"][0]["sim_state"] == "marked_staged"
    assert "raw_source_exfiltration" in packet["entity_sim"][0]["blocked_actions"]
    assert packet["frontend_cards"]
    assert packet["operator_network_capability"]["status"] == "read_only_entity_sim"
    assert (root / "logs" / "hush_maif_interface_latest.json").exists()
