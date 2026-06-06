"""file_self_sim_learning_seq001_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq024_v001 import _size_pressure
from .file_self_sim_learning_seq001_seq026_v001 import _neighbors_from_graph
from .file_self_sim_learning_seq001_seq026_v001 import _reason_not_to_split
from .file_self_sim_learning_seq001_seq027_v001 import _proposed_split_children
from .file_self_sim_learning_seq001_seq027_v001 import _split_file_quote
from .file_self_sim_learning_seq001_seq033_v001 import _default_validation
from .file_self_sim_learning_seq001_seq034_v001 import _nearest_manifest
from .file_self_sim_learning_seq001_seq034_v001 import _tests_for_file
from .file_self_sim_learning_seq001_seq036_v001 import _candidate_allowed
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import hashlib
import re

def _overcap_split_jobs(
    root: Path,
    wake_order: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    registry: dict[str, Any],
    graph: dict[str, Any],
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    packet_by_file = {packet.get("file"): packet for packet in packets}
    registry_by_file = {item.get("file"): item for item in registry.get("files", []) or []}
    ordered: list[str] = []
    for node in wake_order:
        rel = node.get("file")
        pressure = node.get("size_pressure") or {}
        if rel and pressure.get("needs_split_plan"):
            ordered.append(rel)
    critical = [
        item.get("file") for item in sorted(
            registry.get("files", []) or [],
            key=lambda row: (row.get("split_pressure", 0), row.get("line_count", 0)),
            reverse=True,
        )
        if item.get("split_pressure", 0) > 0
    ]
    ordered.extend(critical)

    jobs = []
    for rel in _dedupe(_clean_rel(item) for item in ordered):
        if not rel or not _candidate_allowed(root, rel):
            continue
        size = _size_pressure(root, rel, settings)
        if not size.get("needs_split_plan"):
            continue
        packet = packet_by_file.get(rel) or {}
        tests = ((packet.get("verification_packet") or {}).get("tests") or _tests_for_file(root, rel, {}))
        validation = ((packet.get("verification_packet") or {}).get("validation_plan") or _default_validation(root, rel, tests))
        neighbors = _neighbors_from_graph(graph, rel)
        reg = registry_by_file.get(rel) or {}
        status = "ready_for_split_plan" if tests or not rel.endswith(".py") else "blocked_missing_validation"
        jobs.append({
            "schema": "overcap_split_job/v1",
            "job_id": "split-" + hashlib.sha256(f"{rel}|{size.get('line_count')}".encode("utf-8")).hexdigest()[:12],
            "file": rel,
            "file_id": reg.get("file_id") or "F-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12],
            "arch_seq": reg.get("arch_seq", ""),
            "local_seq": reg.get("local_seq", ""),
            "status": status,
            "deepseek_mode": "split_plan_only_no_source_write",
            "approval_gate": "operator_required",
            "line_count": size.get("line_count", 0),
            "size_state": size.get("state"),
            "split_pressure": size.get("pressure"),
            "reason_to_split": "over cap and repeatedly expensive for context; extract responsibilities behind a stable facade",
            "reason_not_to_split": _reason_not_to_split(rel, tests, neighbors),
            "context_pack": _dedupe([rel, _nearest_manifest(root, rel), *tests[:4], *neighbors[:6]]),
            "proposed_children": _proposed_split_children(root, rel),
            "validation_plan": validation[:6],
            "file_quote": _split_file_quote(rel, size, tests),
        })
        if len(jobs) >= int(settings.get("split_plan_limit") or 8):
            break
    return jobs
