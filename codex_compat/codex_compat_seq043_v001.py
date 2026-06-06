"""codex_compat_seq043_v001.py — Auto-extracted by Pigeon Compiler."""
import argparse
import json
import os
import re

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bridge explicit Codex events into telemetry training logs.")
    parser.add_argument("--root", default=".", help="Repo root to write logs into.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prompt = sub.add_parser("log-prompt")
    p_prompt.add_argument("--prompt", required=True)
    p_prompt.add_argument("--deleted-text", default="")
    p_prompt.add_argument("--deleted-word", action="append", default=[])
    p_prompt.add_argument("--deletion-ratio", type=float)
    p_prompt.add_argument("--hesitation-count", type=int, default=0)
    p_prompt.add_argument("--duration-ms", type=int, default=0)

    p_comp = sub.add_parser("log-composition")
    p_comp.add_argument("--final-text", required=True)
    p_comp.add_argument("--deleted-text", default="")
    p_comp.add_argument("--deleted-word", action="append", default=[])
    p_comp.add_argument("--hesitation-count", type=int, default=0)
    p_comp.add_argument("--duration-ms", type=int, default=0)

    p_pre = sub.add_parser("pre-prompt")
    p_pre.add_argument("--final-text", required=True)
    p_pre.add_argument("--deleted-text", default="")
    p_pre.add_argument("--deleted-word", action="append", default=[])
    p_pre.add_argument("--hesitation-count", type=int, default=0)
    p_pre.add_argument("--duration-ms", type=int, default=0)
    p_pre.add_argument("--no-sim", action="store_true")
    p_pre.add_argument("--sim-timeout-s", type=int, default=45)
    p_pre.add_argument("--no-inject", action="store_true")

    p_select = sub.add_parser("select-context")
    p_select.add_argument("--prompt", required=True)
    p_select.add_argument("--deleted-word", action="append", default=[])

    p_pack = sub.add_parser("context-pack")
    p_pack.add_argument("--prompt", default="")
    p_pack.add_argument("--deleted-word", action="append", default=[])
    p_pack.add_argument("--surface", default="codex")
    p_pack.add_argument("--no-inject", action="store_true")

    p_self = sub.add_parser("file-self-knowledge")
    p_self.add_argument("--prompt", default="")
    p_self.add_argument("--file", action="append", default=[])
    p_self.add_argument("--limit", type=int, default=8)
    p_self.add_argument("--no-write", action="store_true")

    p_train = sub.add_parser("train-numeric")
    p_train.add_argument("--prompt", required=True)
    p_train.add_argument("--file", action="append", required=True)

    p_predict = sub.add_parser("predict-numeric")
    p_predict.add_argument("--prompt", required=True)
    p_predict.add_argument("--top-n", type=int, default=6)

    p_response = sub.add_parser("log-response")
    p_response.add_argument("--prompt", required=True)
    p_response.add_argument("--response", required=True)
    p_response.add_argument("--style-arm")
    p_response.add_argument("--hook-id", action="append", default=[])
    p_response.add_argument("--intent-node", action="append", default=[])
    p_response.add_argument("--context-window-file", action="append", default=[])
    p_response.add_argument("--feedback", default="")

    p_edit = sub.add_parser("log-edit")
    p_edit.add_argument("--file")
    p_edit.add_argument("--why", default="codex edit")
    p_edit.add_argument("--prompt")

    sub.add_parser("capture-pair")
    sub.add_parser("state")

    p_shed = sub.add_parser("shed")
    p_shed.add_argument("--module", required=True)
    p_shed.add_argument("--confidence", type=float, required=True)
    p_shed.add_argument("--note", default="")

    p_launch = sub.add_parser("launch-observatory")
    p_launch.add_argument("--thought-completer", action="store_true")

    p_deepseek = sub.add_parser("launch-deepseek")
    p_deepseek.add_argument("--dry-run", action="store_true")

    p_intent = sub.add_parser("push-intent-resolver")
    p_intent.add_argument("--prompt-limit", type=int, default=100)

    sub.add_parser("intent-loop-status")

    p_close_loop = sub.add_parser("close-intent-loop")
    p_close_loop.add_argument("--loop-id")
    p_close_loop.add_argument("--status", default="verified")
    p_close_loop.add_argument("--note", default="")

    p_closeout = sub.add_parser(
        "submit-closeout",
        help="Agent end-of-work notes before backwards pass / push (deferred bugs, unsaid flags).",
    )
    p_closeout.add_argument("--note", default="", help="Freeform closeout summary")
    p_closeout.add_argument("--file", action="append", default=[], help="Touched files this session")
    p_closeout.add_argument(
        "--deferred-bug",
        action="append",
        default=[],
        help="Bug noticed but not fixed: title|file|reason",
    )
    p_closeout.add_argument("--completed-fix", action="append", default=[], help="Fix completed this session")
    p_closeout.add_argument("--unsaid-flag", action="append", default=[], help="Risk/flag left unsaid during work")
    p_closeout.add_argument("--source", default="cursor_agent")

    sub.add_parser("bug-notice-stats", help="How many bugs agents noticed vs deferred vs fixed")

    p_intent_attn = sub.add_parser(
        "intent-attention-stats",
        help="Per-file operator vs edit vs file intent grades (X/Y/Z alignment)",
    )
    p_intent_attn.add_argument("--file", default="", help="Filter to one file path")

    p_patch_reg = sub.add_parser(
        "patch-registry",
        help="Bootstrap/reconcile pigeon_registry.json and file identity aliases",
    )
    p_patch_reg.add_argument("--rebuild", action="store_true", help="Force full registry rebuild from disk scan")

    p_stale = sub.add_parser("stale-date-audit")
    p_stale.add_argument("--max-lag-minutes", type=int, default=30)

    p_import = sub.add_parser("import-jsonl")
    p_import.add_argument("source")
    p_import.add_argument("--no-capture", action="store_true")
    return parser
