import json
import tempfile
import unittest
from pathlib import Path

from src.root_sim_key_file_seq001_v001 import build_root_sim_key_file


class RootSimKeyFileTests(unittest.TestCase):
    def test_merges_prompt_probe_and_bug_chat_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "logs" / "prompt_context_packet_latest.json").write_text(json.dumps({
                "intent_key_encoding": {"intents": [{
                    "intent_key": "src:route:test:minor",
                    "segment": "test segment",
                    "files": ["src/a.py"],
                }]},
                "manifest_state_protocol": {"shattered_intent_keys": [{
                    "intent_key": "src:route:test:minor",
                    "segment": "test shard",
                    "files": ["src/a.py"],
                }]},
            }), encoding="utf-8")
            (root / "logs" / "copilot_probe_push_cycle_latest.json").write_text(json.dumps({
                "file_sim_orchestration": {"waking_files": [{"name": "tc_gemini", "sources": ["graph"]}]}
            }), encoding="utf-8")
            (root / "logs" / "file_bug_chat_latest.json").write_text(json.dumps({
                "comments": [{
                    "owner": "logs/x.jsonl",
                    "intent_key": "logs_x:repair:stale:p1",
                    "why_touched": "stale lane",
                    "operator_comedy": "I keep getting touched because stale.",
                    "coding_agent_note": "Verify this evidence first: stale.",
                    "opus_manager_note": "P1 owner=logs/x.jsonl",
                    "learned_from_sim": "first trace",
                    "interlink_score": 8,
                }]
            }), encoding="utf-8")

            result = build_root_sim_key_file(root, write=True)
            text = (root / "ROOT_SIM_KEYS.md").read_text(encoding="utf-8")
            manifest = (root / "src" / "MANIFEST.md").read_text(encoding="utf-8")

            self.assertEqual(result["called_count"], 3)
            self.assertEqual(result["attention_selected_count"], 3)
            self.assertIn("src/a.py", text)
            self.assertIn("tc_gemini", text)
            self.assertIn("I keep getting touched", text)
            self.assertIn("Coding Agent Note", text)
            self.assertIn("Verify this evidence first", text)
            self.assertIn("Live Sim Call Receipts", manifest)
            self.assertIn("src/a.py", manifest)


if __name__ == "__main__":
    unittest.main()
