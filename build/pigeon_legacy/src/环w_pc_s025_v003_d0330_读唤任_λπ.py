"""Push-based learning cycle — the PUSH is the unit of learning.

Each git push = one learning cycle:
  1. Collect all prompts since last push (operator signal)
  2. Collect git diff (copilot signal — the operator never types code)
  3. Compute sync score (did copilot output match operator intent?)
  4. Generate dual coaching (for operator AND for coding agent)
  5. Score old predictions (how accurate were last cycle's guesses?)
  6. Run backward pass on journal entries (gradient distribution)
  7. Fire new predictions (what will operator want next push?)
  8. Inject predictions into copilot-instructions
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CYCLE_STATE_PATH = "logs/push_cycle_state.json"
CYCLE_LOG_PATH = "logs/push_cycles.jsonl"
JOURNAL_PATH = "logs/prompt_journal.jsonl"
PREDICTION_LOG_PATH = "logs/push_predictions.jsonl"
COPILOT_BRAIN_PATH = "logs/copilot_brain_map.json"


def _load_pigeon_module(root: Path, folder: str, pattern: str):
    """Dynamically import a pigeon module by glob (filenames mutate).

    Sets __package__ so relative imports inside sub-packages (like backward_seq007)
    resolve correctly via the parent folder as the package.
    """
    import importlib.util, sys
    base = root / folder
    matches = sorted(base.glob(f'{pattern}.py'))
    if not matches:
        return None
    fpath = matches[-1]
    # Derive package name from folder path (e.g. pigeon_brain/flow → pigeon_brain.flow)
    pkg_name = folder.replace('/', '.').replace('\\', '.')
    # Ensure parent package is in sys.modules
    parts = pkg_name.split('.')
    for i in range(len(parts)):
        partial = '.'.join(parts[:i+1])
        if partial not in sys.modules:
            pkg_dir = root / '/'.join(parts[:i+1])
            init_file = pkg_dir / '__init__.py'
            if init_file.exists():
                pspec = importlib.util.spec_from_file_location(
                    partial, init_file,
                    submodule_search_locations=[str(pkg_dir)])
                if pspec and pspec.loader:
                    pmod = importlib.util.module_from_spec(pspec)
                    sys.modules[partial] = pmod
                    try:
                        pspec.loader.exec_module(pmod)
                    except Exception:
                        pass
            else:
                # Create a namespace package stub
                import types
                pmod = types.ModuleType(partial)
                pmod.__path__ = [str(pkg_dir)]
                pmod.__package__ = partial
                sys.modules[partial] = pmod

    mod_name = f'{pkg_name}.{fpath.stem}'
    spec = importlib.util.spec_from_file_location(
        mod_name, fpath,
        submodule_search_locations=None)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_state(root: Path) -> dict:
    p = root / CYCLE_STATE_PATH
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:
            pass
    return {"last_journal_line": 0, "total_cycles": 0, "last_commit": None}


def _save_state(root: Path, state: dict) -> None:
    p = root / CYCLE_STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2) + "\n", "utf-8")


def _load_journal_since(root: Path, after_line: int) -> list[dict]:
    """Load all prompt_journal entries since the last push."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return []
    entries = []
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if i <= after_line or not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries


def _extract_operator_signal(entries: list[dict]) -> dict:
    """Aggregate operator signal from all prompts in this push cycle."""
    if not entries:
        return {"prompt_count": 0}
    wpms = [e.get("signals", {}).get("wpm", 0) or e.get("wpm", 0) for e in entries]
    dels = [e.get("signals", {}).get("deletion_ratio", 0) or e.get("deletion_ratio", 0) for e in entries]
    hess = [e.get("signals", {}).get("hesitation_count", 0) for e in entries]
    intents = {}
    for e in entries:
        intent = e.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
    module_refs = set()
    for e in entries:
        for m in e.get("module_refs", []):
            module_refs.add(m)
    deleted_words = []
    for e in entries:
        for w in e.get("deleted_words", []):
            if isinstance(w, str):
                deleted_words.append(w)
            elif isinstance(w, dict):
                deleted_words.append(w.get("word", ""))
    states = {}
    for e in entries:
        s = e.get("cognitive_state", "unknown")
        states[s] = states.get(s, 0) + 1
    avg = lambda xs: sum(xs) / len(xs) if xs else 0
    return {
        "prompt_count": len(entries),
        "avg_wpm": round(avg(wpms), 1),
        "avg_deletion": round(avg(dels), 3),
        "total_hesitations": sum(hess),
        "intent_distribution": intents,
        "dominant_intent": max(intents, key=lambda key: intents.get(key, 0)) if intents else "unknown",
        "module_refs": sorted(module_refs),
        "deleted_words": deleted_words[-20:],
        "cognitive_states": states,
        "dominant_state": max(states, key=lambda key: states.get(key, 0)) if states else "unknown",
    }


def _extract_copilot_signal(changed_files: list[str]) -> dict:
    """Extract copilot signal from the git diff (files changed = copilot wrote)."""
    py_files = [f for f in changed_files if f.endswith(".py")]
    modules_touched = set()
    for f in py_files:
        stem = Path(f).stem
        # Strip pigeon suffix to get base module name
        parts = stem.split("_seq")
        if parts:
            modules_touched.add(parts[0])
    return {
        "files_changed": len(changed_files),
        "py_files_changed": len(py_files),
        "modules_touched": sorted(modules_touched),
        "non_py_files": [f for f in changed_files if not f.endswith(".py")],
    }


def _train_intent_numeric_seq001_v001(entries: list[dict], changed_files: list[str]) -> None:
    """Train intent_numeric_seq001_v001 surface: journal prompts → files touched."""
    try:
        from src._resolve import src_import as _src_import
        record_touch = _src_import("intent_numeric_seq001", "record_touch")
    except (ImportError, AttributeError):
        return
    
    # Combine all prompts in this cycle into one training signal
    combined_prompt = ' '.join(e.get('msg', '') for e in entries if e.get('msg'))
    if not combined_prompt or len(combined_prompt) < 10:
        return
    
    # Get Python file stems (module names)
    modules = []
    for f in changed_files:
        if f.endswith('.py'):
            stem = Path(f).stem
            # Strip pigeon suffix
            parts = stem.split('_seq')
            if parts:
                modules.append(parts[0])
    
    if modules:
        record_touch(combined_prompt, modules, learning_rate=0.1)


def _refresh_copilot_brain_signal(root: Path) -> None:
    """Refresh heat + Copilot brain map before a push cycle snapshot."""
    try:
        heat_mod = _load_pigeon_module(root, 'src', '热p_fhm_s011*')
        if heat_mod and hasattr(heat_mod, 'update_heat_map'):
            heat_mod.update_heat_map(root)
    except Exception:
        pass


def _load_copilot_brain_signal(root: Path) -> dict:
    """Load the latest Copilot-edit brain map if available."""
    path = root / COPILOT_BRAIN_PATH
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return {}


def _enrich_copilot_signal_with_brain(copilot: dict, brain: dict) -> dict:
    """Attach Copilot-edit-only entropy hotspots to the cycle signal."""
    if not brain:
        copilot['brain_source'] = 'missing'
        copilot['brain_modules_tracked'] = 0
        copilot['brain_hotspots'] = []
        copilot['brain_regions'] = []
        copilot['touched_module_entropy'] = []
        return copilot

    modules = brain.get('modules', {})
    touched = []
    for mod in copilot.get('modules_touched', []):
        data = modules.get(mod)
        if not data:
            continue
        touched.append({
            'module': mod,
            'region': data.get('region', 'cortex'),
            'edit_entropy': data.get('edit_entropy', 0.0),
            'brain_heat': data.get('brain_heat', 0.0),
            'event_count': data.get('event_count', 0),
            'dominant_state': data.get('dominant_state', 'unknown'),
        })
    touched.sort(key=lambda item: (-item['brain_heat'], -item['edit_entropy'], item['module']))

    copilot['brain_source'] = brain.get('source', 'unknown')
    copilot['brain_modules_tracked'] = brain.get('modules_tracked', 0)
    copilot['brain_global_entropy'] = brain.get('global_avg_edit_entropy', 0.0)
    copilot['brain_hotspots'] = [
        {
            'module': item.get('module', ''),
            'region': item.get('region', 'cortex'),
            'edit_entropy': item.get('edit_entropy', 0.0),
            'brain_heat': item.get('brain_heat', 0.0),
        }
        for item in brain.get('top_modules', [])[:5]
    ]
    copilot['brain_regions'] = [
        {
            'region': item.get('region', 'cortex'),
            'avg_entropy': item.get('avg_entropy', 0.0),
            'brain_heat': item.get('brain_heat', 0.0),
            'module_count': item.get('module_count', 0),
        }
        for item in brain.get('regions', [])[:3]
    ]
    copilot['touched_module_entropy'] = touched[:8]
    return copilot


def _compute_sync(operator: dict, copilot: dict) -> dict:
    """Compute sync between operator intent and copilot output.

    Sync = how well did the code changes match what the operator was asking for?
    Since the operator never types code, ALL code is copilot.
    Operator → prompts (intent). Copilot → diffs (output).
    """
    op_modules = set(operator.get("module_refs", []))
    cp_modules = set(copilot.get("modules_touched", []))

    if not op_modules and not cp_modules:
        return {"score": 0.5, "reason": "no module references in either signal"}

    # Module overlap between operator references and copilot changes
    overlap = op_modules & cp_modules
    union = op_modules | cp_modules
    jaccard = len(overlap) / len(union) if union else 0.0

    # Effort ratio — prompts per file changed (lower = more efficient sync)
    prompts = operator.get("prompt_count", 1)
    files = max(copilot.get("py_files_changed", 1), 1)
    effort_ratio = prompts / files

    # Intent alignment — was the operator debugging/building/etc and did code change?
    intent = operator.get("dominant_intent", "unknown")
    intent_bonus = 0.0
    if intent == "debugging" and copilot.get("py_files_changed", 0) > 0:
        intent_bonus = 0.1  # fix intent + actual code change = aligned
    elif intent == "building" and copilot.get("py_files_changed", 0) >= 2:
        intent_bonus = 0.15  # build intent + multiple files = strong alignment
    elif intent == "restructuring" and copilot.get("py_files_changed", 0) >= 3:
        intent_bonus = 0.1  # restructure + many files = aligned

    # Frustration penalty — high deletion/hesitation = poor sync
    frustration_penalty = 0.0
    if operator.get("avg_deletion", 0) > 0.4:
        frustration_penalty = 0.1
    if operator.get("dominant_state") == "frustrated":
        frustration_penalty += 0.05

    sync_score = min(1.0, max(0.0,
        jaccard * 0.5 + intent_bonus + (1.0 / max(effort_ratio, 0.5)) * 0.3 - frustration_penalty
    ))

    return {
        "score": round(sync_score, 3),
        "jaccard": round(jaccard, 3),
        "module_overlap": sorted(overlap),
        "operator_only": sorted(op_modules - cp_modules),
        "copilot_only": sorted(cp_modules - op_modules),
        "effort_ratio": round(effort_ratio, 2),
        "intent_alignment": intent,
        "frustration_penalty": round(frustration_penalty, 3),
    }


def _generate_dual_coaching(operator: dict, copilot: dict, sync: dict) -> dict:
    """Generate coaching for BOTH the operator and the coding agent."""
    operator_tips = []
    agent_tips = []
    touched_entropy = copilot.get("touched_module_entropy", [])

    # Operator coaching based on their signal
    if operator.get("avg_deletion", 0) > 0.4:
        operator_tips.append("High deletion rate — try articulating intent more clearly before typing. Outline the task first.")
    if operator.get("prompt_count", 0) > 10 and copilot.get("py_files_changed", 0) < 3:
        operator_tips.append("Many prompts, few file changes — consider being more specific about which modules to touch.")
    if sync.get("operator_only"):
        operator_tips.append(f"You referenced {sync['operator_only']} but copilot didn't touch them — be more explicit about expected changes.")
    if operator.get("dominant_state") == "frustrated" and operator.get("prompt_count", 0) > 5:
        operator_tips.append("Frustration detected across multiple prompts — try breaking the task into smaller pushable units.")
    if not operator.get("module_refs"):
        operator_tips.append("No module references detected in prompts — naming specific modules helps copilot target the right files.")
    if copilot.get("brain_regions"):
        hottest_region = copilot["brain_regions"][0]
        if hottest_region.get("avg_entropy", 0) > 0.25:
            operator_tips.append(
                f"Copilot edit pressure is concentrated in {hottest_region['region']} — narrower prompts may reduce retouch churn in that region."
            )

    # Agent coaching based on copilot signal
    if sync.get("copilot_only"):
        agent_tips.append(f"Touched {sync['copilot_only']} without operator reference — confirm intent before modifying unreferenced modules.")
    if sync.get("effort_ratio", 0) > 5:
        agent_tips.append("Operator needed many prompts — respond with more complete implementations to reduce round-trips.")
    if sync.get("score", 0) < 0.3:
        agent_tips.append("Low sync score — operator intent and code output diverged. Ask clarifying questions earlier.")
    if copilot.get("py_files_changed", 0) > 15:
        agent_tips.append("Large blast radius — prefer focused changes. Wide scatter makes it hard for operator to verify.")
    if touched_entropy:
        hottest_touch = touched_entropy[0]
        if hottest_touch.get("edit_entropy", 0) > 0.3:
            agent_tips.append(
                f"Recent edits to {hottest_touch['module']} show high Copilot retouch entropy — prefer a fuller fix over another partial pass."
            )

    return {
        "operator_coaching": operator_tips or ["Good sync — keep current communication pattern."],
        "agent_coaching": agent_tips or ["Good alignment with operator intent."],
    }


def run_push_cycle(root: Path, commit_hash: str, intent: str,
                   changed_files: list[str]) -> dict[str, Any]:
    """Run one push-based learning cycle. Called by git_plugin post-commit."""
    state = _load_state(root)
    _refresh_copilot_brain_signal(root)
    brain = _load_copilot_brain_signal(root)

    # 1. Collect operator signal (all prompts since last push)
    entries = _load_journal_since(root, state["last_journal_line"])
    operator = _extract_operator_signal(entries)

    # 2. Collect copilot signal (what code changed)
    copilot = _extract_copilot_signal(changed_files)
    copilot = _enrich_copilot_signal_with_brain(copilot, brain)

    # 3. Compute sync
    sync = _compute_sync(operator, copilot)

    # 4. Generate dual coaching
    coaching = _generate_dual_coaching(operator, copilot, sync)

    # 5. Score old predictions from last cycle
    score_result = _score_old_predictions(root)

    # 6. Backward pass on key journal entries (gradient distribution)
    backward_results = _run_backward_on_entries(root, entries)

    # 6.5. Train intent_numeric_seq001_v001 surface: journal prompts → files touched
    _train_intent_numeric_seq001_v001(entries, changed_files)

    # 7. Fire new predictions (what will operator want next push?)
    predictions = _fire_predictions(root)

    # 8. Build cycle record
    now = datetime.now(timezone.utc).isoformat()
    total_journal_lines = state["last_journal_line"] + len(entries)
    cycle = {
        "ts": now,
        "commit": commit_hash,
        "intent": intent,
        "cycle_number": state["total_cycles"] + 1,
        "operator_signal": operator,
        "copilot_signal": copilot,
        "sync": sync,
        "coaching": coaching,
        "prediction_score": score_result,
        "backward_runs": len(backward_results),
        "new_predictions": len(predictions),
    }

    # 8. Append to cycle log
    log_path = root / CYCLE_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle) + "\n")

    # 9. Update state
    state["last_journal_line"] = total_journal_lines
    state["total_cycles"] += 1
    state["last_commit"] = commit_hash
    state["last_sync_score"] = sync["score"]
    state["last_prediction_count"] = len(predictions)
    state["updated_at"] = now
    _save_state(root, state)

    # 10. Inject predictions + coaching into copilot-instructions.md
    _inject_predictions_into_prompt(root, predictions, coaching)

    # 11. Capture codebase health snapshot + compute drift
    try:
        from src.push_snapshot_seq001_v001 import capture_snapshot, compute_drift, inject_drift_block
        snapshot = capture_snapshot(root, commit_hash, intent, changed_files)
        drift_result = compute_drift(root, snapshot)
        inject_drift_block(root, snapshot, drift_result)
        cycle['snapshot_health'] = snapshot.get('modules', {}).get('compliance_pct', 0)
        cycle['drift_direction'] = drift_result.get('drift', {}).get('health_direction', 'unknown')
    except Exception as e:
        cycle['snapshot_error'] = str(e)[:200]

    # 12. Inject narrative glove (organism consciousness)
    try:
        from src.narrative_glove_seq001_v001 import inject_narrative
        inject_narrative(root)
    except Exception:
        pass

    # 13. Baseline drift assessment — truth gate + semantic void detection
    try:
        from src.push_baseline_seq001_v001 import assess_on_push, build_drift_report
        baseline = assess_on_push(root, changed_files)
        cycle['baseline_drift'] = baseline.get('total_drift', 0)
        cycle['baseline_voids'] = baseline.get('total_voids', 0)
        cycle['modules_assessed'] = baseline.get('modules_assessed', 0)
        # inject drift report into copilot-instructions
        drift_block = build_drift_report(root)
        if drift_block:
            _inject_pigeon_block(root, 'baseline-drift', drift_block)
    except Exception as e:
        cycle['baseline_error'] = str(e)[:200]

    # 14. File semantic layer — grow per-file context + intent drift detection
    try:
        from src.file_semantic_layer_seq001_v001 import grow_on_push, build_semantic_report
        sem = grow_on_push(root, changed_files)
        cycle['semantic_modules'] = sem.get('modules_processed', 0)
        cycle['semantic_escalated'] = sem.get('escalated', 0)
        cycle['semantic_growing'] = sem.get('growing', 0)
        sem_block = build_semantic_report(root)
        if sem_block:
            _inject_pigeon_block(root, 'semantic-layer', sem_block)
    except Exception as e:
        cycle['semantic_error'] = str(e)[:200]

    return cycle


# ── Moon Cycle stages (backward → predict → inject) ─────────────────────────

def _score_old_predictions(root: Path) -> dict:
    """Score predictions from the LAST push cycle against what actually happened."""
    try:
        scorer = _load_pigeon_module(root, 'pigeon_brain/flow', '算f_ps_s014*')
        if scorer and hasattr(scorer, 'score_predictions_post_commit'):
            return scorer.score_predictions_post_commit(root)
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}
    return {"status": "no_scorer"}


def _run_backward_on_entries(root: Path, entries: list[dict]) -> list[dict]:
    """Run backward pass on journal entries — distribute credit to nodes.

    Only runs on high-signal entries (frustrated/hesitant state or high deletion)
    to keep DeepSeek costs bounded. Max 3 backward passes per push.
    """
    backward_mod = _load_pigeon_module(root, 'pigeon_brain/flow', '逆f_ba_s007*')
    if not backward_mod or not hasattr(backward_mod, 'backward_pass'):
        return []

    # Select high-signal entries worth running backward pass on
    candidates = []
    for e in entries:
        signals = e.get("signals", {})
        state = e.get("cognitive_state", "unknown")
        del_ratio = signals.get("deletion_ratio", 0) or e.get("deletion_ratio", 0)
        if state in ("frustrated", "hesitant", "confused") or del_ratio > 0.3:
            candidates.append(e)

    # Cap at 3 to keep DeepSeek costs bounded (~$0.009 max per push)
    candidates = candidates[:3]
    results = []
    for entry in candidates:
        try:
            # Build a synthetic electron_id from the entry
            eid = entry.get("session_id", "") + "_" + str(entry.get("session_n", 0))
            backward_results = backward_mod.backward_pass(
                root,
                electron_id=eid,
                journal_entry=entry,
                fix_context=entry.get("msg", ""),
                use_deepseek=True,
            )
            results.extend(backward_results)
        except Exception:
            pass  # DeepSeek timeout or model error — skip, don't block push
    return results


def _fire_predictions(root: Path) -> list[dict]:
    """Fire new predictions for what operator will want next push cycle."""
    predictor = _load_pigeon_module(root, 'pigeon_brain/flow', '预p_pr_s009*')
    if not predictor or not hasattr(predictor, 'predict_next_needs'):
        return []

    try:
        predictions = predictor.predict_next_needs(
            root,
            run_flow_fn=None,  # no phantom execution — just predict
            n_predictions=3,
        )
        # Persist to prediction log for post-commit scoring
        log_path = root / PREDICTION_LOG_PATH
        log_path.parent.mkdir(parents=True, exist_ok=True)
        for p in predictions:
            p["cycle_ts"] = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            for p in predictions:
                f.write(json.dumps(p) + "\n")
        return predictions
    except Exception:
        return []


def _inject_pigeon_block(root: Path, tag: str, block: str) -> None:
    """Replace a <!-- pigeon:TAG --> block in copilot-instructions.md."""
    ci_path = root / ".github" / "copilot-instructions.md"
    if not ci_path.exists():
        return
    content = ci_path.read_text("utf-8")
    start_tag = f"<!-- pigeon:{tag} -->"
    end_tag = f"<!-- /pigeon:{tag} -->"
    si = content.find(start_tag)
    ei = content.find(end_tag)
    if si >= 0 and ei >= 0:
        content = content[:si] + block + content[ei + len(end_tag):]
    else:
        op_marker = "<!-- pigeon:operator-state -->"
        oi = content.find(op_marker)
        if oi >= 0:
            content = content[:oi] + block + "\n\n" + content[oi:]
        else:
            content += "\n\n" + block
    ci_path.write_text(content, "utf-8")


def _inject_predictions_into_prompt(root: Path, predictions: list[dict],
                                     coaching: dict) -> None:
    """Inject predictions + coaching into copilot-instructions.md.

    Writes a <!-- pigeon:predictions --> block so Copilot knows what
    the operator will likely want next and can prepare proactively.
    """
    if not predictions and not coaching:
        return

    lines = ["<!-- pigeon:predictions -->",
             "## Push Cycle Predictions",
             "",
             f"*Auto-generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC*",
             ""]

    if predictions:
        lines.append("**What you'll likely want next push:**")
        # Deduplicate: if phantom_seed and modules are identical, only show the first occurrence
        seen_seeds: set[str] = set()
        unique_preds = []
        for p in predictions:
            key = p.get("phantom_seed", "") + "|" + ",".join(p.get("trend", {}).get("modules", []))
            if key not in seen_seeds:
                seen_seeds.add(key)
                unique_preds.append(p)
        for i, p in enumerate(unique_preds, 1):
            seed = p.get("phantom_seed", p.get("prediction_id", "?"))
            conf = p.get("confidence", 0)
            mode = p.get("mode", "?")
            trend = p.get("trend", {})
            modules = trend.get("modules", [])
            lines.append(f"{i}. [{mode}] {seed[:120]} (conf={conf:.0%})")
            if modules:
                lines.append(f"   - hot modules: {', '.join(modules[:5])}")
        lines.append("")

    if coaching.get("operator_coaching"):
        lines.append("**Operator coaching:**")
        for tip in coaching["operator_coaching"]:
            lines.append(f"- {tip}")
        lines.append("")

    if coaching.get("agent_coaching"):
        lines.append("**Agent coaching (for Copilot):**")
        for tip in coaching["agent_coaching"]:
            lines.append(f"- {tip}")
        lines.append("")

    lines.append("<!-- /pigeon:predictions -->")
    block = "\n".join(lines)

    # Inject into copilot-instructions.md
    ci_path = root / ".github" / "copilot-instructions.md"
    if not ci_path.exists():
        return

    content = ci_path.read_text("utf-8")
    start_tag = "<!-- pigeon:predictions -->"
    end_tag = "<!-- /pigeon:predictions -->"

    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)

    if start_idx >= 0 and end_idx >= 0:
        content = content[:start_idx] + block + content[end_idx + len(end_tag):]
    else:
        # Insert before the operator-state block (or at end)
        op_marker = "<!-- pigeon:operator-state -->"
        op_idx = content.find(op_marker)
        if op_idx >= 0:
            content = content[:op_idx] + block + "\n\n" + content[op_idx:]
        else:
            content += "\n\n" + block

    ci_path.write_text(content, "utf-8")
