import json
import subprocess
import tempfile
from pathlib import Path

from src.dead_stale_code_audit_seq001_v001 import audit_dead_stale_code_paths


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-m", message)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="dead_stale_audit_"))
    _git(root, "init")
    _git(root, "config", "user.email", "audit@example.test")
    _git(root, "config", "user.name", "Audit Test")
    (root / "src").mkdir()
    (root / "client").mkdir()
    (root / "src" / "live_router_seq001_v001.py").write_text(
        "def route():\n    return True\n",
        encoding="utf-8",
    )
    (root / "src" / "old_surface_seq001_v001.py").write_text(
        "# INTENT: old surface\n\ndef old():\n    return False\n",
        encoding="utf-8",
    )
    (root / "client" / "app.py").write_text(
        "from src.live_router_seq001_v001 import route\n\nroute()\n",
        encoding="utf-8",
    )
    _commit(root, "feat: add live router and old surface")
    (root / "src" / "old_surface_seq001_v001.py").rename(root / "src" / "old_surface_seq002_v001.py")
    (root / "src" / "old_surface_seq002_v001.py").write_text(
        "# INTENT: newer surface\n\ndef old():\n    return True\n",
        encoding="utf-8",
    )
    _commit(root, "chore: rename old surface into newer identity")
    (root / "_tmp_probe.py").write_text("print('probe')\n", encoding="utf-8")
    _commit(root, "test: add temp probe")
    (root / "_tmp_probe.py").unlink()
    _commit(root, "cleanup: remove temp probe")
    return root


def test_dead_stale_code_audit_writes_live_and_dead_reconstruction():
    root = _repo()

    result = audit_dead_stale_code_paths(root, write=True)

    assert result["source_file_count"] >= 3
    assert result["dead_event_count"] >= 1
    assert result["deletion_groups"]["temp_or_stress_cleanup"]["count"] == 1
    assert any(item["path"].endswith("old_surface_seq002_v001.py") for item in result["top_findings"])
    latest = json.loads((root / "logs" / "dead_stale_code_audit_latest.json").read_text(encoding="utf-8"))
    assert latest["schema"] == "dead_stale_code_audit/v1"
    report = (root / "logs" / "dead_stale_code_audit_latest.md").read_text(encoding="utf-8")
    assert "What Got Killed" in report
    assert "Live Stale Suspects" in report
