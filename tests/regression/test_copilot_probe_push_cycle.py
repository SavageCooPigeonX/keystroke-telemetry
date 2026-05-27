import json

from codex_compat import enqueue_deepseek_prompt_job
from src.copilot_probe_push_cycle_seq001_v001 import (
    build_copilot_probe_push_cycle,
    render_deepseek_compiler_prompt,
)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_probe_push_cycle_builds_compiler_packet(tmp_path):
    _write(
        tmp_path / "MANIFEST.md",
        "# Probe repo\n\nOwns intent graph, DeepSeek compiler, and Copilot orchestration.\n",
    )
    _write(
        tmp_path / "src" / "probe_orchestrator_seq001_v001.py",
        '"""Probe orchestrator wakes files and hands compiler jobs to DeepSeek."""\n'
        "from .compiler_gate_seq001_v001 import validate\n",
    )
    _write(
        tmp_path / "src" / "compiler_gate_seq001_v001.py",
        '"""Compiler gate validates bounded mutations."""\n',
    )

    packet = build_copilot_probe_push_cycle(
        tmp_path,
        "copilot becomes sim orchestration and deepseek compiler runs each prompt",
        deleted_words=["scope"],
        context_selection={
            "status": "ok",
            "confidence": 0.8,
            "files": [{"name": "src/probe_orchestrator_seq001_v001.py", "score": 0.8}],
        },
        source="unit",
        write=True,
    )

    assert packet["schema"] == "copilot_probe_push_cycle/v1"
    assert packet["cycle_id"].startswith("probe-")
    assert packet["intent_moves"]
    assert packet["file_sim_orchestration"]["waking_files"]
    assert "Copilot/Codex is the operator probe" in packet["deepseek_compiler_handoff"]["compiler_prompt"]
    assert (tmp_path / "logs" / "copilot_probe_push_cycle_latest.json").exists()
    assert (tmp_path / "logs" / "copilot_probe_push_cycle.md").exists()


def test_deepseek_job_uses_probe_context_path_and_waking_files(tmp_path):
    packet = {
        "cycle_id": "probe-test",
        "file_sim_orchestration": {
            "waking_files": [{"name": "src/probe_orchestrator_seq001_v001.py", "score": 0.9}],
        },
        "deepseek_compiler_handoff": {
            "context_pack_path": "logs/copilot_probe_push_cycle_latest.json",
        },
    }
    job = enqueue_deepseek_prompt_job(
        tmp_path,
        "PUSH CYCLE CONTRACT:\nDeepSeek compiler handoff",
        context_selection={"status": "ok", "confidence": 0.7},
        context_pack={"prompt": "raw operator prompt", "copilot_probe_push_cycle": packet},
        deleted_words=["scope"],
        source="unit:probe_push_cycle",
        mode="probe_push_cycle",
    )

    assert job is not None
    assert job["mode"] == "probe_push_cycle"
    assert job["context_pack_path"] == "logs/copilot_probe_push_cycle_latest.json"
    assert job["dynamic_context_pack_path"] == "logs/dynamic_context_pack.json"
    assert job["probe_cycle_id"] == "probe-test"
    assert job["focus_files"][0]["name"] == "src/probe_orchestrator_seq001_v001.py"
    rows = [
        json.loads(line)
        for line in (tmp_path / "logs" / "deepseek_prompt_jobs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows[-1]["source"] == "unit:probe_push_cycle"


def test_rendered_compiler_prompt_contains_closure_contract():
    packet = {
        "operator_prompt": "run the compiler push cycle",
        "deleted_words": [],
        "operator_probe": {"read": "Copilot probes; DeepSeek compiles."},
        "intent_moves": [{"intent_key": "root:build:push_cycle:patch", "files": ["src/x.py"], "why": "unit"}],
        "file_sim_orchestration": {
            "waking_files": [{"name": "src/x.py", "score": 0.5, "sources": ["unit"]}],
            "focus_packets": [{"id": "x", "role_hint": "owns the push cycle", "top_edges": []}],
        },
        "deepseek_compiler_handoff": {"context_pack_path": "logs/copilot_probe_push_cycle_latest.json"},
    }

    text = render_deepseek_compiler_prompt(packet)

    assert "REQUIRED OUTPUT" in text
    assert "validation gates" in text
    assert "backward into file memory" in text

