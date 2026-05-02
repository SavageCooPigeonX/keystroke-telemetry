import compileall
import importlib.util
import shutil
from pathlib import Path


def _load_clean_split_runner():
    root = Path(__file__).resolve().parent
    runner = sorted((root / "pigeon_compiler" / "runners").glob("*rcs_s010*.py"))[-1]
    spec = importlib.util.spec_from_file_location("run_clean_split_fallback_test", runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_clean_split_falls_back_without_deepseek(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    root = Path(__file__).resolve().parent
    source = root / "_tmp_compiler_fallback_source.py"
    target = root / "_tmp_compiler_fallback_compiled"
    if target.exists():
        shutil.rmtree(target)
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

        result = runner.run(source, target_name="_tmp_compiler_fallback_compiled")

        assert result["violations"] == 0
        assert target.exists()
        assert compileall.compile_dir(str(target), quiet=1)
        assert all(
            len(path.read_text(encoding="utf-8").splitlines()) <= 200
            for path in target.glob("*.py")
            if path.name != "__init__.py"
        )
    finally:
        if source.exists():
            source.unlink()
        if target.exists():
            shutil.rmtree(target)
