"""Test the import_rewriter patch — verify all import patterns are handled."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pigeon_compiler.rename_engine.import_rewriter_seq003_v004_d0316__rewrite_all_imports_across_the_lc_import_rewriter_now import (
    _rewrite_line, _build_stem_map
)

# Simulate a rename: pipeline_seq015_v005_d0314__old_desc_lc_old_intent
#                  → pipeline_seq015_v006_d0316__new_desc_lc_new_intent
IMPORT_MAP = {
    'production_auditor.pipeline_seq015_v005_d0314__old_desc_lc_old_intent':
        'production_auditor.pipeline_seq015_v006_d0316__new_desc_lc_new_intent',
    'api.audit_routes_seq002_v003_d0314__old_audit_routes_lc_old':
        'api.audit_routes_seq002_v004_d0316__new_audit_routes_lc_new',
}
STEM_MAP = _build_stem_map(IMPORT_MAP)

passed = 0
failed = 0

def check(name, line, expected):
    global passed, failed
    result = _rewrite_line(line, IMPORT_MAP, STEM_MAP)
    if result == expected:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}")
        print(f"    input:    {line}")
        print(f"    expected: {expected}")
        print(f"    got:      {result}")

print("=== Test import_rewriter patterns ===\n")

# 1. Direct dotted import (already worked)
check("dotted_from_import",
    "from production_auditor.pipeline_seq015_v005_d0314__old_desc_lc_old_intent import run_full_audit",
    "from production_auditor.pipeline_seq015_v006_d0316__new_desc_lc_new_intent import run_full_audit")

# 2. Bare import (already worked)
check("bare_import",
    "import production_auditor.pipeline_seq015_v005_d0314__old_desc_lc_old_intent",
    "import production_auditor.pipeline_seq015_v006_d0316__new_desc_lc_new_intent")

# 3. *** THE BUG *** - from package import module (was broken, now fixed)
check("package_import_module",
    "from production_auditor import pipeline_seq015_v005_d0314__old_desc_lc_old_intent",
    "from production_auditor import pipeline_seq015_v006_d0316__new_desc_lc_new_intent")

# 4. Relative import
check("relative_import",
    "from .pipeline_seq015_v005_d0314__old_desc_lc_old_intent import run_full_audit",
    "from .pipeline_seq015_v006_d0316__new_desc_lc_new_intent import run_full_audit")

# 5. Dotted subpackage import via stem
check("subpackage_stem",
    "from some_other.pipeline_seq015_v005_d0314__old_desc_lc_old_intent import X",
    "from some_other.pipeline_seq015_v006_d0316__new_desc_lc_new_intent import X")

# 6. import package.module (bare dotted)
check("bare_dotted_import_stem",
    "import other_pkg.pipeline_seq015_v005_d0314__old_desc_lc_old_intent",
    "import other_pkg.pipeline_seq015_v006_d0316__new_desc_lc_new_intent")

# 7. Multi-import from package
check("multi_import_from_package",
    "from production_auditor import something_else, pipeline_seq015_v005_d0314__old_desc_lc_old_intent",
    "from production_auditor import something_else, pipeline_seq015_v006_d0316__new_desc_lc_new_intent")

# 8. __init__.py style import
check("init_style_import",
    "from api.audit_routes_seq002_v003_d0314__old_audit_routes_lc_old import audit_bp",
    "from api.audit_routes_seq002_v004_d0316__new_audit_routes_lc_new import audit_bp")

# 9. External package — should NOT be touched
check("external_flask",
    "from flask import Blueprint",
    "from flask import Blueprint")

check("external_os",
    "import os",
    "import os")

# 10. Non-import line — should NOT be touched
check("non_import",
    "x = pipeline_seq015_v005_d0314__old_desc_lc_old_intent",
    "x = pipeline_seq015_v005_d0314__old_desc_lc_old_intent")

# 11. Indented import
check("indented_import",
    "    from production_auditor.pipeline_seq015_v005_d0314__old_desc_lc_old_intent import run_full_audit",
    "    from production_auditor.pipeline_seq015_v006_d0316__new_desc_lc_new_intent import run_full_audit")

# 12. from package import module as alias
check("import_as_alias",
    "from production_auditor import pipeline_seq015_v005_d0314__old_desc_lc_old_intent as pipeline",
    "from production_auditor import pipeline_seq015_v006_d0316__new_desc_lc_new_intent as pipeline")

print(f"\n{'='*40}")
print(f"Results: {passed} passed / {passed + failed} total")
if failed:
    print(f"FAILURES: {failed}")
    sys.exit(1)
else:
    print("ALL PASS")
