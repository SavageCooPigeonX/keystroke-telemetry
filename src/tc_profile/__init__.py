"""tc_profile/ -- auto-fixed pigeon package."""
from .p_tc_p_s032_v001 import update_profile_from_composition
from .p_tc_p_s040_v001 import detect_session_template
from .p_tcpucd_s031_v001 import update_profile_from_completion
from .p_tpbd_s033_v001 import bootstrap_profile
from .p_tpbf_s036_v001 import bootstrap_profile
from .p_tpfid_s025_v001 import format_intelligence_for_prompt
from .p_tpfpd_s037_v001 import format_profile_for_prompt
from .p_tpgj_s043_v001 import generate_profile_from_journal
from .p_tpgs_s041_v001 import generate_profile_from_session
from .p_tpgsd_s042_v001 import generate_profile_from_session
from .p_tpie_s039_v001 import extract_session_triggers, extract_session_files
from .p_tpig_s038_v001 import extract_session_triggers, extract_session_files, detect_session_template
from .p_tpls_s030_v001 import load_profile, save_profile
from .p_tpsc_s006_v001 import classify_section
from .p_tpusd_s007_v001 import update_section
