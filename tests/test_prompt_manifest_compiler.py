import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.prompt_manifest_compiler_seq001_v001 import build_prompt_context_packet, decode_file_intent


def _load_push_audit_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "run_deepseek_push_audit.py"
    spec = importlib.util.spec_from_file_location("run_deepseek_push_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptManifestCompilerTests(unittest.TestCase):
    def test_decode_file_intent_treats_file_name_as_changelog(self):
        row = decode_file_intent("src/tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer.py")

        self.assertEqual(row["seq"], "001")
        self.assertEqual(row["version"], "004")
        self.assertEqual(row["date_code"], "0421")
        self.assertIn("gemini api call system prompt", row["encoded_intent"])

    def test_prompt_packet_writes_opus_session_and_prompt_box(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "MANIFEST.md").write_text("# Master\n", encoding="utf-8")
            packet = build_prompt_context_packet(
                root,
                "sync file sim before codex acts",
                focus_files=["src/example_seq001_v001__file_sim_context_probe.py"],
                write=True,
            )

            self.assertEqual(packet["role_contract"]["master_manifest_session"], "opus_repo_orchestrator")
            self.assertTrue((root / "logs" / "prompt_context_packet_latest.json").exists())
            prompt_box = (root / "logs" / "copilot_prompt_box_latest.md").read_text(encoding="utf-8")
            self.assertIn("file-name-intent:file sim context probe", prompt_box)

    def test_latest_prompt_reader_accepts_prompt_journal_msg_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "MANIFEST.md").write_text("# Master\n", encoding="utf-8")
            (root / "logs" / "prompt_journal.jsonl").write_text(
                json.dumps({"msg": "build opus pulse from real prompt journal"}) + "\n",
                encoding="utf-8",
            )

            packet = build_prompt_context_packet(root, "", focus_files=[], write=True)

            self.assertEqual(packet["operator_prompt"], "build opus pulse from real prompt journal")
            self.assertNotEqual(packet["prompt_hash"], "e3b0c44298fc1c14")

    def test_deepseek_push_audit_queues_advisory_job(self):
        module = _load_push_audit_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "logs").mkdir()
            (root / "MANIFEST.md").write_text("# Master\n", encoding="utf-8")
            changed = ["src/example_seq001_v001__audit_prompt_manifest.py"]

            with patch.object(module, "_git_changed_files", return_value=changed):
                packet = module.build_deepseek_push_audit(root, write=True)

            self.assertEqual(packet["state_contract"]["write_policy"], "advisory_packet_only")
            job = json.loads((root / "logs" / "deepseek_prompt_jobs.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(job["mode"], "deepseek_push_code_audit")
            self.assertIn("file-name changelog mismatches", packet["deepseek_prompt"])


if __name__ == "__main__":
    unittest.main()
