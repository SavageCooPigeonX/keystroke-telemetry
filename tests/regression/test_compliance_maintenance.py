from pathlib import Path

from pigeon_compiler.pigeon_limits import explain_exclusion
from scripts.maintain_compliance import apply_compiler, emit_repair_jobs, scan


def test_exclusion_decision_explains_protected_paths(tmp_path):
    app = tmp_path / "app.py"
    app.write_text("print('entrypoint')\n", encoding="utf-8")
    client = tmp_path / "client" / "os_hook.py"
    client.parent.mkdir()
    client.write_text("print('client entrypoint')\n", encoding="utf-8")
    source = tmp_path / "src" / "module.py"
    source.parent.mkdir()
    source.write_text("def ok():\n    return True\n", encoding="utf-8")

    assert explain_exclusion(app, tmp_path)["reason"] == "protected_name"
    assert explain_exclusion(client, tmp_path)["reason"] == "protected_dir:client"
    assert explain_exclusion(source, tmp_path)["excluded"] is False


def test_compliance_scan_uses_real_tree_not_registry(tmp_path):
    source = tmp_path / "src" / "giant.py"
    source.parent.mkdir()
    source.write_text("\n".join(f"x_{idx} = {idx}" for idx in range(230)) + "\n", encoding="utf-8")
    ignored = tmp_path / "client" / "giant_client.py"
    ignored.parent.mkdir()
    ignored.write_text("\n".join(f"x_{idx} = {idx}" for idx in range(230)) + "\n", encoding="utf-8")

    report = scan(tmp_path)

    assert report["violation_count"] == 1
    assert report["violations"][0]["path"] == "src/giant.py"
    assert report["violations"][0]["risk"] == "low"
    assert report["excluded_count"] == 1


def test_compliance_scan_marks_root_entrypoint_high_risk(tmp_path):
    root_entry = tmp_path / "runner.py"
    root_entry.write_text(
        "\n".join(["import argparse", "def main():", "    return 0", 'if __name__ == "__main__":', "    main()"] + [f"x_{i} = {i}" for i in range(230)])
        + "\n",
        encoding="utf-8",
    )

    report = scan(tmp_path)

    assert report["violation_count"] == 1
    violation = report["violations"][0]
    assert violation["risk"] == "high"
    assert "root_level_module" in violation["reasons"]
    assert "runtime_entrypoint_marker" in violation["reasons"]


def test_apply_compiler_defaults_to_low_risk_only(monkeypatch, tmp_path):
    low = tmp_path / "src" / "leaf.py"
    low.parent.mkdir()
    low.write_text("\n".join(f"x_{idx} = {idx}" for idx in range(230)) + "\n", encoding="utf-8")
    high = tmp_path / "runner.py"
    high.write_text(
        "\n".join(["import argparse", "def main():", "    return 0", 'if __name__ == "__main__":', "    main()"] + [f"x_{i} = {i}" for i in range(230)])
        + "\n",
        encoding="utf-8",
    )

    class Runner:
        def run(self, source, target_name=None):
            target = source.parent / target_name
            target.mkdir()
            (target / "part.py").write_text("x = 1\n", encoding="utf-8")
            return {"files": 1, "violations": 0}

    monkeypatch.setattr("scripts.maintain_compliance._load_runner", lambda root: Runner())
    report = scan(tmp_path)
    applied = apply_compiler(tmp_path, report["violations"], max_files=0)

    assert [item["file"] for item in applied] == ["src/leaf.py"]


def test_emit_repair_jobs_records_operator_intent_and_deepseek_v4(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_CODING_MODEL", "deepseek-v4-pro")
    report = {
        "violation_count": 2,
        "risk_counts": {"low": 1, "medium": 1, "high": 0},
        "violations": [
            {
                "path": "src/leaf.py",
                "lines": 230,
                "risk": "low",
                "reasons": ["leaf_over_cap"],
                "strategy": "compile_package_first",
            },
            {
                "path": "src/shared.py",
                "lines": 500,
                "risk": "medium",
                "reasons": ["fan_in:1"],
                "strategy": "compile_package_then_import_facade_test",
            },
        ],
    }

    emitted = emit_repair_jobs(
        tmp_path,
        report,
        max_files=1,
        max_risk="low",
        autonomous_write=True,
    )

    assert len(emitted) == 1
    assert emitted[0]["queued"] is True
    assert emitted[0]["model"] == "deepseek-v4-pro"
    assert emitted[0]["autonomous_write"] is True
    assert emitted[0]["focus_files"][0] == "src/leaf.py"
    assert "autonomous pigeon compliance repair" in emitted[0]["prompt"]

    jobs = (tmp_path / "logs" / "deepseek_prompt_jobs.jsonl").read_text(encoding="utf-8")
    receipt = (tmp_path / "logs" / "pigeon_compliance_autonomy_latest.json").read_text(encoding="utf-8")
    assert "compliance-" in jobs
    assert "autonomous_pigeon_compliance_repair" in receipt
