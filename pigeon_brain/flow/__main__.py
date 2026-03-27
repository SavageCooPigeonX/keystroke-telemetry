# pigeon_brain/flow/__main__.py — CLI entry point
"""
Usage:
  Forward pass:
    py -m pigeon_brain.flow flow "Fix the hardcoded import in __main__.py"
    py -m pigeon_brain.flow flow --mode heat "self_fix keeps failing"
    py -m pigeon_brain.flow flow --multi "import rewriter breaks after rename"
    py -m pigeon_brain.flow flow --origin self_fix "analyze why v10 has high drama"

  Backward pass:
    py -m pigeon_brain.flow backward <electron_id>

  Talk to nodes:
    py -m pigeon_brain.flow talk self_fix "Why do you keep flagging __main__.py?"
    py -m pigeon_brain.flow talk --worst "What is your biggest problem?"

  Predict:
    py -m pigeon_brain.flow predict

  Dev plan:
    py -m pigeon_brain.flow plan

  Fix summary:
    py -m pigeon_brain.flow fix-summary
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .flow_engine_seq003_v002_d0324__the_flow_engine_is_the_lc_flow_engine_context import run_flow, run_multi
from .task_writer_seq005_v002_d0324__the_river_delta_where_all_lc_flow_engine_context import write_task, write_multi
from .backward_seq007_v001_d0325__backward_pass_gradient_distributor_lc_backprop_impl import (
    backward_pass, log_forward_pass,
)
from .node_conversation_seq012_v001_d0325__node_conversation_interface_lc_backprop_impl import (
    talk_to_node, find_worst_node,
)
from .predictor_seq009_v001_d0325__phantom_electron_predictor_lc_backprop_impl import (
    predict_next_needs,
)
from .dev_plan_seq010_v001_d0325__self_development_plan_generator_lc_backprop_impl import (
    generate_dev_plan,
)
from .fix_summary_seq011_v001_d0325__structured_diff_analysis_lc_backprop_impl import (
    generate_fix_summary,
)
from .learning_loop_seq013_v001_d0327__perpetual_forward_backward_training_lc_deepseek_backprop import (
    run_loop, catch_up,
)
from .prediction_scorer_seq014_v001_d0327__prediction_vs_reality_feedback_lc_e2e_loop import (
    score_predictions_post_edit, score_predictions_post_commit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flow engine — context-accumulating dataflow with backpropagation"
    )
    sub = parser.add_subparsers(dest="command")
    parser.add_argument("--root", default=".", help="Project root")

    # flow <task> — forward pass
    fw = sub.add_parser("flow", help="Run forward pass (default)")
    fw.add_argument("task", help="The task/bug/question to flow through the graph")
    fw.add_argument("--mode", choices=["targeted", "heat", "failure"],
                    default="targeted", help="Path selection mode")
    fw.add_argument("--multi", action="store_true",
                    help="Run all 3 modes and merge perspectives")
    fw.add_argument("--origin", default=None,
                    help="Explicit start node (auto-detected if omitted)")
    fw.add_argument("--root", default=".")

    # backward <electron_id>
    bw = sub.add_parser("backward", help="Run backward pass for an electron")
    bw.add_argument("electron_id", help="The electron ID from a forward pass")
    bw.add_argument("--root", default=".")

    # talk <node> <question>   OR   talk --worst <question>
    tk = sub.add_parser("talk", help="Talk to a graph node")
    tk.add_argument("node", nargs="?", help="Node name (omit with --worst)")
    tk.add_argument("question", nargs="?", default="What is your biggest problem?")
    tk.add_argument("--worst", action="store_true", help="Auto-select worst node")
    tk.add_argument("--root", default=".")

    # predict
    pr = sub.add_parser("predict", help="Fire phantom electrons from cognitive profile")
    pr.add_argument("--root", default=".")

    # plan
    pl = sub.add_parser("plan", help="Generate self-development plan")
    pl.add_argument("--root", default=".")

    # fix-summary
    fs = sub.add_parser("fix-summary", help="Generate structured fix summary from last commit")
    fs.add_argument("--root", default=".")

    # loop — perpetual learning
    lp = sub.add_parser("loop", help="Start perpetual learning loop (forward→backward→learn)")
    lp.add_argument("--once", action="store_true",
                    help="Process new entries once then exit")
    lp.add_argument("--catch-up", action="store_true",
                    help="Process ALL unprocessed journal entries then exit")
    lp.add_argument("--no-deepseek", action="store_true",
                    help="Skip DeepSeek calls (heuristic-only backward pass)")
    lp.add_argument("--root", default=".")

    # score — score predictions against actual commit diff
    sc = sub.add_parser("score", help="Score predictions against last commit diff")
    sc.add_argument("--root", default=".")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "flow":
        _cmd_forward(root, args)
    elif args.command == "backward":
        _cmd_backward(root, args)
    elif args.command == "talk":
        _cmd_talk(root, args)
    elif args.command == "predict":
        _cmd_predict(root)
    elif args.command == "plan":
        _cmd_plan(root)
    elif args.command == "fix-summary":
        _cmd_fix_summary(root)
    elif args.command == "loop":
        _cmd_loop(root, args)
    elif args.command == "score":
        _cmd_score(root)
    else:
        parser.print_help()


def _cmd_forward(root: Path, args: argparse.Namespace) -> None:
    """Run forward pass and log it."""
    if args.multi:
        packets = run_multi(root, args.task, origin=args.origin)
        for p in packets:
            s = p.summary()
            s["accumulated"] = [
                {"node": i.node, "fears": i.fears, "dual_score": i.dual_score,
                 "relevance": i.relevance}
                for i in p.accumulated
            ]
            eid = log_forward_pass(root, s)
            print(f"[logged electron {eid} mode={p.mode}]")
        output = write_multi(packets)
    else:
        packet = run_flow(root, args.task, mode=args.mode, origin=args.origin)
        s = packet.summary()
        s["accumulated"] = [
            {"node": i.node, "fears": i.fears, "dual_score": i.dual_score,
             "relevance": i.relevance}
            for i in packet.accumulated
        ]
        eid = log_forward_pass(root, s)
        print(f"[logged electron {eid}]")
        output = write_task(packet)
    print(output)


def _cmd_backward(root: Path, args: argparse.Namespace) -> None:
    """Run backward pass from latest prompt journal entry."""
    journal = root / "logs" / "prompt_journal.jsonl"
    if not journal.exists():
        print("No prompt journal found.")
        return
    last_line = journal.read_text(encoding="utf-8").strip().splitlines()[-1]
    entry = json.loads(last_line)

    results = backward_pass(root, args.electron_id, entry)
    if not results:
        print(f"No forward path found for electron {args.electron_id}")
        return
    print(f"Backward pass complete — {len(results)} nodes updated:")
    for r in results:
        print(f"  {r['node']}: credit={r['credit']:.3f}, loss={r['loss']:.3f}")


def _cmd_talk(root: Path, args: argparse.Namespace) -> None:
    """Talk to a node."""
    node = args.node
    if args.worst or not node:
        node = find_worst_node(root)
        if not node:
            print("No nodes with enough learning history to identify worst performer.")
            return
        print(f"[auto-selected worst node: {node}]")
    question = args.question or "What is your biggest problem?"
    output = talk_to_node(root, node, question)
    print(output)


def _cmd_predict(root: Path) -> None:
    """Fire phantom electrons."""
    predictions = predict_next_needs(root, run_flow_fn=run_flow)
    if not predictions:
        print("Not enough journal data for predictions (need 3+ entries).")
        return
    print(f"Fired {len(predictions)} phantom electrons:")
    for p in predictions:
        print(f"  [{p['mode']}] confidence={p['confidence']:.2f}: {p['phantom_seed'][:80]}")


def _cmd_plan(root: Path) -> None:
    """Generate dev plan."""
    output = generate_dev_plan(root)
    print(output)


def _cmd_fix_summary(root: Path) -> None:
    """Generate fix summary from last commit."""
    summary = generate_fix_summary(root)
    print(json.dumps(summary, indent=2))


def _cmd_loop(root: Path, args: argparse.Namespace) -> None:
    """Start perpetual learning loop."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    use_ds = not getattr(args, "no_deepseek", False)
    if getattr(args, "catch_up", False):
        print("[learning_loop] Catching up on all unprocessed entries...")
        result = catch_up(root, use_deepseek=use_ds)
        print(f"[learning_loop] Done — {result['entries_processed']} processed, "
              f"{result['total_nodes_trained']} nodes trained, "
              f"{result['cycles']} total cycles")
        return
    run_loop(root, once=getattr(args, "once", False), use_deepseek=use_ds)


def _cmd_score(root: Path) -> None:
    """Score predictions against edit sessions (primary) + commit diff (secondary)."""
    # Primary: edit-session scoring
    result = score_predictions_post_edit(root)
    if result["status"] == "scored":
        print(f"Edit-session scoring: {result['predictions_scored']} predictions")
        print(f"  Avg combined: {result['avg_combined']:.3f}")
        print(f"  Avg F1: {result['avg_f1']:.3f}")
        print(f"  Overconfidence rate: {result['overconfidence_rate']:.2f}")
        print(f"  Nodes updated: {result['nodes_updated']}")
        print(f"  Edit pairs available: {result['edits_available']}")
    elif result["status"] == "no_predictions":
        print("No predictions to score. Run 'predict' first.")
        return
    else:
        print(f"Edit-session scoring: {result['status']}")

    # Secondary: commit-diff audit
    commit_result = score_predictions_post_commit(root)
    if commit_result.get("status") == "scored":
        print(f"\nCommit-diff audit: {commit_result['predictions_scored']} predictions")
        print(f"  Avg F1: {commit_result['avg_f1']:.3f}")
        print(f"  Changed files: {commit_result['changed_files']}")
        print(f"  Actual modules: {', '.join(commit_result['actual_modules'][:10])}")


if __name__ == "__main__":
    main()
