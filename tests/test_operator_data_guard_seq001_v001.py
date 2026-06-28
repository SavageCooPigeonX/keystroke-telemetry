from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / (
    "operator_data_guard_seq001_v001__block_operator_data_git_storage_lc_"
    "data_storage_operator_happens.py"
)
INSTALLER = ROOT / "scripts" / (
    "install_operator_data_guard_hook_seq001_v001__install_pre_push_operator_data_guard_lc_"
    "data_storage_operator_happens.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class OperatorDataGuardTests(unittest.TestCase):
    def test_classifies_operator_data_but_allows_code_and_contract_docs(self):
        guard = _load(GUARD, "operator_data_guard")

        self.assertTrue(guard.classify_operator_data_path("query_memory.json"))
        self.assertTrue(guard.classify_operator_data_path("logs/prompt_journal.jsonl"))
        self.assertTrue(guard.classify_operator_data_path(".maif/operator_profile.json"))
        self.assertFalse(guard.classify_operator_data_path("src/query_memory_seq010.py"))
        self.assertFalse(guard.classify_operator_data_path("docs/operator_data_storage_contract.md"))

    def test_blocks_staged_operator_data_in_git_repo(self):
        guard = _load(GUARD, "operator_data_guard_git")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / ".gitignore").write_text("\n".join(guard.REQUIRED_GITIGNORE_PATTERNS) + "\n", encoding="utf-8")
            (root / "README.md").write_text("# ok\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=root, check=True)
            (root / "query_memory.json").write_text("[]\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", "query_memory.json"], cwd=root, check=True)

            report = guard.audit_operator_data_storage(root, include_untracked=False)

            self.assertFalse(report["ok"])
            self.assertIn("query_memory.json", report["findings"][0]["path"])

    def test_installer_writes_pre_push_hook(self):
        installer = _load(INSTALLER, "operator_data_guard_installer")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks = root / ".git" / "hooks"
            hooks.mkdir(parents=True)

            hook = installer.install_hook(root)

            self.assertEqual(hook.name, "pre-push")
            text = hook.read_text(encoding="utf-8")
            self.assertIn("operator_data_guard", text)
            self.assertIn("--pre-push", text)


if __name__ == "__main__":
    unittest.main()
