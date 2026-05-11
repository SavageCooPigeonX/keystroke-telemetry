import json
import tempfile
import unittest
from pathlib import Path

from src.cannon_execution_gate_seq001_v001 import build_cannon_execution_gate
from src.opus_micro_pulse_runtime_seq001_v001 import build_opus_micro_pulse_runtime


class CannonExecutionGateTests(unittest.TestCase):
    def test_blocks_when_cannon_payload_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()

            result = build_cannon_execution_gate(root, "build the thing", write=True)

            self.assertFalse(result["cleared"])
            self.assertEqual(result["status"], "blocked")
            self.assertIn("missing_or_unreadable:logs/prompt_cannon_job_latest.json", result["blockers"])
            self.assertTrue((root / "logs" / "cannon_execution_gate_latest.json").exists())

    def test_clears_after_opus_micro_pulse_creates_cannon_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")
            (root / "src" / "MANIFEST.md").write_text("# Src\n", encoding="utf-8")
            (root / "src" / "unified_manifest_state_seq001_v001.py").write_text('"""Unified manifest state."""\n', encoding="utf-8")
            (root / "logs" / "operator_syntax_triggers.json").write_text(json.dumps({
                "files": {
                    "src/unified_manifest_state_seq001_v001.py": {
                        "file": "src/unified_manifest_state_seq001_v001.py",
                        "tokens": ["build", "manifest", "cannon", "payload"],
                        "syntax_tokens": ["manifest", "state"],
                        "learned_operator_tokens": ["cannon", "payload"],
                        "observations": 2,
                    }
                }
            }), encoding="utf-8")
            prompt = "build the cannon payload gate before codex can mutate files"

            build_opus_micro_pulse_runtime(root, prompt, write=True)
            result = build_cannon_execution_gate(root, prompt, write=True)

            self.assertTrue(result["cleared"])
            self.assertEqual(result["status"], "cleared")
            self.assertEqual(result["executor_session"], "codex_execution_session")
            self.assertGreater(result["predicted_file_count"], 0)
            self.assertEqual(result["executor_prompt_path"], "logs/opus_executor_prompt_latest.md")
            self.assertTrue(result["executor_prompt_ready"])


if __name__ == "__main__":
    unittest.main()
