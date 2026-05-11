import tempfile
import unittest
from pathlib import Path

from src.manifest_state_cycle_seq001_v001 import apply_manifest_state_cycle


class ManifestStateCycleTests(unittest.TestCase):
    def test_files_write_bounded_state_to_own_folder_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "macro" / "session_macro_cycle_seq001_v001.py"
            target.parent.mkdir(parents=True)
            target.write_text('"""session macro cycle prompt grouping."""\n', encoding="utf-8")
            (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")
            (root / "src" / "macro" / "MANIFEST.md").write_text("# Macro\n", encoding="utf-8")

            result = apply_manifest_state_cycle(
                root,
                "session macro cycle prompt grouping should write manifest state",
                focus_files=["src/macro/session_macro_cycle_seq001_v001.py"],
            )

            self.assertEqual(result["schema"], "manifest_state_write_cycle/v1")
            self.assertTrue(any(row["manifest"] == "src/macro/MANIFEST.md" for row in result["file_writes"]))
            self.assertEqual(result["folder_context_coupling"]["schema"], "folder_context_coupling/v1")
            text = (root / "src" / "macro" / "MANIFEST.md").read_text(encoding="utf-8")
            self.assertIn("Folder Unified State", text)
            self.assertTrue((root / "logs" / "manifest_state_write_latest.json").exists())


if __name__ == "__main__":
    unittest.main()
