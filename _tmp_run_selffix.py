"""Run self-fix cycle and write report."""
import json, importlib.util, sys
from pathlib import Path

# Import directly from monolith (shard __init__.py is incomplete)
spec = importlib.util.spec_from_file_location(
    "self_fix_mono",
    Path("src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc.py")
)
sf = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sf
spec.loader.exec_module(sf)
run_self_fix = sf.run_self_fix
write_self_fix_report = sf.write_self_fix_report

root = Path('.')
reg = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
report = run_self_fix(root, reg)
probs = report['problems']
print(f"Scanned {report['total_files_scanned']} modules, {report['import_graph_size']} in import graph")
by_sev = {}
by_type = {}
for p in probs:
    s = p.get('severity', '?')
    t = p.get('type', '?')
    by_sev[s] = by_sev.get(s, 0) + 1
    by_type[t] = by_type.get(t, 0) + 1
print(f"Total problems: {len(probs)}")
print("By severity:", dict(sorted(by_sev.items())))
print("By type:", dict(sorted(by_type.items())))

# Show critical ones
crits = [p for p in probs if p.get('severity') == 'critical']
print(f"\nCritical problems ({len(crits)}):")
for p in crits[:20]:
    f = p.get('file', '?')
    t = p.get('type', '?')
    fix = p.get('fix', '?')
    print(f"  [{t}] {f}: {fix[:80]}")

# Show over-cap
overcap = [p for p in probs if p.get('type') == 'over_hard_cap']
print(f"\nOver-cap ({len(overcap)}):")
for p in overcap[:10]:
    print(f"  {p.get('file', '?')}: {p.get('count', '?')} lines")

# Write report
out = write_self_fix_report(root, report)
print(f"\nReport written: {out}")
