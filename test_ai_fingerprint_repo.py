import json
import shutil
import tempfile
from pathlib import Path

from src.ai_fingerprint_repo_seq001_v001 import build_operator_fingerprint, plug_repo


def test_external_repo_plugs_into_ai_fingerprint_without_training():
    root = Path(tempfile.mkdtemp(prefix="ai_fp_root_"))
    repo = Path(tempfile.mkdtemp(prefix="maif_probe_"))
    (repo / "maif_auditor").mkdir()
    (repo / "README.md").write_text("# MAIF Auditor\nAudit entities across AI models.\n", encoding="utf-8")
    (repo / "maif_auditor" / "engine.py").write_text(
        "class Auditor:\n"
        "    def audit_entity(self):\n"
        "        return {'visibility_score': 8}\n",
        encoding="utf-8",
    )
    (root / "logs").mkdir()
    (root / "logs" / "semantic_profile.json").write_text(
        json.dumps({"schema": "semantic_profile/v1", "facts": {"name": {"value": "Nikita"}}, "intents": {"build": 2}}),
        encoding="utf-8",
    )

    result = plug_repo(root, repo, "maif_auditor", limit=20, train=False)

    assert result["files_indexed"] == 2
    assert result["trained_touches"] == 0
    assert result["privacy"] == "closed"
    assert result["files"][0]["identity"].startswith("maif_auditor")
    assert "term_hashes" in result["files"][0]
    assert "top_terms" not in result["files"][0]
    assert result["repo"].startswith("closed:maif_auditor:")
    assert result["ai_fingerprint"]["facts"]["name"]["value"] == "Nikita"
    assert json.dumps(result)
    assert (root / "logs" / "repo_fingerprint_maif_auditor.json").exists()
    assert (root / "logs" / "ai_fingerprint.json").exists()


def test_closed_repo_training_redacts_touch_preview():
    root = Path(tempfile.mkdtemp(prefix="ai_fp_closed_train_"))
    repo = Path(tempfile.mkdtemp(prefix="closed_probe_"))
    (root / "logs").mkdir()
    (root / "src").mkdir()
    source_numeric = next((Path(__file__).resolve().parent / "src").glob("intent_numeric_seq001*.py"))
    shutil.copy(source_numeric, root / "src" / source_numeric.name)
    (repo / "engine.py").write_text("def secret_entity_pipeline():\n    return 'classified'\n", encoding="utf-8")

    result = plug_repo(root, repo, "closed_repo", limit=5, train=True)
    touches = (root / "logs" / "private_numeric_training.jsonl").read_text(encoding="utf-8")

    assert result["trained_touches"] == 1
    assert "secret_entity_pipeline" not in touches
    assert "prompt_hash" in touches


def test_operator_fingerprint_uses_prompt_terms_and_semantic_intents():
    root = Path(tempfile.mkdtemp(prefix="ai_fp_terms_"))
    logs = root / "logs"
    logs.mkdir()
    (logs / "semantic_profile.json").write_text(
        json.dumps({"schema": "semantic_profile/v1", "facts": {}, "intents": {"intent_system_design": 3}}),
        encoding="utf-8",
    )
    (logs / "prompt_journal.jsonl").write_text(
        json.dumps({"msg": "maif prompt encoding context selection"}) + "\n",
        encoding="utf-8",
    )

    fingerprint = build_operator_fingerprint(root)

    assert fingerprint["semantic_intents"]["intent_system_design"] == 3
    assert fingerprint["top_prompt_terms"][0][0] in {"maif", "prompt", "encoding", "context", "selection"}
    assert fingerprint["numeric_signature"]["vector"]
