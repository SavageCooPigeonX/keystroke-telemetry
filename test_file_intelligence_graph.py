import json

from src.file_intelligence_graph_seq001_v001 import (
    build_file_intelligence_graph,
    expand_files_with_graph,
    render_graph_context_for_files,
)


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_file_intelligence_graph_builds_typed_edges_from_code_and_logs(tmp_path):
    _write(
        tmp_path / "src" / "alpha_seq001_v001.py",
        '"""Alpha owns graph intent routing."""\nfrom .beta_seq001_v001 import run_beta\n',
    )
    _write(tmp_path / "src" / "beta_seq001_v001.py", '"""Beta supports alpha."""\n')
    _write(
        tmp_path / "test_alpha.py",
        "from src.alpha_seq001_v001 import run_beta\n",
    )
    _write(
        tmp_path / "logs" / "intent_touches.jsonl",
        json.dumps({"prompt_preview": "graph intent routing", "files": ["alpha", "beta"]}) + "\n",
    )
    _write(
        tmp_path / "logs" / "sim_mailbox.jsonl",
        json.dumps({"from": ["alpha"], "to": "beta", "action_path": "beta should align with alpha"}) + "\n",
    )

    graph = build_file_intelligence_graph(
        tmp_path,
        prompt="build graph intent routing for alpha",
        focus_files=["alpha"],
        write=True,
    )
    edge_types = {(edge["src"], edge["dst"], edge["type"]) for edge in graph["edges"]}

    assert ("alpha", "beta", "imports") in edge_types
    assert ("alpha", "beta", "co_touched_with") in edge_types
    assert ("alpha", "beta", "sim_requested") in edge_types
    assert any(edge[0] == "alpha" and edge[2] == "tested_by" for edge in edge_types)
    assert (tmp_path / "logs" / "file_intelligence_graph_latest.json").exists()


def test_expand_files_with_graph_adds_neighbors_and_prompt_matches(tmp_path):
    _write(
        tmp_path / "src" / "alpha_seq001_v001.py",
        '"""Alpha graph owner."""\nfrom .beta_seq001_v001 import run_beta\n',
    )
    _write(tmp_path / "src" / "beta_seq001_v001.py", '"""Beta graph helper."""\n')
    _write(tmp_path / "src" / "graph_helper_seq001_v001.py", '"""Graph helper file."""\n')

    rows = expand_files_with_graph(
        tmp_path,
        [{"name": "alpha", "score": 0.6}],
        prompt="graph helper for alpha",
        limit=4,
    )
    names = [row["name"] for row in rows]

    assert "alpha" in names
    assert "beta" in names
    assert "graph_helper" in names


def test_render_graph_context_is_model_readable(tmp_path):
    _write(
        tmp_path / "src" / "alpha_seq001_v001.py",
        '"""Alpha graph owner."""\nfrom .beta_seq001_v001 import run_beta\n',
    )
    _write(tmp_path / "src" / "beta_seq001_v001.py", '"""Beta graph helper."""\n')

    text = render_graph_context_for_files(
        tmp_path,
        [{"name": "alpha"}],
        prompt="alpha graph edge context",
    )

    assert "FILE INTELLIGENCE GRAPH" in text
    assert "FILE alpha" in text
    assert "edge imports beta" in text
