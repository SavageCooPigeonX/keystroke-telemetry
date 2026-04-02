"""警p_sa_s030_v003_d0402_缩分话_λV_strip_alert_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _strip_alert_block(text: str) -> str:
    pat = re.compile(
        rf'^\s*{re.escape(ALERT_START)}\s*$\n.*?^\s*{re.escape(ALERT_END)}\s*$\n?',
        re.MULTILINE | re.DOTALL,
    )
    return pat.sub('', text)
