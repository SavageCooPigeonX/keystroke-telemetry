import json

from src.hourly_autonomous_file_sim_seq001_v001 import run_hourly_autonomous_file_sim
from test_file_self_sim_learning import _repo


def test_hourly_file_sim_emits_one_deepseek_action_without_source_overwrite():
    root = _repo()
    big_path = root / "src" / "intent" / "big_router_seq009_v002.py"
    big_source = "\n".join(f"def route_part_{i}():\n    return {i}\n" for i in range(18))
    big_path.write_text(big_source, encoding="utf-8")
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
        "cross_file_validation": {
            "exists": True,
            "dirty": False,
            "imports": [],
            "referenced_by": ["test_big_router.py"],
        },
        "ten_q": {"passed": True, "score": 9},
    })

    result = run_hourly_autonomous_file_sim(
        root,
        "hourly organization compliance split overcap validation",
        limit=5,
        write=True,
        source_result=latest,
        sim_config={"soft_line_cap": 20, "warn_line_cap": 30, "hard_line_cap": 40},
    )

    assert result["schema"] == "hourly_autonomous_file_sim/v1"
    assert result["mode"] == "one_intent_aligned_action_per_hour"
    assert result["selected_action"]["action_type"] == "deepseek_split_plan_context"
    assert result["selected_action"]["target_file"] == "src/intent/big_router_seq009_v002.py"
    assert result["selected_action"]["deepseek_mode"] == "split_plan_only_no_source_write"
    assert result["validation"]["source_mutation"] == "none"
    assert result["deepseek_context_pack"]["schema"] == "hourly_deepseek_context_pack/v1"
    assert "operator approval" in " ".join(result["deepseek_context_pack"]["must_not_do"])
    assert big_path.read_text(encoding="utf-8") == big_source
    assert (root / "logs" / "hourly_autonomous_file_sim_latest.json").exists()
    assert (root / "logs" / "hourly_deepseek_context_pack.json").exists()
    rendered = (root / "logs" / "hourly_autonomous_file_sim.md").read_text(encoding="utf-8")
    assert "Hourly Autonomous File Sim" in rendered
    assert "File Quote" in rendered
    assert "Next Hour Seed" in rendered
