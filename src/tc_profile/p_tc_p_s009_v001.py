"""Compatibility facade for p_tc_p_s009_v001_compiled."""

try:
    from .p_tc_p_s009_v001_compiled import (
        __deduce_intelligence_comfort_avoidance,
        __deduce_intelligence_decision_speed,
        __deduce_intelligence_deletion_personality,
        __deduce_intelligence_frustration_response,
        __deduce_intelligence_time_personality,
        __deduce_intelligence_work_style,
    )
except ImportError:
    from p_tc_p_s009_v001_compiled import (
        __deduce_intelligence_comfort_avoidance,
        __deduce_intelligence_decision_speed,
        __deduce_intelligence_deletion_personality,
        __deduce_intelligence_frustration_response,
        __deduce_intelligence_time_personality,
        __deduce_intelligence_work_style,
    )

__all__ = [
    "__deduce_intelligence_comfort_avoidance",
    "__deduce_intelligence_decision_speed",
    "__deduce_intelligence_deletion_personality",
    "__deduce_intelligence_frustration_response",
    "__deduce_intelligence_time_personality",
    "__deduce_intelligence_work_style",
]
