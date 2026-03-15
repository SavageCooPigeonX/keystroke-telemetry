"""Focused release-readiness checks for public source distribution."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def main():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"src*"' in pyproject, "pyproject.toml must package the src telemetry modules"

    env_example = REPO_ROOT / ".env.example"
    assert env_example.exists(), ".env.example must exist for public deployment"
    assert "DEEPSEEK_API_KEY" in env_example.read_text(encoding="utf-8")

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    compiler_readme = (REPO_ROOT / "pigeon_compiler" / "README.md").read_text(encoding="utf-8")

    assert "MIT License" in readme or "MIT license" in readme, "README must document the public license"
    assert "MIT License" in compiler_readme or "MIT license" in compiler_readme, \
        "pigeon_compiler/README.md must document the public license"
    assert "pip install ." in readme, "README must document source installation for release validation"
    assert ".env.example" in readme, "README must document the example environment file"

    print("PUBLIC RELEASE CHECKS PASSED ✓")


if __name__ == "__main__":
    main()
