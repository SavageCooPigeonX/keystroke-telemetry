"""Compatibility facade for p_tpes_s003_v001_compiled."""

try:
    from .p_tpes_s003_v001_compiled import _empty_profile, _empty_section
except ImportError:
    from p_tpes_s003_v001_compiled import _empty_profile, _empty_section

__all__ = ["_empty_profile", "_empty_section"]
