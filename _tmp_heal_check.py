from pigeon_compiler.rename_engine.heal_seq009_v004_d0315__self_healing_orchestrator_lc_verify_pigeon_plugin import scan_issues

issues = scan_issues(".")
print(f"Issues found: {len(issues)}")
for i in issues[:20]:
    sev = i.get("severity", "?")
    itype = i.get("issue_type", "?")
    fname = i.get("file", "?")[:60]
    print(f"  [{sev}] {itype} in {fname}")
