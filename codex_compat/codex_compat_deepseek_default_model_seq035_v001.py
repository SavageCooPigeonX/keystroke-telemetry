"""codex_compat_deepseek_default_model_seq035_v001.py — Auto-extracted by Pigeon Compiler."""
import os
import re

def _deepseek_default_model() -> str:
    return os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"
