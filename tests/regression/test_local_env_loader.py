import os
from pathlib import Path

from src.local_env_loader_seq001_v001 import has_env_key, load_local_env


def test_local_env_loader_reads_real_env_not_examples(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    root = Path(tmp_path)
    (root / ".env").write_text("DEEPSEEK_API_KEY=fake-test-key\n", encoding="utf-8")
    (root / ".env.example").write_text("DEEPSEEK_API_KEY=example-only\n", encoding="utf-8")

    loaded = load_local_env(root, keys={"DEEPSEEK_API_KEY"})

    assert os.environ["DEEPSEEK_API_KEY"] == "fake-test-key"
    assert loaded["DEEPSEEK_API_KEY"] == str(root / ".env")
    assert has_env_key(root, "DEEPSEEK_API_KEY") is True

