"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_stage_compliance_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from pigeon_compiler.rename_engine.正f_cmp_s008_v004_d0315_踪稿析_λν import audit_compliance

def _run_heal_pipeline_compliance(root: Path, report: dict):
    """Stage 3: Compliance audit."""
    print(f'[5/5] Running compliance audit...')
    compliance = audit_compliance(root)
    report['stages']['compliance'] = {
        'total': compliance['total'],
        'compliant': compliance['compliant'],
        'pct': compliance['compliance_pct'],
        'oversize': len(compliance['oversize']),
        'critical': [e['path'] for e in compliance['oversize']
                     if e['status'] == 'CRITICAL'],
    }
    print(f'      Compliance: {compliance["compliant"]}/{compliance["total"]} '
          f'({compliance["compliance_pct"]}%)')
