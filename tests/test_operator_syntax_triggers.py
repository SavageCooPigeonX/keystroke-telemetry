import tempfile
import unittest
from pathlib import Path

from src.operator_syntax_triggers_seq001_v001 import learn_operator_syntax_triggers, match_operator_syntax_triggers


class OperatorSyntaxTriggerTests(unittest.TestCase):
    def test_static_syntax_wakes_low_touch_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "rare_probe_seq001_v001.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                '"""Compiles manifest syntax triggers for low touch file sims."""\n'
                "def assemble_operator_syntax_probe():\n"
                "    return 'syntax trigger'\n",
                encoding="utf-8",
            )

            rows = match_operator_syntax_triggers(root, "operator syntax trigger for low touch manifest file", limit=3)

            self.assertEqual(rows[0]["file"], "src/rare_probe_seq001_v001.py")
            self.assertIn("file_static_syntax", rows[0]["sources"])

    def test_learning_operator_language_promotes_observed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "blank_leaf_seq001_v001.py"
            target.parent.mkdir(parents=True)
            target.write_text("def quiet_leaf():\n    return None\n", encoding="utf-8")
            graph = {
                "graph_id": "intent-graph:test",
                "prompt": "semantic numeric encoding should wake sleepy leaf",
                "intents": [{
                    "segment": "semantic numeric encoding",
                    "intent_key": "src:route:semantic_numeric_encoding:minor",
                    "files": ["src/blank_leaf_seq001_v001.py"],
                }],
            }

            learn_operator_syntax_triggers(root, graph, write=True)
            rows = match_operator_syntax_triggers(root, "wake semantic numeric sleepy leaf", limit=3)

            self.assertEqual(rows[0]["file"], "src/blank_leaf_seq001_v001.py")
            self.assertIn("learned_operator_syntax", rows[0]["sources"])

    def test_low_touch_files_keep_exploration_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observed = root / "src" / "observed_seq001_v001.py"
            sleepy = root / "src" / "sleepy_syntax_seq001_v001.py"
            observed.parent.mkdir(parents=True)
            observed.write_text("def semantic_numeric_encoding():\n    return True\n", encoding="utf-8")
            sleepy.write_text("def semantic_numeric_sleepy_trigger():\n    return True\n", encoding="utf-8")
            graph = {"graph_id": "g", "prompt": "semantic numeric encoding", "intents": [{
                "segment": "semantic numeric encoding",
                "intent_key": "src:route:semantic_numeric_encoding:minor",
                "files": ["src/observed_seq001_v001.py"],
            }]}

            learn_operator_syntax_triggers(root, graph, write=True)
            rows = match_operator_syntax_triggers(root, "semantic numeric sleepy trigger", limit=2)

            self.assertTrue(any(row["file"] == "src/sleepy_syntax_seq001_v001.py" for row in rows))


if __name__ == "__main__":
    unittest.main()
