import importlib.util
from pathlib import Path


def _load_overwriter():
    root = Path(__file__).resolve().parent
    path = root / "src" / "file_overwriter_seq001_v001_d0422__autonomous_file_patcher_lc_feat_file_cortex.py"
    spec = importlib.util.spec_from_file_location("file_overwriter_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_patch_override_requires_file_approval(tmp_path):
    mod = _load_overwriter()
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "sample.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    result = mod.overwrite_file(
        "sample",
        "change value",
        root=tmp_path,
        dry_run=False,
        target_path="src/sample.py",
        _patch_override="<<<SEARCH\nVALUE = 1\n===\nVALUE = 2\n>>>REPLACE",
    )

    assert result["applied"] is False
    assert "missing file approval" in result["error"]
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"


def test_approved_patch_override_writes_with_regression(tmp_path, monkeypatch):
    mod = _load_overwriter()
    monkeypatch.setattr(mod, "_run_post_patch_grader", lambda *args, **kwargs: {"verdict": "accept"})
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "sample.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    result = mod.overwrite_file(
        "sample",
        "change value",
        grade_result={"confidence": 1.0, "approved": True},
        root=tmp_path,
        dry_run=False,
        approved=True,
        target_path="src/sample.py",
        _patch_override="<<<SEARCH\nVALUE = 1\n===\nVALUE = 2\n>>>REPLACE",
    )

    assert result["applied"] is True
    assert result["dry_run"] is False
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"
    assert (tmp_path / "logs" / "file_overwrites.jsonl").exists()
