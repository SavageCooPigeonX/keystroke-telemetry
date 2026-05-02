import json

from src.file_self_sim_learning_seq001_v001 import simulate_file_self_learning
from test_file_self_sim_learning import _repo


def test_file_sim_queues_one_perpendicular_deepseek_job_without_source_write():
    root = _repo()
    big_path = root / "src" / "intent" / "big_router_seq009_v002.py"
    source = "\n".join(f"def route_part_{i}():\n    return {i}\n" for i in range(18))
    big_path.write_text(source, encoding="utf-8")
    (root / "test_big_router.py").write_text(
        "from src.intent.big_router_seq009_v002 import route_part_0\n\n"
        "def test_route_part_0():\n"
        "    assert route_part_0() == 0\n",
        encoding="utf-8",
    )
    latest = json.loads((root / "logs" / "batch_rewrite_sim_latest.json").read_text(encoding="utf-8"))
    latest["proposals"].append({
        "path": "src/intent/big_router_seq009_v002.py",
        "confidence": 0.84,
        "interlink_score": 0.76,
        "approval_gate": "operator_required",
        "context_injection": [
            "src/intent/big_router_seq009_v002.py",
            "src/intent/validator.py",
            "src/intent/MANIFEST.md",
            "test_big_router.py",
        ],
        "validation_plan": [
            "py -m py_compile src/intent/big_router_seq009_v002.py",
            "py -m pytest test_big_router.py -q",
        ],
        "cross_file_validation": {"exists": True, "dirty": False, "imports": [], "referenced_by": ["test_big_router.py"]},
        "ten_q": {"passed": True, "score": 9},
    })

    result = simulate_file_self_learning(
        root,
        "per sim deepseek split compression alternate state",
        limit=5,
        write=True,
        source_result=latest,
        config={"soft_line_cap": 20, "warn_line_cap": 30, "hard_line_cap": 40},
    )

    lane = result["perpendicular_deepseek"]
    assert lane["queued"] is True
    assert lane["job"]["source"] == "file_sim_perpendicular_lane/v1"
    assert lane["job"]["mode"] == "file_sim_split_plan"
    assert lane["job"]["autonomous_write"] is False
    assert lane["job"]["write_artifact"] is True
    assert "alternate-state simulation" in lane["job"]["prompt"]
    assert (root / "logs" / "deepseek_prompt_jobs.jsonl").exists()
    assert (root / "logs" / "file_sim_deepseek_context_pack.json").exists()
    assert big_path.read_text(encoding="utf-8") == source
