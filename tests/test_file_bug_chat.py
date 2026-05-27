import json
import tempfile
import unittest
from pathlib import Path

from src.file_bug_chat_seq001_v001 import build_file_bug_chat
from src.unified_manifest_state_seq001_v001 import append_master_persistent_state


class FileBugChatTests(unittest.TestCase):
    def test_builds_operator_and_opus_layers_for_bugs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "file_bug_surface_latest.json").write_text(json.dumps({
                "bugs": [{
                    "bug_id": "stale:deepseek_results",
                    "owner": "logs/deepseek_prompt_results.jsonl",
                    "severity": "P1",
                    "source": "pipeline_staleness_audit",
                    "title": "stale pipeline lane: deepseek_results",
                    "evidence": "age=99m deps=code_completion_jobs",
                    "next_action": "verify receipts",
                }]
            }), encoding="utf-8")

            chat = build_file_bug_chat(root, write=True)

            self.assertEqual(chat["comment_count"], 1)
            comment = chat["comments"][0]
            self.assertIn("I keep getting touched", comment["operator_comedy"])
            self.assertIn("Verify this evidence first", comment["coding_agent_note"])
            self.assertIn("intent_key", comment["opus_manager_note"])
            self.assertGreaterEqual(comment["interlink_score"], 8)

    def test_master_manifest_can_include_bug_chat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "file_bug_chat_latest.json").write_text(json.dumps({
                "comments": [{
                    "owner": "logs/x.jsonl",
                    "operator_comedy": "I keep getting touched because receipts are stale.",
                }]
            }), encoding="utf-8")

            text = append_master_persistent_state(root, "# Root\n", [])

            self.assertIn("File Bug Chat", text)
            self.assertIn("receipts are stale", text)


if __name__ == "__main__":
    unittest.main()
