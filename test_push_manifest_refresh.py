import json
from pathlib import Path

from scripts.refresh_push_manifests import refresh_push_manifests


def test_refresh_push_manifest_adds_intent_comments_and_boundaries(tmp_path):
    root = tmp_path
    src = root / "src"
    logs = root / "logs"
    src.mkdir()
    logs.mkdir()
    (src / "alpha.py").write_text('"""alpha module."""\n\ndef run():\n    return True\n', encoding="utf-8")
    (logs / "intent_keys.jsonl").write_text(json.dumps({
        "intent_key": "src:document:manifest:patch",
        "scope": "src",
        "manifest_path": "src/MANIFEST.md",
        "prompt": "manifest should store intent keys",
    }) + "\n", encoding="utf-8")
    (logs / "file_self_knowledge_latest.json").write_text(json.dumps({
        "packets": [{"file": "src/alpha.py", "file_quote": "alpha says manifests need comments"}]
    }), encoding="utf-8")

    result = refresh_push_manifests(
        root,
        folders=[src],
        changed_files=["src/alpha.py"],
    )

    text = (src / "MANIFEST.md").read_text(encoding="utf-8")
    assert result["changed_count"] == 1
    assert "## Push Intent Keys" in text
    assert "src:document:manifest:patch" in text
    assert "alpha says manifests need comments" in text
    assert "Numeric Encoding Boundary" in text


def test_refresh_push_manifest_preserves_file_sim_state_block(tmp_path):
    root = tmp_path
    src = root / "src"
    src.mkdir()
    (root / "logs").mkdir()
    (src / "alpha.py").write_text('"""alpha module."""\n', encoding="utf-8")
    (src / "MANIFEST.md").write_text(
        "# Old\n\n"
        "<!-- manifest:file-sim-state -->\n"
        "## File Sim State\n\n"
        "- alpha remembers beta\n"
        "<!-- /manifest:file-sim-state -->\n",
        encoding="utf-8",
    )

    refresh_push_manifests(root, folders=[src], changed_files=["src/alpha.py"])

    text = (src / "MANIFEST.md").read_text(encoding="utf-8")
    assert "manifest:push-intent-state" in text
    assert "manifest:file-sim-state" in text
    assert "alpha remembers beta" in text
