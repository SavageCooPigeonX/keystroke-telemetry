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
PIGEON_INSTALLER = ROOT / "scripts" / "install_pigeon_hooks.py"
CHANGED_GATE = ROOT / "scripts" / "pigeon_changed_file_gate_seq001_v001__block_new_overcap_lc_push_compliance.py"


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
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "install_pigeon_hooks.py").write_text(
                "from pathlib import Path\n"
                "Path('.git/hooks/pre-push').write_text('operator_data_guard --pre-push\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )

            hook = installer.install_hook(root)

            self.assertEqual(hook.name, "pre-push")
            text = hook.read_text(encoding="utf-8")
            self.assertIn("operator_data_guard", text)
            self.assertIn("--pre-push", text)

    def test_combined_pigeon_pre_push_runs_operator_guard_before_compliance(self):
        installer = _load(PIGEON_INSTALLER, "install_pigeon_hooks")

        pre_push = installer.PRE_PUSH
        guard_index = pre_push.index("operator_data_guard_seq001_v001")
        compliance_index = pre_push.index('if [ "${PIGEON_COMPLIANCE_APPLY:-0}" = "1" ]')

        self.assertLess(guard_index, compliance_index)
        self.assertIn("PIGEON_REFRESH_PUSH_MANIFESTS", pre_push)
        self.assertIn("refresh_push_manifests.py\" --dry-run", pre_push)
        self.assertIn("pigeon_changed_file_gate_seq001_v001", pre_push)
        self.assertIn("PIGEON_FULL_COMPLIANCE_BLOCK", pre_push)
        self.assertIn('export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"', installer.POST_COMMIT)
        self.assertIn('export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"', installer.PRE_COMMIT)
        self.assertIn('export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"', installer.PRE_PUSH)
        self.assertIn('elif command -v py >/dev/null 2>&1; then', installer.POST_COMMIT)
        self.assertIn('elif command -v py >/dev/null 2>&1; then', installer.PRE_COMMIT)

    def test_changed_file_gate_allows_improved_existing_overcap_and_blocks_worse(self):
        gate = _load(CHANGED_GATE, "pigeon_changed_file_gate")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            src = root / "src"
            src.mkdir()
            target = src / "over_seq001_v001.py"
            target.write_text("\n".join("x = 1" for _ in range(gate.PIGEON_MAX + 5)), encoding="utf-8")
            subprocess.run(["git", "add", "src/over_seq001_v001.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "seed"], cwd=root, check=True, stdout=subprocess.PIPE)

            target.write_text("\n".join("x = 1" for _ in range(gate.PIGEON_MAX + 2)), encoding="utf-8")
            subprocess.run(["git", "commit", "-am", "improve"], cwd=root, check=True, stdout=subprocess.PIPE)
            self.assertTrue(gate.audit_changed_file_compliance(root)["ok"])

            target.write_text("\n".join("x = 1" for _ in range(gate.PIGEON_MAX + 8)), encoding="utf-8")
            subprocess.run(["git", "commit", "-am", "worse"], cwd=root, check=True, stdout=subprocess.PIPE)
            report = gate.audit_changed_file_compliance(root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["violations"][0]["status"], "worsened_overcap")


if __name__ == "__main__":
    unittest.main()
