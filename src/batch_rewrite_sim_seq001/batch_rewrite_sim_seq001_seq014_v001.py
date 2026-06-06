"""batch_rewrite_sim_seq001_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def _fallback_prompt_sim_targets(root: Path) -> list[tuple[str, float, str]]:
    candidates = [
        "codex_compat.py",
        "src/batch_rewrite_sim_seq001_v001.py",
        "src/file_self_sim_learning_seq001_v001.py",
        "src/file_email_plugin_seq001_v001.py",
        "src/intent_loop_closer_seq001_v001.py",
    ]
    return [
        (rel, 0.7, "prompt_contract_fallback_core_file")
        for rel in candidates
        if (root / rel).exists()
    ]
