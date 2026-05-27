import json
import tempfile
import unittest
from pathlib import Path

from src.file_bug_surface_seq001_v001 import build_file_bug_surface
from src.unified_manifest_state_seq001_v001 import append_master_persistent_state


class FileBugSurfaceTests(unittest.TestCase):
    def test_stale_lanes_surface_as_master_bugs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "pipeline_staleness_audit_latest.json").write_text(json.dumps({
                "stale": [{
                    "name": "deepseek_results",
                    "path": "logs/deepseek_prompt_results.jsonl",
                    "age_minutes": 99,
                    "max_age_minutes": 10,
                    "entries": 1,
                }],
                "cognitive_probe_health": {"status": "weak", "unknown_ratio": 0.5, "coverage_gap": 7},
                "major_file_opinions": [{
                    "file": "src/example.py",
                    "stance": "I see stale results",
                    "stale_dependencies": ["deepseek_results"],
                }],
            }), encoding="utf-8")

            surface = build_file_bug_surface(root, write=True)

            self.assertGreaterEqual(surface["bug_count"], 3)
            self.assertEqual(surface["most_logical_autonomous_action"], "repair DeepSeek result receipt lane, then rerun file-sim code job closure")
            self.assertTrue((root / "logs" / "file_bug_surface_latest.json").exists())

    def test_master_manifest_renders_surfaced_bug_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "file_bug_surface_latest.json").write_text(json.dumps({
                "bugs": [{
                    "severity": "P1",
                    "owner": "logs/x.jsonl",
                    "title": "stale pipeline lane",
                    "next_action": "repair receipts",
                }]
            }), encoding="utf-8")

            text = append_master_persistent_state(root, "# Root\n", [])

            self.assertIn("Surfaced Bug Queue", text)
            self.assertIn("repair receipts", text)


if __name__ == "__main__":
    unittest.main()
