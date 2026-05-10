"""codex_compat_main_seq075_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_audit_stale_dates_seq053_v001 import audit_stale_dates
from .codex_compat_build_dynamic_context_pack_seq042_v001 import build_dynamic_context_pack
from .codex_compat_build_parser_seq074_v001 import build_parser
from .codex_compat_capture_pair_seq069_v001 import capture_pair
from .codex_compat_close_intent_loop_seq049_v001 import close_intent_loop
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from .codex_compat_get_intent_loop_status_seq050_v001 import get_intent_loop_status
from .codex_compat_import_jsonl_seq073_v001 import import_jsonl
from .codex_compat_launch_deepseek_daemon_seq037_v001 import launch_deepseek_daemon
from .codex_compat_log_composition_seq063_v001 import log_composition
from .codex_compat_log_edit_seq068_v001 import log_edit
from .codex_compat_log_prompt_seq062_v001 import log_prompt
from .codex_compat_log_response_seq066_v001 import log_response
from .codex_compat_predict_numeric_files_seq017_v001 import predict_numeric_files
from .codex_compat_push_intent_resolver_seq071_v001 import push_intent_resolver
from .codex_compat_record_entropy_shed_seq070_v001 import record_entropy_shed
from .codex_compat_refresh_state_seq057_v001 import refresh_state
from .codex_compat_run_pre_prompt_pipeline_seq055_v001 import run_pre_prompt_pipeline
from .codex_compat_select_context_seq056_v001 import select_context
from .codex_compat_train_numeric_surface_seq016_v001 import train_numeric_surface
from pathlib import Path
from typing import Any
import json
import os
import re
import subprocess
import sys

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "log-prompt":
        result: Any = log_prompt(
            root,
            args.prompt,
            deleted_words=args.deleted_word,
            deleted_text=args.deleted_text,
            deletion_ratio=args.deletion_ratio,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
        )
    elif args.command == "log-composition":
        result = log_composition(
            root,
            args.final_text,
            deleted_text=args.deleted_text,
            deleted_words=args.deleted_word,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
        )
    elif args.command == "pre-prompt":
        result = run_pre_prompt_pipeline(
            root,
            args.final_text,
            deleted_text=args.deleted_text,
            deleted_words=args.deleted_word,
            hesitation_count=args.hesitation_count,
            duration_ms=args.duration_ms,
            run_sim=not args.no_sim,
            sim_timeout_s=args.sim_timeout_s,
            inject=not args.no_inject,
        )
    elif args.command == "select-context":
        result = select_context(root, args.prompt, args.deleted_word)
    elif args.command == "context-pack":
        result = build_dynamic_context_pack(
            root,
            prompt=args.prompt,
            deleted_words=args.deleted_word,
            surface=args.surface,
            inject=not args.no_inject,
        )
    elif args.command == "file-self-knowledge":
        _ensure_repo_on_path(root)
        from src.file_self_knowledge_seq001_v001 import build_file_self_knowledge
        result = build_file_self_knowledge(
            root,
            files=args.file,
            prompt=args.prompt,
            limit=args.limit,
            write=not args.no_write,
        )
    elif args.command == "train-numeric":
        result = train_numeric_surface(root, args.prompt, args.file)
    elif args.command == "predict-numeric":
        result = predict_numeric_files(root, args.prompt, args.top_n)
    elif args.command == "log-response":
        result = log_response(
            root,
            args.prompt,
            args.response,
            style_arm=args.style_arm,
            hook_ids=args.hook_id,
            intent_nodes=args.intent_node,
            context_window_files=args.context_window_file,
            feedback_text=args.feedback,
        )
    elif args.command == "log-edit":
        result = log_edit(root, file=args.file, why=args.why, prompt=args.prompt)
    elif args.command == "capture-pair":
        result = capture_pair(root)
    elif args.command == "state":
        result = refresh_state(root, "manual refresh")
    elif args.command == "shed":
        result = record_entropy_shed(root, args.module, args.confidence, args.note)
    elif args.command == "launch-observatory":
        if args.thought_completer:
            target = root / "src" / "thought_completer.py"
            cmd = ["py", str(target), "--observatory", "--no-gemini"]
        else:
            matches = sorted((root / "src").glob("*tc_observatory*.py"))
            target = matches[-1] if matches else root / "src" / "tc_observatory_seq001_v001.py"
            cmd = ["py", str(target)]
        proc = subprocess.Popen(cmd, cwd=root)
        result = {"status": "started", "pid": proc.pid, "target": str(target)}
    elif args.command == "launch-deepseek":
        result = launch_deepseek_daemon(root, dry_run=args.dry_run)
    elif args.command == "push-intent-resolver":
        result = push_intent_resolver(root, args.prompt_limit)
    elif args.command == "intent-loop-status":
        result = get_intent_loop_status(root)
    elif args.command == "close-intent-loop":
        result = close_intent_loop(root, loop_id=args.loop_id, status=args.status, note=args.note)
    elif args.command == "stale-date-audit":
        result = audit_stale_dates(root, max_lag_minutes=args.max_lag_minutes)
    elif args.command == "import-jsonl":
        result = import_jsonl(root, Path(args.source), capture=not args.no_capture)
    else:
        raise AssertionError(args.command)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((output + "\n").encode("utf-8", errors="replace"))
    return 0
