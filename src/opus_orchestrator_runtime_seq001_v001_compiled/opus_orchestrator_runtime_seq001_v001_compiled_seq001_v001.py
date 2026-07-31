"""opus_orchestrator_runtime_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_orchestrator_runtime_seq001_v001_compiled_seq002_v001 import render_opus_runtime
from .opus_orchestrator_runtime_seq001_v001_compiled_seq003_v001 import _artifact_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq003_v001 import _prompt_box_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq003_v001 import _training_debug_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq004_v001 import _coding_memory_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq004_v001 import _folder_context_coupling_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq004_v001 import _macro_cycle_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq004_v001 import _manifest_write_cycle_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq005_v001 import _agent_from_packet
from .opus_orchestrator_runtime_seq001_v001_compiled_seq005_v001 import _hush_summary
from .opus_orchestrator_runtime_seq001_v001_compiled_seq005_v001 import _manifest_write
from .opus_orchestrator_runtime_seq001_v001_compiled_seq005_v001 import _work_completed
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import HISTORY
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import LATEST
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import MANIFEST_NOTE
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import MARKDOWN
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import SCHEMA
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _append_jsonl
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _json
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _jsonl_tail
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _now
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _prompt_row
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import _write_json
from pathlib import Path
from src.hush_intent_runtime_seq001_v001 import build_hush_intent_runtime
from src.opus_artifact_memory_seq001_v001 import build_opus_artifact_memory
from src.opus_coding_area_memory_seq001_v001 import build_opus_coding_area_memory
from src.opus_prompt_box_seq001_v001 import refine_opus_prompt_box
from src.opus_training_pair_debug_seq001_v001 import debug_training_pairs
from src.session_macro_cycle_seq001_v001 import build_session_macro_cycle
from typing import Any
import json

def build_opus_orchestrator_runtime(root: Path, prompt: str = "", *, write: bool = True) -> dict[str, Any]:
    """Assemble the chat surface Claude Opus should see before orchestration."""
    root = Path(root)
    journal = _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 3)
    context = _json(root / "logs" / "dynamic_context_pack.json")
    fsk = _json(root / "logs" / "file_self_knowledge_latest.json")
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    delegates = _json(root / "logs" / "file_deepseek_delegate_latest.json")
    current_prompt = prompt or (journal[-1].get("msg", "") if journal else "")
    artifact = build_opus_artifact_memory(root, current_prompt, write=write)
    coding_memory = build_opus_coding_area_memory(root, current_prompt, write=write)
    training_debug = debug_training_pairs(root, write=write)
    hush = build_hush_intent_runtime(root, current_prompt, write=write)
    macro_cycle = build_session_macro_cycle(root, prompt_limit=5, window_minutes=20, write=write)
    prompt_box = refine_opus_prompt_box(root, current_prompt, write=write)
    packets = fsk.get("packets") or []
    jobs = delegates.get("jobs") or []
    fence = ((hush.get("repo_classification") or {}).get("mutation_fence")) or "blocked"
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "chat_surface": "thought_completer",
        "operator_prompt": current_prompt,
        "last_three_prompts": [_prompt_row(row) for row in journal],
        "roles": {
            "runtime_authority": "hush",
            "orchestrator": "claude-opus",
            "context_selector": "gemini",
            "file_reasoner": "gemini",
            "file_hands": "deepseek",
            "apply_grader": "claude-opus",
        },
        "gemini_context": {
            "confidence": (context.get("context_selection") or {}).get("confidence"),
            "files": (context.get("context_selection") or {}).get("files") or [],
            "intent_key": ((context.get("prompt_brain") or {}).get("intent") or {}).get("intent_key", ""),
        },
        "hush_intent_runtime": _hush_summary(hush),
        "orchestration_gate": {
            "mutation_fence": fence,
            "source_mutation_allowed": fence == "open",
            "rule": "Hush owns repo-room selection; blocked fences mean plans/artifacts only.",
        },
        "file_subagents": [_agent_from_packet(packet, jobs, fence) for packet in packets[:8]],
        "hush_file_packets": (hush.get("file_packets") or [])[:8],
        "artifact_memory": _artifact_summary(artifact),
        "coding_area_memory": _coding_memory_summary(coding_memory),
        "training_pair_debug": _training_debug_summary(training_debug),
        "session_macro_cycle": _macro_cycle_summary(macro_cycle),
        "opus_prompt_box": _prompt_box_summary(prompt_box),
        "manifest_state_write_cycle": _manifest_write_cycle_summary(root),
        "folder_context_coupling": _folder_context_coupling_summary(root),
        "work_completed": _work_completed(delegates, sim),
        "manifest_write": _manifest_write(current_prompt, packets, jobs),
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN, "manifest_note": MANIFEST_NOTE},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_opus_runtime(result), encoding="utf-8")
        (root / MANIFEST_NOTE).write_text(result["manifest_write"]["markdown"], encoding="utf-8")
    return result
