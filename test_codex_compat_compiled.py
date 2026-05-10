import ast
import importlib
import importlib.util
import json
import pkgutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "codex_compat"


def test_compiled_codex_compat_imports_all_modules():
    import codex_compat

    failures = []
    for module_info in pkgutil.iter_modules(codex_compat.__path__):
        if module_info.ispkg:
            continue
        name = f"codex_compat.{module_info.name}"
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - assertion reports all failures
            failures.append((name, type(exc).__name__, str(exc)))

    assert failures == []


def test_compiled_codex_compat_has_no_internal_circular_imports():
    edges = {}
    for path in PACKAGE.glob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        deps = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.level == 1
                and node.module
                and node.module.startswith("codex_compat_")
            ):
                deps.append(node.module)
        edges[path.stem] = deps

    cycles = []
    seen = set()

    def visit(node, stack):
        if node in stack:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in seen:
            return
        seen.add(node)
        for dep in edges.get(node, []):
            visit(dep, stack + [node])

    for node in edges:
        visit(node, [])

    assert cycles == []


def test_compiled_codex_compat_parent_package_parity():
    import codex_compat

    expected = {
        "build_dynamic_context_pack",
        "run_pre_prompt_pipeline",
        "log_prompt",
        "log_response",
        "log_edit",
        "select_context",
        "main",
    }

    assert expected <= set(dir(codex_compat))


def test_compiled_codex_compat_has_real_sibling_imports_not_runtime_bridge():
    generated = list(PACKAGE.glob("codex_compat_*_seq*_v001.py"))

    assert generated
    assert not (PACKAGE / "_runtime.py").exists()
    assert any(
        "from .codex_compat_parse_deleted_words_seq003_v001 import _parse_deleted_words"
        in path.read_text(encoding="utf-8")
        for path in generated
    )
    assert all("_runtime" not in path.read_text(encoding="utf-8") for path in generated)


def test_compiler_writer_resolves_internal_imports():
    writer_path = next((ROOT / "pigeon_compiler" / "cut_executor").glob("*fw_s003*.py"))
    spec = importlib.util.spec_from_file_location("pigeon_file_writer_under_test", writer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    plan = {
        "cuts": [
            {"new_file": "pkg_a_seq001_v001.py", "functions": ["a"]},
            {"new_file": "pkg_b_seq002_v001.py", "functions": ["b"]},
        ]
    }

    imports = module._resolve_imports("def a():\n    return b()\n", [], plan, plan["cuts"][0], module._symbol_module_map(plan))

    assert imports == ["from .pkg_b_seq002_v001 import b"]


def test_compiled_codex_compat_writes_compile_lineage_aliases():
    lineage_path = PACKAGE / "COMPILE_LINEAGE.json"
    alias_path = ROOT / "logs" / "file_identity_aliases.json"

    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    aliases = json.loads(alias_path.read_text(encoding="utf-8"))
    build_alias = aliases["aliases"]["codex_compat.py::build_dynamic_context_pack"]

    assert lineage["schema"] == "pigeon_compile_lineage/v1"
    assert lineage["source_file"] == "codex_compat.py"
    assert build_alias["current_file"] == "codex_compat/codex_compat_build_dynamic_context_pack_seq042_v001.py"
    assert any(
        entry["generated_file"] == build_alias["current_file"]
        for entry in lineage["files"]
    )


def test_file_sim_resolves_split_identity_aliases():
    from src.batch_rewrite_sim_seq001_v001 import _resolve_alias_targets

    targets = _resolve_alias_targets(ROOT, "codex_compat.py::build_dynamic_context_pack")

    assert targets == ["codex_compat/codex_compat_build_dynamic_context_pack_seq042_v001.py"]


def test_file_sim_context_selection_uses_split_identity_aliases():
    from src.batch_rewrite_sim_seq001_v001 import simulate_batch_rewrites

    result = simulate_batch_rewrites(
        ROOT,
        intent="verify codex compat compile identity",
        limit=1,
        write=False,
        context_selection={"files": [{"name": "codex_compat.py::build_dynamic_context_pack"}]},
    )

    assert result["proposals"][0]["path"] == "codex_compat/codex_compat_build_dynamic_context_pack_seq042_v001.py"
    assert "identity_alias:numeric_context_selection_alias" in result["proposals"][0]["evidence"]
