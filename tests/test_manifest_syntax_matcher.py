import tempfile
import unittest
from pathlib import Path

from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax


class ManifestSyntaxMatcherTests(unittest.TestCase):
    def test_manifest_self_selects_by_folder_and_system_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "thought_completer").mkdir(parents=True)
            (root / "src" / "thought_completer" / "MANIFEST.md").write_text(
                "# thought completer\n\nprompt context syntax trigger orchestration\n",
                encoding="utf-8",
            )
            (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")

            result = match_manifest_syntax(root, "thought completer prompt syntax orchestration", write=True)

            self.assertEqual(result["schema"], "manifest_syntax_match/v1")
            self.assertEqual(result["selected_manifests"][0]["manifest"], "src/thought_completer/MANIFEST.md")
            self.assertIn("numeric", result["selected_manifests"][0])
            self.assertTrue((root / "logs" / "manifest_syntax_match_latest.json").exists())


if __name__ == "__main__":
    unittest.main()
