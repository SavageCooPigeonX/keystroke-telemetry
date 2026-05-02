import json
import tempfile
from pathlib import Path

import codex_compat
from src.file_self_knowledge_seq001_v001 import (
    PACKET_SCHEMA,
    build_file_self_knowledge,
    load_file_self_knowledge,
)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="file_self_knowledge_"))
    (root / ".github").mkdir(parents=True)
    (root / "logs" / "file_memory").mkdir(parents=True)
    (root / "src" / "intent").mkdir(parents=True)
    (root / ".github" / "copilot-instructions.md").write_text("# Instructions\n", encoding="utf-8")
    (root / "MANIFEST.md").write_text("# Root\nfile self knowledge owns mutation guides\n", encoding="utf-8")
    (root / "src" / "intent" / "MANIFEST.md").write_text(
        "# Intent\nrouter owns intent compilation and mutation warrants\nvalidator owns proof\n",
        encoding="utf-8",
    )
    (root / "src" / "intent" / "validator.py").write_text(
        "def validate(packet):\n    return bool(packet.get('intent_key'))\n",
        encoding="utf-8",
    )
    (root / "src" / "intent" / "router.py").write_text(
        "from src.intent.validator import validate\n\n"
        "def route_intent(prompt):\n"
        "    packet = {'intent_key': prompt, 'scope': 'src/intent'}\n"
        "    return packet if validate(packet) else {}\n",
        encoding="utf-8",
    )
    (root / "test_router.py").write_text(
        "from src.intent.router import route_intent\n\n"
        "def test_route_intent():\n"
        "    assert route_intent('compile')['scope'] == 'src/intent'\n",
        encoding="utf-8",
    )
    memory_path = root / "logs" / "file_memory" / "src__intent__router.py.json"
    memory_path.write_text(json.dumps({
        "messages": [
            {
                "commands": {
                    "remember": ["router owns intent warrants before coding models draft"],
                    "use": ["src/intent/validator.py before rewrite"],
                    "avoid": ["generic rewrite without proof"],
                },
                "body_preview": "router wants validator loaded before mutation",
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "file_memory_index.json").write_text(json.dumps({
        "files": [
            {
                "file": "src/intent/router.py",
                "messages": 1,
                "path": "logs/file_memory/src__intent__router.py.json",
                "markdown": "logs/file_memory/src__intent__router.py.md",
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "file_job_council_latest.json").write_text(json.dumps({
        "jobs": [
            {
                "captain": "src/intent/router.py",
                "files": ["src/intent/router.py", "src/intent/validator.py"],
                "context_files": ["src/intent/MANIFEST.md", "test_router.py"],
                "why": "router and validator co-own intent proof",
            }
        ],
        "relationships": [
            {
                "from": "src/intent/router.py",
                "to": "src/intent/validator.py",
                "type": "friendship",
                "reason": "validator proves router packets",
            }
        ],
    }), encoding="utf-8")
    (root / "logs" / "file_identity_growth.jsonl").write_text(
        json.dumps({
            "file": "src/intent/router.py",
            "intent_key": "src/intent:build:mutation_warrant:patch",
            "growth_tags": ["intent", "compile", "warrant", "operator", "probe"],
        }) + "\n",
        encoding="utf-8",
    )
    (root / "logs" / "dead_token_collective_pairs.jsonl").write_text(
        json.dumps({
            "event_type": "rename",
            "old_path": "src/intent/router_v001_chore_cascade.py",
            "new_path": "src/intent/router.py",
            "old_identity": "router_v001_chore_cascade",
            "new_identity": "router",
            "dead_tokens": ["v001", "chore", "cascade"],
            "intent_key": "src/intent:rename:router:major",
        }) + "\n",
        encoding="utf-8",
    )
    return root


def test_file_self_knowledge_builds_repo_owned_packets():
    root = _repo()

    result = build_file_self_knowledge(
        root,
        files=["src/intent/router.py"],
        prompt="codex probes operator intent and writes mutation warrants",
        write=True,
    )

    assert result["schema"] == "file_self_knowledge/v1"
    assert result["packet_count"] == 1
    packet = result["packets"][0]
    assert packet["schema"] == PACKET_SCHEMA
    assert packet["file"] == "src/intent/router.py"
    assert "intent compilation and mutation routing" in packet["owns"]
    assert "src/intent/validator.py" in packet["required_context"]
    assert "src/intent/MANIFEST.md" in packet["required_context"]
    assert "test_router.py" in packet["required_context"]
    assert any("py_compile src/intent/router.py" in command for command in packet["validates_with"])
    assert any("pytest test_router.py" in command for command in packet["validates_with"])
    assert "chore" in packet["dead_token_negatives"]
    assert "coding_model_role" in packet["mutation_scope"]
    assert "warrant" in packet["model_guide"]
    assert (root / "logs" / "file_self_knowledge_latest.json").exists()
    assert (root / "logs" / "file_self_knowledge" / "src__intent__router.py.json").exists()
    assert "File Self-Knowledge" in (root / "logs" / "file_self_knowledge.md").read_text(encoding="utf-8")
    profiles = json.loads((root / "file_profiles.json").read_text(encoding="utf-8"))
    assert profiles["router"]["self_knowledge_packet"]["file"] == "src/intent/router.py"

    loaded = load_file_self_knowledge(root, "src/intent/router.py")
    assert loaded["packet_id"] == packet["packet_id"]


def test_dynamic_context_pack_includes_file_self_knowledge():
    root = _repo()

    pack = codex_compat.build_dynamic_context_pack(
        root,
        "codex probes operator intent and writes mutation warrants",
        context_selection={
            "files": [{"name": "src/intent/router.py", "path": "src/intent/router.py", "score": 0.92}],
            "confidence": 0.92,
            "status": "ok",
        },
        inject=False,
    )

    self_knowledge = pack["file_self_knowledge"]
    assert self_knowledge["packets"]
    assert self_knowledge["packets"][0]["file"] == "src/intent/router.py"
    rendered = (root / "logs" / "dynamic_context_pack.md").read_text(encoding="utf-8")
    assert "FILE_SELF_KNOWLEDGE" in rendered
    assert "src/intent/router.py" in rendered
