"""Test regression rollback on syntax error."""
import sys, shutil
sys.path.insert(0, '.')
from pathlib import Path
import importlib.util

f = sorted(Path('src').glob('file_overwriter*.py'))[-1]
spec = importlib.util.spec_from_file_location('fo', f)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

tmp = Path('logs/_test_broken_syntax.py')
bak = Path('logs/_test_good_backup.py.bak')

tmp.write_text('def broken(\n    print("syntax error")\n', 'utf-8')
bak.write_text('# good backup\n', 'utf-8')

reg = m._run_regression('_test_broken_syntax', tmp, bak, Path('.'))
print('passed:', reg['passed'])
print('failed:', reg['failed'])
print('error:', reg['error'][:120])
restored = tmp.read_text('utf-8')
print('restored correctly:', restored == '# good backup\n')

tmp.unlink(missing_ok=True)
bak.unlink(missing_ok=True)
