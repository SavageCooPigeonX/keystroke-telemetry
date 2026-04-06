"""Stress test: import every module, verify exports, check for silent failures.

test_all.py covers 5 modules (8.2% coverage). This smoke-tests ALL src/ modules:
1. Can it be imported without error?
2. Do its declared exports exist?
3. Over-cap files flagged.

Run: py deep_stress_test.py
"""
import ast
import importlib
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))


def discover_modules():
    src = ROOT / 'src'
    modules = []
    for f in sorted(src.rglob('*.py')):
        if '__pycache__' in str(f):
            continue
        # Skip dot-prefixed directories (un-importable by Python)
        rel = f.relative_to(ROOT)
        parts = list(rel.with_suffix('').parts)
        if any(p.startswith('.') for p in parts):
            continue
        mod_path = '.'.join(parts)
        modules.append((mod_path, f))
    return modules


def get_exports(path):
    try:
        tree = ast.parse(path.read_text('utf-8'))
    except SyntaxError:
        return [], [], True
    funcs = [n.name for n in ast.iter_child_nodes(tree) 
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith('_')]
    classes = [n.name for n in ast.iter_child_nodes(tree) 
               if isinstance(n, ast.ClassDef) and not n.name.startswith('_')]
    return funcs, classes, False


def test_import(mod_path):
    try:
        mod = importlib.import_module(mod_path)
        return True, mod
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    modules = discover_modules()
    passed = 0
    import_failed = 0
    export_missing = 0
    syntax_errors = 0
    results = []
    t0 = time.time()

    for mod_path, file_path in modules:
        funcs, classes, has_syntax_err = get_exports(file_path)
        if has_syntax_err:
            syntax_errors += 1
            results.append(('SYNTAX', mod_path, 'SyntaxError'))
            continue
        ok, mod_or_err = test_import(mod_path)
        if not ok:
            import_failed += 1
            results.append(('IMPORT', mod_path, str(mod_or_err)[:100]))
            continue
        missing = [n for n in funcs + classes if not hasattr(mod_or_err, n)]
        if missing:
            export_missing += 1
            results.append(('EXPORT', mod_path, f"missing: {', '.join(missing[:5])}"))
        else:
            passed += 1
            results.append(('OK', mod_path, f"{len(funcs)}F {len(classes)}C"))

    elapsed = time.time() - t0
    total = len(modules)
    
    print(f"\n{'='*60}")
    print(f"  DEEP STRESS TEST: IMPORT + EXPORT VERIFICATION")
    print(f"{'='*60}")
    print(f"  Modules: {total} | Passed: {passed} ({passed*100//total}%) | Failed: {import_failed}")
    print(f"  Export issues: {export_missing} | Syntax: {syntax_errors} | Time: {elapsed:.1f}s")
    print()

    failures = [r for r in results if r[0] != 'OK']
    if failures:
        print(f"  FAILURES ({len(failures)}):")
        for kind, mod, detail in sorted(failures)[:30]:
            short = mod.split('.')[-1][:45]
            print(f"    [{kind:6s}] {short}")
            print(f"             {detail[:90]}")

    over_cap = [(len(fp.read_text('utf-8').splitlines()), mp)
                for mp, fp in modules
                if len(fp.read_text('utf-8').splitlines()) > 200]
    if over_cap:
        over_cap.sort(reverse=True)
        print(f"\n  OVER 200-LINE CAP ({len(over_cap)}):")
        for lines, mod in over_cap[:10]:
            print(f"    {lines:5d}  {mod.split('.')[-1][:55]}")

    health = passed / total if total else 0
    print(f"\n  HEALTH: {health:.0%} {'✓' if health >= 0.8 else '⚠'}")
    return 0 if import_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
