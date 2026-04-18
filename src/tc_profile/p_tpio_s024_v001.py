"""tc_profile_seq001_v001_intelligence_orchestrator_seq024_v001.py — Auto-extracted by Pigeon Compiler.

COGNITIVE NOTE (auto-added by reactor): This module triggered 3+ high-load flushes (avg_hes=1.039, state=focused). Consider simplifying its public interface or adding examples."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | 37 lines | ~482 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
import ast
import re
import time

from .p_tcpic_s010_v001 import __deduce_intelligence_comfort_avoidance
from .p_tc_p_s012_v001 import __deduce_intelligence_deletion_personality
from .p_tpidt_s011_v001 import __deduce_intelligence_time_personality
from .p_tpifs_s015_v001 import __deduce_intelligence_frustration_response
from .p_tc_p_s010_v001 import __deduce_intelligence_suppression_pattern
from .p_tc_p_s021_v001 import __deduce_intelligence_contradiction_detector
from .p_tpidw_s018_v001 import __deduce_intelligence_decision_speed
from .p_tpidw_s018_v001 import __deduce_intelligence_work_style
from .p_tpibl_s022_v001 import __deduce_intelligence_behavioral_laws
from .p_tpip_s023_v001 import __deduce_intelligence_persist

def _deduce_intelligence(profile: dict):
    """The scary part. Cross-reference ALL shards to discover secrets.

    Called after every update. Each deduction checks for a NEW pattern
    the system hasn't logged yet. Secrets accumulate forever.
    """
    from collections import Counter
    from datetime import datetime, timezone

    intel = profile['shards'].setdefault('intelligence', {
        'secrets': [], 'behavioral_laws': [], 'contradictions': [],
        'predictions_log': [], 'operator_model': {}, 'secret_count': 0,
        'last_deduction': None,
    })
    model = intel.setdefault('operator_model', {})
    sections = profile['shards'].get('sections', {})
    now = datetime.now(timezone.utc).isoformat()
    existing = {s.get('key') for s in intel.get('secrets', []) if isinstance(s, dict)}
    new_secrets = []

    new_secrets.extend(__deduce_intelligence_comfort_avoidance(sections, existing, now, model))
    new_secrets.extend(__deduce_intelligence_deletion_personality(profile, existing, now, model))
    new_secrets.extend(__deduce_intelligence_time_personality(sections, existing, now, model))
    new_secrets.extend(__deduce_intelligence_frustration_response(sections, existing, now, model))
    new_secrets.extend(__deduce_intelligence_suppression_pattern(sections, existing, now))
    __deduce_intelligence_contradiction_detector(profile, sections, existing, now, intel)
    new_secrets.extend(__deduce_intelligence_decision_speed(profile, existing, now, model))
    new_secrets.extend(__deduce_intelligence_work_style(sections, existing, now, model))
    __deduce_intelligence_behavioral_laws(sections, existing, intel)
    __deduce_intelligence_persist(new_secrets, sections, intel, model, now)
