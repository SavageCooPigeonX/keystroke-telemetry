import json
import tempfile
import unittest
from pathlib import Path

from src.folder_context_coupling_seq001_v001 import build_folder_context_coupling


class FolderContextCouplingTests(unittest.TestCase):
    def test_folder_coupling_prefers_local_but_reports_external_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src" / "alpha").mkdir(parents=True)
            (root / "src" / "beta").mkdir(parents=True)
            (root / "src" / "alpha" / "MANIFEST.md").write_text("# Alpha\nmanifest syntax sim\n", encoding="utf-8")
            (root / "src" / "beta" / "MANIFEST.md").write_text("# Beta\nvalidation peer\n", encoding="utf-8")
            (root / "src" / "alpha" / "a.py").write_text("def manifest_syntax_sim():\n    return True\n", encoding="utf-8")
            (root / "src" / "beta" / "b.py").write_text("def validation_peer():\n    return True\n", encoding="utf-8")
            (root / "logs" / "operator_syntax_triggers.json").write_text(json.dumps({
                "files": {
                    "src/alpha/a.py": {"file": "src/alpha/a.py", "observations": 3},
                }
            }), encoding="utf-8")
            (root / "logs" / "file_relationship_graph.json").write_text(json.dumps({
                "edges": [{
                    "from": "src/alpha/a.py",
                    "to": "src/beta/b.py",
                    "weight": 0.8,
                }]
            }), encoding="utf-8")

            report = build_folder_context_coupling(root, "manifest syntax sim validation peer", focus_files=["src/alpha/a.py"])

            folders = {row["folder"]: row for row in report["folders"]}
            self.assertIn("src/alpha", folders)
            self.assertEqual(folders["src/alpha"]["folder"], "src/alpha")
            self.assertTrue(folders["src/alpha"]["operator_label"].endswith("-inator"))
            self.assertIn("alpha", folders["src/alpha"]["identity_tokens"])
            self.assertIn("identity_tokens", folders["src/alpha"])
            self.assertTrue(report["cross_folder_edges"])
            self.assertTrue(report["package_rankings"])
            self.assertEqual(report["deepseek_manifest_manager"]["mode"], "manifest_manager_advisory")
            self.assertTrue((root / "logs" / "folder_context_coupling_latest.json").exists())


if __name__ == "__main__":
    unittest.main()
