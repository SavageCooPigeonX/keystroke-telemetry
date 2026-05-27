import json
import tempfile
import unittest
from pathlib import Path

from src.unified_manifest_state_seq001_v001 import (
    append_folder_unified_state,
    append_master_persistent_state,
    refresh_master_manifest,
)


class UnifiedManifestStateTests(unittest.TestCase):
    def test_folder_manifest_gets_single_unified_state_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "logs" / "prompt_context_packet_latest.json").write_text(json.dumps({
                "manifest_state_protocol": {
                    "read_set": [{"manifest": "MANIFEST.md"}, {"manifest": "tests/MANIFEST.md"}],
                }
            }), encoding="utf-8")
            (root / "logs" / "operator_syntax_triggers.json").write_text(json.dumps({
                "files": {
                    "src/a.py": {"file": "src/a.py", "observations": 2, "learned_operator_tokens": ["intent", "syntax"]},
                }
            }), encoding="utf-8")

            out = append_folder_unified_state(root, "# MANIFEST - src\n", "src", ["src/a.py"])

            self.assertEqual(out.count("<!-- manifest:folder-unified-state -->"), 1)
            self.assertIn("state_doc: `src/MANIFEST.md`", out)
            self.assertIn("src/a.py", out)

    def test_master_manifest_persists_project_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")
            (root / "src" / "MANIFEST.md").write_text("# Src\n", encoding="utf-8")
            (root / "logs" / "prompt_context_packet_latest.json").write_text(json.dumps({
                "prompt_hash": "abc",
                "manifest_state_protocol": {
                    "status": "manifest_context_loaded",
                    "master_intent_keys": ["src:route:test:minor"],
                },
            }), encoding="utf-8")

            result = refresh_master_manifest(root, ["src/a.py"])
            text = (root / "MANIFEST.md").read_text(encoding="utf-8")

            self.assertTrue(result["changed"])
            self.assertIn("Master Persistent State", text)
            self.assertIn("src:route:test:minor", text)
            self.assertIn("| `src` | `src/MANIFEST.md` | 1 |", text)

    def test_master_state_replaces_old_block(self):
        text = append_master_persistent_state(Path("."), "# Root\n<!-- manifest:master-persistent-state -->old<!-- /manifest:master-persistent-state -->\n", [])

        self.assertEqual(text.count("<!-- manifest:master-persistent-state -->"), 1)


if __name__ == "__main__":
    unittest.main()
