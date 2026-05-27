"""Push-time Pigeon compliance maintenance.

The policy is intentionally simple:
- excluded means external path/runtime safety or non-source/generated surface
- non-excluded Python files must stay at or below PIGEON_MAX
- optional --apply compiles over-cap files into split packages, then blocks so
  the generated repair can be reviewed and committed
"""
from __future__ import annotations

import argparse
import ast
import compileall
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pigeon_compiler.pigeon_limits import PIGEON_MAX, explain_exclusion

PROMPT_JOBS = Path("logs/deepseek_prompt_jobs.jsonl")


def _repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return Path(proc.stdout.strip())


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _load_runner(root: Path):
    matches = sorted((root / "pigeon_compiler" / "runners").glob("*rcs_s010*.py"))
    if not matches:
        raise RuntimeError("clean split runner not found")
    spec = importlib.util.spec_from_file_location("pigeon_clean_split_runtime", matches[-1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safe_target_name(path: Path) -> str:
    stem = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in path.stem)
    return f"{stem[:48]}_compiled"


def _module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def _imports_from(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _public_exports(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return 999
    count = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            count += 1
    return count


def _has_entrypoint(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = [
        'if __name__ == "__main__"',
        "if __name__ == '__main__'",
        "argparse.",
        "click.",
        "@app.route",
        "Flask(",
    ]
    return any(marker in text for marker in markers)


def _risk_level(root: Path, rel: str, lines: int, fan_in: int, exports: int, entrypoint: bool) -> dict[str, Any]:
    path = Path(rel)
    reasons = []
    if len(path.parts) == 1:
        reasons.append("root_level_module")
    if path.name == "__main__.py":
        reasons.append("__main___entrypoint")
    if str(rel).startswith(("pigeon_compiler/", "pigeon_brain/")):
        reasons.append("compiler_or_brain_infrastructure")
    if entrypoint:
        reasons.append("runtime_entrypoint_marker")
    if fan_in >= 3:
        reasons.append(f"fan_in:{fan_in}")
    elif fan_in:
        reasons.append(f"fan_in:{fan_in}")
    if exports >= 8:
        reasons.append(f"many_public_exports:{exports}")
    elif exports:
        reasons.append(f"public_exports:{exports}")
    if lines >= 1000:
        reasons.append("very_large_split")

    if (
        "root_level_module" in reasons
        or "__main___entrypoint" in reasons
        or "runtime_entrypoint_marker" in reasons
        or any(item.startswith("fan_in:") and int(item.split(":", 1)[1]) >= 3 for item in reasons)
        or any(item.startswith("many_public_exports:") for item in reasons)
        or "very_large_split" in reasons
    ):
        return {"risk": "high", "reasons": reasons, "strategy": "manual_facade_and_behavior_tests"}
    if fan_in or exports or str(rel).startswith(("pigeon_compiler/", "pigeon_brain/")):
        return {"risk": "medium", "reasons": reasons, "strategy": "compile_package_then_import_facade_test"}
    return {"risk": "low", "reasons": reasons or ["leaf_over_cap"], "strategy": "compile_package_first"}


def _risk_rank(risk: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(risk, 9)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _load_jsonl(path: Path, limit: int = 2000) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def _deepseek_model() -> str:
    return os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"


def _repair_job_id(row: dict[str, Any]) -> str:
    payload = f"{row.get('path')}|{row.get('lines')}|{row.get('risk')}|{PIGEON_MAX}"
    return "compliance-" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _repair_prompt(row: dict[str, Any]) -> str:
    reasons = ", ".join(row.get("reasons") or [])
    return "\n".join([
        "Operator intent: autonomous pigeon compliance repair.",
        "Use DeepSeek V4 as the compiler/reasoning model for this compliance action.",
        "",
        f"Target file: {row['path']}",
        f"Current lines: {row['lines']}",
        f"PIGEON_MAX lines: {PIGEON_MAX}",
        f"Risk tier: {row.get('risk', 'unknown')}",
        f"Risk reasons: {reasons or 'none'}",
        f"Suggested strategy: {row.get('strategy', 'preserve behavior and reduce surface')}",
        "",
        "Contract:",
        "1. Preserve public behavior and imports.",
        "2. Decompose by natural responsibility boundaries; keep a compatibility facade when needed.",
        "3. Prefer the smallest safe compliance improvement over a broad rewrite.",
        "4. Run or name the focused tests/import checks needed after the patch.",
        "5. If the file cannot be safely decomposed in one action, emit the blocker and the next exact repair step.",
    ])


def emit_repair_jobs(
    root: Path,
    report: dict[str, Any],
    *,
    max_files: int,
    max_risk: str,
    autonomous_write: bool,
) -> list[dict[str, Any]]:
    ceiling = _risk_rank(max_risk)
    candidates = [
        row for row in report.get("violations", [])
        if _risk_rank(row.get("risk", "high")) <= ceiling
    ]
    selected = candidates if max_files == 0 else candidates[:max_files]
    job_path = root / PROMPT_JOBS
    seen = {str(row.get("job_id") or "") for row in _load_jsonl(job_path)}
    emitted = []
    for row in selected:
        job_id = _repair_job_id(row)
        job = {
            "schema": "deepseek_prompt_job/v1",
            "ts": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "source": "pigeon_compliance_gate/v1",
            "status": "queued",
            "priority": 1 + _risk_rank(row.get("risk", "high")),
            "mode": "autonomous_compliance_repair",
            "model": _deepseek_model(),
            "prompt": _repair_prompt(row),
            "focus_files": [row["path"], "logs/pigeon_compliance_push_latest.json"],
            "context_pack_path": "logs/pigeon_compliance_push_latest.json",
            "context_confidence": 1.0,
            "autonomous_write": autonomous_write,
            "compliance": {
                "pigeon_max": PIGEON_MAX,
                "lines": row.get("lines"),
                "risk": row.get("risk"),
                "reasons": row.get("reasons", []),
                "strategy": row.get("strategy"),
            },
        }
        if job_id not in seen:
            _append_jsonl(job_path, job)
            seen.add(job_id)
            emitted.append({**job, "queued": True})
        else:
            emitted.append({**job, "queued": False, "reason": "already_queued"})
    receipt = {
        "schema": "pigeon_compliance_autonomy_intent/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "operator_intent": "autonomous_pigeon_compliance_repair",
        "model": _deepseek_model(),
        "autonomous_write": autonomous_write,
        "max_risk": max_risk,
        "max_files": max_files,
        "emitted_count": sum(1 for row in emitted if row.get("queued")),
        "selected_count": len(selected),
        "violation_count": report.get("violation_count", 0),
        "risk_counts": report.get("risk_counts", {}),
        "jobs": [
            {
                "job_id": row.get("job_id"),
                "target": (row.get("focus_files") or [""])[0],
                "queued": row.get("queued"),
                "model": row.get("model"),
                "autonomous_write": row.get("autonomous_write"),
            }
            for row in emitted
        ],
    }
    _write_json(root / "logs" / "pigeon_compliance_autonomy_latest.json", receipt)
    _append_jsonl(root / "logs" / "pigeon_compliance_autonomy.jsonl", receipt)
    return emitted


def _annotate_violations(root: Path, files: list[dict[str, Any]], violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    imports_by_file: dict[str, set[str]] = {}
    module_by_file: dict[str, str] = {}
    for row in files:
        path = root / row["path"]
        module_by_file[row["path"]] = _module_name(root, path)
        imports_by_file[row["path"]] = _imports_from(path)

    fan_in: dict[str, int] = {row["path"]: 0 for row in files}
    for source, imports in imports_by_file.items():
        for target_rel, module in module_by_file.items():
            if source == target_rel:
                continue
            if module in imports or any(item == module or item.startswith(module + ".") for item in imports):
                fan_in[target_rel] = fan_in.get(target_rel, 0) + 1

    annotated = []
    for row in violations:
        path = root / row["path"]
        exports = _public_exports(path)
        entrypoint = _has_entrypoint(path)
        risk = _risk_level(root, row["path"], row["lines"], fan_in.get(row["path"], 0), exports, entrypoint)
        annotated.append({
            **row,
            "fan_in": fan_in.get(row["path"], 0),
            "public_exports": exports,
            "entrypoint": entrypoint,
            **risk,
        })
    return sorted(annotated, key=lambda item: (_risk_rank(item["risk"]), -item["lines"], item["path"]))


def scan(root: Path) -> dict[str, Any]:
    files = []
    excluded = []
    violations = []
    warnings = []
    for path in sorted(root.rglob("*.py")):
        decision = explain_exclusion(path, root)
        rel = decision["path"]
        if decision["excluded"]:
            excluded.append({"path": rel, "reason": decision["reason"]})
            continue
        lines = _line_count(path)
        row = {"path": rel, "lines": lines}
        files.append(row)
        if lines > PIGEON_MAX:
            violations.append(row)
        elif lines > 50:
            warnings.append(row)
    violations = _annotate_violations(root, files, violations)
    risk_counts = {
        "low": sum(1 for row in violations if row["risk"] == "low"),
        "medium": sum(1 for row in violations if row["risk"] == "medium"),
        "high": sum(1 for row in violations if row["risk"] == "high"),
    }
    return {
        "schema": "pigeon_compliance_push/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "pigeon_max": PIGEON_MAX,
        "files_checked": len(files),
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:30],
        "warning_count": len(warnings),
        "violation_count": len(violations),
        "risk_counts": risk_counts,
        "safe_first": [row for row in violations if row["risk"] == "low"][:20],
        "violations": violations,
    }


def apply_compiler(
    root: Path,
    violations: list[dict[str, Any]],
    max_files: int,
    max_risk: str = "low",
) -> list[dict[str, Any]]:
    runner = _load_runner(root)
    ceiling = _risk_rank(max_risk)
    candidates = [row for row in violations if _risk_rank(row.get("risk", "high")) <= ceiling]
    selected = candidates if max_files == 0 else candidates[:max_files]
    results = []
    for row in selected:
        rel = row["path"]
        source = root / rel
        target_name = _safe_target_name(source)
        try:
            result = runner.run(source, target_name=target_name)
            target = source.parent / target_name
            imports_ok = bool(target.exists() and compileall.compile_dir(str(target), quiet=1))
            results.append({
                "file": rel,
                "status": "compiled" if result.get("violations", 0) == 0 and imports_ok else "compiled_with_risk",
                "target": str(target.relative_to(root)).replace("\\", "/") if target.exists() else target_name,
                "files": result.get("files", 0),
                "violations": result.get("violations", 0),
                "compileall": imports_ok,
                "risk": row.get("risk"),
                "risk_reasons": row.get("reasons", []),
            })
        except Exception as exc:
            results.append({"file": rel, "status": "error", "error": str(exc)})
    return results


def _write_report(root: Path, report: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(exist_ok=True)
    latest = logs / "pigeon_compliance_push_latest.json"
    latest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (logs / "pigeon_compliance_push.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _safe_print(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(str(text).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="scan the full tree; kept for hook readability")
    parser.add_argument("--apply", action="store_true", help="compile over-cap files into split packages")
    parser.add_argument("--max-files", type=int, default=int(os.environ.get("PIGEON_COMPLIANCE_MAX_FILES", "0")))
    parser.add_argument(
        "--max-risk",
        choices=["low", "medium", "high"],
        default=os.environ.get("PIGEON_COMPLIANCE_MAX_RISK", "low"),
        help="highest risk tier allowed for --apply; default low",
    )
    parser.add_argument("--emit-repair-jobs", action="store_true", help="queue DeepSeek V4 compliance repair jobs")
    parser.add_argument(
        "--repair-max-files",
        type=int,
        default=int(os.environ.get("PIGEON_COMPLIANCE_REPAIR_MAX_FILES", "2")),
        help="maximum compliance repair jobs to emit; 0 means all candidates",
    )
    parser.add_argument(
        "--repair-max-risk",
        choices=["low", "medium", "high"],
        default=os.environ.get("PIGEON_COMPLIANCE_REPAIR_MAX_RISK", os.environ.get("PIGEON_COMPLIANCE_MAX_RISK", "low")),
        help="highest risk tier allowed for emitted repair jobs",
    )
    parser.add_argument(
        "--autonomous-write",
        action="store_true",
        default=os.environ.get("PIGEON_COMPLIANCE_AUTONOMOUS_WRITES", "").lower() in {"1", "true", "yes", "on"},
        help="allow queued DeepSeek jobs to attempt source mutation through the daemon",
    )
    parser.add_argument("--json", action="store_true", help="print full JSON report")
    args = parser.parse_args()

    root = _repo_root()
    report = scan(root)
    if args.apply and report["violations"]:
        report["applied"] = apply_compiler(root, report["violations"], args.max_files, max_risk=args.max_risk)
        report["apply_policy"] = {
            "max_risk": args.max_risk,
            "max_files": args.max_files,
            "mode": "compile_packages_only_no_source_replacement",
        }
        report["action_required"] = (
            "review generated split packages, add compatibility facades/tests for medium/high risk files, "
            "replace source only after behavior validation"
        )
    if args.emit_repair_jobs and report["violations"]:
        report["repair_jobs"] = emit_repair_jobs(
            root,
            report,
            max_files=args.repair_max_files,
            max_risk=args.repair_max_risk,
            autonomous_write=args.autonomous_write,
        )
    _write_report(root, report)

    if args.json:
        _safe_print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _safe_print(
            f"Pigeon compliance: {report['violation_count']} over-cap / "
            f"{report['files_checked']} checked; {report['excluded_count']} excluded"
        )
        _safe_print(
            "Risk tiers: "
            f"low={report['risk_counts']['low']} "
            f"medium={report['risk_counts']['medium']} "
            f"high={report['risk_counts']['high']}"
        )
        for row in report["violations"][:20]:
            _safe_print(f"  {row['risk'].upper():<6} OVER {row['lines']:>5}  {row['path']}  [{', '.join(row['reasons'][:3])}]")
        if report.get("applied"):
            ok = sum(1 for item in report["applied"] if item.get("status") == "compiled")
            _safe_print(f"  compiled packages: {ok}/{len(report['applied'])}")
        if report.get("repair_jobs"):
            queued = sum(1 for item in report["repair_jobs"] if item.get("queued"))
            _safe_print(f"  DeepSeek repair jobs queued: {queued}/{len(report['repair_jobs'])}")
    return 2 if report["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
