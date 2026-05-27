"""p_tc_p_s009_v001_compiled_functions_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def __deduce_intelligence_work_style(sections, existing, now, model):
    new_secrets = []
    key = 'work_style'
    if key not in existing and len(sections) >= 2:
        visits_per_section = [sec.get('visit_count', 0) for sec in sections.values() if isinstance(sec, dict)]
        if visits_per_section:
            max_v = max(visits_per_section)
            spread = len([v for v in visits_per_section if v > max_v * 0.3])
            total_v = sum(visits_per_section)
            if max_v / max(total_v, 1) > 0.7:
                ws = 'deep diver'
                desc = f'{max_v/total_v:.0%} of visits in one section. you tunnel in and stay.'
            elif spread >= 4:
                ws = 'butterfly'
                desc = f'{spread} sections with significant activity. you context-switch constantly.'
            else:
                ws = 'circuit runner'
                desc = f'you rotate through {spread} sections in cycles. predictable orbit.'
            new_secrets.append({
                'key': key, 'type': 'personality', 'discovered': now,
                'confidence': min(0.8, 0.4 + total_v * 0.01),
                'text': desc, 'evidence': f'{total_v} total visits across {len(visits_per_section)} sections',
            })
            model['work_style'] = ws
    return new_secrets
