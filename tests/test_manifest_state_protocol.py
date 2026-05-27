import tempfile
import unittest
from pathlib import Path

from src.manifest_state_protocol_seq001_v001 import build_manifest_state_protocol, render_manifest_state_prompt


class ManifestStateProtocolTests(unittest.TestCase):
    def test_manifest_state_requires_read_set_and_local_write_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "alpha").mkdir(parents=True)
            (root / "src" / "beta").mkdir(parents=True)
            (root / "MANIFEST.md").write_text("# Master\n", encoding="utf-8")
            (root / "src" / "alpha" / "MANIFEST.md").write_text("# Alpha\n", encoding="utf-8")
            (root / "src" / "beta" / "MANIFEST.md").write_text("# Beta\n", encoding="utf-8")
            graph = {"intents": [{
                "intent_key": "src/alpha:route:syntax_trigger:minor",
                "segment": "syntax trigger",
                "manifest_path": "src/alpha/MANIFEST.md",
                "files": ["src/beta/tool.py"],
            }]}

            protocol = build_manifest_state_protocol(root, graph, {}, ["src/alpha/file.py"])

            self.assertEqual(protocol["status"], "manifest_context_loaded")
            read_set = {row["manifest"] for row in protocol["read_set"]}
            self.assertIn("MANIFEST.md", read_set)
            self.assertIn("src/alpha/MANIFEST.md", read_set)
            self.assertIn("src/beta/MANIFEST.md", read_set)
            writes = {row["may_write"] for row in protocol["write_boundary"]}
            self.assertIn("src/alpha/MANIFEST.md", writes)
            self.assertIn("src/beta/MANIFEST.md", writes)

    def test_prompt_render_names_shattered_keys(self):
        protocol = {
            "status": "manifest_context_loaded",
            "read_set": [{"manifest": "MANIFEST.md", "exists": True, "hash": "abc"}],
            "shattered_intent_keys": [{"intent_key": "root:route:test:minor", "manifest": "MANIFEST.md", "numeric_bins": [1, 0]}],
        }

        text = "\n".join(render_manifest_state_prompt(protocol))

        self.assertIn("Codex/Copilot must read", text)
        self.assertIn("root:route:test:minor", text)


if __name__ == "__main__":
    unittest.main()
