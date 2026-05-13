import ast
import importlib.util
import shutil
from pathlib import Path


def _repo_root() -> Path:
    root = Path(__file__).resolve().parent
    while root != root.parent and not (root / "pigeon_compiler").exists():
        root = root.parent
    return root


def _load_clean_split_runner():
    root = _repo_root()
    runner = sorted((root / "pigeon_compiler" / "runners").glob("*rcs_s010*.py"))[-1]
    spec = importlib.util.spec_from_file_location("run_clean_split_fallback_test", runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_split_falls_back_without_deepseek(monkeypatch, tmp_path):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    scratch = _repo_root() / "test_logs" / "compiler_fallback" / f"{tmp_path.parent.name}_{tmp_path.name}"
    scratch.mkdir(parents=True, exist_ok=True)
    source = scratch / "compiler_fallback_source.py"
    target = scratch / "compiler_fallback_compiled"
    try:
        source.write_text(
            "\n\n".join(
                f"def function_{idx}():\n"
                + "\n".join(f"    value_{line} = {line}" for line in range(8))
                + "\n    return value_7\n"
                for idx in range(35)
            )
            + "\n",
            encoding="utf-8",
        )
        runner = _load_clean_split_runner()

        result = runner.run(source, target_name="compiler_fallback_compiled")

        assert result["violations"] == 0
        assert target.exists()
        compiled = [path for path in target.glob("*.py") if path.name != "__init__.py"]
        assert compiled
        for path in compiled:
            ast.parse(path.read_text(encoding="utf-8"))
        assert all(
            len(path.read_text(encoding="utf-8").splitlines()) <= 200
            for path in compiled
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
