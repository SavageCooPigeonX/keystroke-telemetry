import json
import tempfile
import unittest
from pathlib import Path

from src.opus_micro_pulse_runtime_seq001_v001 import (
    build_opus_micro_pulse_runtime,
    classify_prompt,
)


class OpusMicroPulseRuntimeTests(unittest.TestCase):
    def test_prompt_classification_blocks_conversation_from_file_sim(self):
        result = classify_prompt("what do you think about this idea maybe files should learn from pauses")

        self.assertIn(result["prompt_class"], {"conversation", "exploration"})
        self.assertFalse(result["durable_mutation_allowed"])
        self.assertIn(result["sim_policy"], {"learning_packet_only", "hypothesis_packet"})

    def test_complex_runtime_prompt_creates_pulses_cannon_and_manifest_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "src").mkdir()
            (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")
            (root / "src" / "MANIFEST.md").write_text("# Src\n", encoding="utf-8")
            (root / "ROOT_SIM_KEYS.md").write_text("# Root Sim Keys\n", encoding="utf-8")
            (root / "src" / "root_sim_key_file_seq001_v001.py").write_text('"""Root navigation key."""\n', encoding="utf-8")
            (root / "src" / "unified_manifest_state_seq001_v001.py").write_text('"""Unified manifest state."""\n', encoding="utf-8")
            (root / "src" / "file_bug_chat_seq001_v001.py").write_text('"""File bug chat."""\n', encoding="utf-8")
            (root / "logs" / "operator_syntax_triggers.json").write_text(json.dumps({
                "files": {
                    "src/root_sim_key_file_seq001_v001.py": {
                        "file": "src/root_sim_key_file_seq001_v001.py",
                        "tokens": ["root", "sim", "keys", "file", "comments"],
                        "syntax_tokens": ["root", "sim", "keys"],
                        "learned_operator_tokens": ["cutoff", "comments"],
                        "observations": 2,
                    },
                    "src/unified_manifest_state_seq001_v001.py": {
                        "file": "src/unified_manifest_state_seq001_v001.py",
                        "tokens": ["manifest", "state", "folder", "persistent"],
                        "syntax_tokens": ["manifest", "state"],
                        "learned_operator_tokens": ["folder", "manifest"],
                        "observations": 3,
                    },
                }
            }), encoding="utf-8")
            (root / "logs" / "file_bug_surface_latest.json").write_text(json.dumps({
                "bugs": [{
                    "owner": "src/root_sim_key_file_seq001_v001.py",
                    "severity": "P1",
                    "title": "comment cutoff stale renderer",
                    "next_action": "render full notes",
                }]
            }), encoding="utf-8")
            row = {
                "session_n": 900,
                "session_id": "test-session",
                "source": "unit",
                "msg": (
                    "perfect build the self calibrating opus micro pulse runtime so files talk in manifests "
                    "and Codex learns from backward diff"
                ),
                "rewrites": [
                    {"old": "micro", "new": "opus micro pulse runtime"},
                    {"old": "diff", "new": "backward diff and touched file learning"},
                ],
                "signals": {"hesitation_count": 8},
            }

            result = build_opus_micro_pulse_runtime(root, prompt_row=row, write=True)
            markdown = (root / "logs" / "opus_micro_pulse.md").read_text(encoding="utf-8")
            root_manifest = (root / "MANIFEST.md").read_text(encoding="utf-8")

            self.assertEqual(result["schema"], "opus_micro_pulse_runtime/v1")
            self.assertGreaterEqual(result["pulse_count"], 2)
            self.assertEqual(result["cannon_job"]["executor_session"], "codex_execution_session")
            self.assertIn("src/root_sim_key_file_seq001_v001.py", result["cannon_job"]["predicted_files"])
            self.assertEqual(result["cannon_job"]["executor_prompt_path"], "logs/opus_executor_prompt_latest.md")
            self.assertIn("Use the raw operator prompt only as fallback evidence", result["cannon_job"]["executor_prompt"])
            self.assertTrue((root / "logs" / "opus_executor_prompt_latest.md").exists())
            self.assertIn("Opus Cannon Bootstrap", (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8"))
            self.assertIn("I was touched by Opus", markdown)
            self.assertIn("Pending Backward Learning", markdown)
            self.assertIn("Opus Micro-Pulse Runtime", root_manifest)

    def test_real_prompt_history_tail_simulates_when_available(self):
        root = Path(__file__).resolve().parents[1]
        journal = root / "logs" / "prompt_journal.jsonl"
        if not journal.exists():
            self.skipTest("prompt journal unavailable")

        result = build_opus_micro_pulse_runtime(root, write=False, max_pulses=3, file_limit=8)

        self.assertGreaterEqual(result["pulse_count"], 1)
        self.assertTrue(result["cannon_job"]["sealed_intent_keys"])
        self.assertIn("expanded_task", result["cannon_job"])
        self.assertEqual(
            result["pending_backward_learning"]["metric"],
            "opus_dynamic_file_intelligence_prediction_vs_codex_execution_diff",
        )


if __name__ == "__main__":
    unittest.main()
