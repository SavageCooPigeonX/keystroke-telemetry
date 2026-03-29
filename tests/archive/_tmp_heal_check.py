from glob import glob
import importlib, os
_hits = glob('pigeon_compiler/rename_engine/heal_seq009_v*.py')
if not _hits:
    raise ImportError('heal_seq009* not found')
_mod = importlib.import_module('pigeon_compiler.rename_engine.' + os.path.splitext(os.path.basename(_hits[0]))[0])
scan_issues = _mod.scan_issues

issues = scan_issues(".")
print(f"Issues found: {len(issues)}")
for i in issues[:20]:
    sev = i.get("severity", "?")
    itype = i.get("issue_type", "?")
    fname = i.get("file", "?")[:60]
    print(f"  [{sev}] {itype} in {fname}")
