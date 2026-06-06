"""batch_rewrite_sim_seq001_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _job_council_summary(
    jobs: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    roster: list[dict[str, Any]],
) -> str:
    failures = sum(int(member.get("failed_checks") or 0) for member in roster)
    beefs = sum(1 for edge in relationships if edge.get("type") == "beef")
    friends = sum(1 for edge in relationships if edge.get("type") == "friendship")
    tokens = sum(int(member.get("approx_tokens") or 0) for member in roster)
    job_word = "job" if len(jobs) == 1 else "jobs"
    if failures:
        return (
            f"{len(jobs)} {job_word} formed around {tokens} estimated tokens. "
            f"{friends} friendships tried to help, {beefs} beefs filed paperwork, "
            f"and {failures} failed checks are yelling at the broken model stack."
        )
    return (
        f"{len(jobs)} {job_word} formed around {tokens} estimated tokens. "
        f"{friends} friendships loaded context, {beefs} beefs stayed documented, "
        "and the files are suspiciously ready for approval."
    )
