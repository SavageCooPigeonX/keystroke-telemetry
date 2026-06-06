"""git_plugin_seq021_v001.py — Pigeon-extracted by compiler."""
from .git_plugin_seq001_v001 import _load_glob_module
from .git_plugin_seq010_v001 import _load_deep_signals
from .git_plugin_seq012_v001 import _generate_commit_coaching
import json
import os
import re

def _run_post_commit_extras(root, intent, h, changed_files, registry, msg,
                            renames=None, box_only=None, cross_context=None):
    """Run narrative, coaching, operator-state for ANY commit."""
    renames = renames or []
    box_only = box_only or []

    # Auto-reconstruct prompt compositions from os_keystrokes before narrative
    try:
        recon_mod = _load_glob_module(root, 'src', 'u_prc_s016*')
        if recon_mod:
            new_entries = recon_mod.reconstruct_all(root)
            if new_entries:
                print(f'  🔬 prompt recon: {len(new_entries)} new composition(s)')
            # Track copilot prompt mutations
            mutations = recon_mod.track_copilot_prompt_mutations(root)
            mc = mutations.get('total_mutations', 0)
            if mc:
                print(f'  🧬 copilot prompt: {mc} mutations tracked')
    except Exception as e:
        print(f'  ⚠️  prompt recon: {e}')

    # Push narrative — include ALL changed code files, not just pigeon
    try:
        narr_mod = _load_glob_module(root, 'src', '叙p_pn_s012*')
        if narr_mod:
            deep = _load_deep_signals(root)
            print(f'  📝 generating push narrative ({len(changed_files)} files)...')
            narr_path = narr_mod.generate_push_narrative(
                root, intent, h, changed_files, registry,
                rework_stats=deep.get('rework'),
                query_mem=deep.get('query'),
                heat_map=deep.get('heat'),
                cross_context=cross_context or {},
            )
            if narr_path:
                print(f'  📖 push narrative → {narr_path.relative_to(root)}')
    except Exception as e:
        print(f'  ⚠️  push narrative: {e}')

    # Generate LLM coaching at commit time
    try:
        coaching_ok = _generate_commit_coaching(
            root, intent, renames, box_only, registry
        )
        if coaching_ok:
            print('  🧠 commit coaching synthesized → operator_coaching.md')
    except Exception as e:
        print(f'  ⚠️  commit coaching: {e}')

    # Managed prompt blocks are refreshed centrally by copilot_prompt_manager_seq020.

    # Mutation scorer — correlate prompt evolution with rework verdicts
    try:
        ms_mod = _load_glob_module(root, 'src', '变p_ms_s021*')
        if ms_mod:
            ms_result = ms_mod.score_mutations(root)
            pairs = ms_result.get('total_pairs', 0)
            if pairs:
                print(f'  📈 mutation scorer: {pairs} pair(s) analyzed')
    except Exception as e:
        print(f'  ⚠️  mutation scorer: {e}')

    # Rework backfill — score historical AI responses from chat history
    try:
        rb_mod = _load_glob_module(root, 'src', '补p_rwb_s022*')
        if rb_mod:
            added = rb_mod.backfill(root)
            if added:
                print(f'  📑 rework backfill: {added} new pair(s) scored')
    except Exception as e:
        print(f'  ⚠️  rework backfill: {e}')

    # Research lab — synthesize prediction report from all telemetry
    try:
        research_mod = _load_glob_module(root, 'src', '研w_rl_s029*')
        if research_mod:
            report_path = research_mod.synthesize_research(root)
            if report_path and report_path.exists():
                print(f'  🔬 research report → {report_path.relative_to(root)}')
    except Exception as e:
        print(f'  ⚠️  research lab: {e}')

    # Intent simulator — forward projection of operator intent per push
    try:
        intent_mod = _load_glob_module(root, 'src', '意w_is_s034*')
        if intent_mod:
            sim_path = intent_mod.simulate_intent(root, inject=True)
            if sim_path and sim_path.exists():
                print(f'  🔮 intent simulation → {sim_path.relative_to(root)}')
    except Exception as e:
        print(f'  ⚠️  intent simulator: {e}')

    # Self-fix: auto-apply CRITICAL hardcoded import fixes
    try:
        sf_mod = _load_glob_module(root, 'src', '修f_sf_s013*')
        if sf_mod and hasattr(sf_mod, 'auto_apply_import_fixes'):
            fixes = sf_mod.auto_apply_import_fixes(root)
            if fixes:
                applied = [f for f in fixes if f.get('applied')]
                print(f'  🔧 self-fix: {len(applied)} hardcoded import(s) auto-applied')
    except Exception as e:
        print(f'  ⚠️  self-fix auto-apply: {e}')

    # Task queue — mark any task IDs mentioned in commit as done
    try:
        tq_mod = _load_glob_module(root, 'src', '队p_tq_s018*')
        if tq_mod and hasattr(tq_mod, 'mark_done'):
            task_ids = re.findall(r'\btq-\d{3}\b', msg)
            for tid in task_ids:
                if tq_mod.mark_done(root, tid, commit=h):
                    print(f'  ✅ task {tid} marked done')
            if task_ids and hasattr(tq_mod, 'inject_task_queue'):
                tq_mod.inject_task_queue(root)
    except Exception as e:
        print(f'  ⚠️  task queue: {e}')

    # File consciousness — rebuild dating profiles + slumber party audit
    try:
        fc_mod = _load_glob_module(root, 'src', '觉w_fc_s019*')
        if fc_mod:
            profiles = fc_mod.build_dating_profiles(root)
            fc_mod.save_profiles(root, profiles)
            print(f'  💒 file consciousness: {len(profiles)} dating profiles updated')
            talks = fc_mod.slumber_party_audit(root, changed_files)
            if talks:
                print(f'  🛌  slumber party: {len(talks)} contract check(s)')
                for t in talks[:3]:
                    print(f'     [{t["severity"]}] {t["changed"]} ↔ {t["partner"]}')
    except Exception as e:
        print(f'  ⚠️  file consciousness: {e}')

    # Push learning cycle — the PUSH is the unit of learning
    try:
        pc_mod = _load_glob_module(root, 'src', '环w_pc_s025*')
        if pc_mod and hasattr(pc_mod, 'run_push_cycle'):
            cycle = pc_mod.run_push_cycle(root, h, intent, changed_files)
            sync = cycle.get('sync', {})
            coaching = cycle.get('coaching', {})
            print(f'  🔄 push cycle #{cycle.get("cycle_number", "?")}: sync={sync.get("score", "?")}'
                  f' | {cycle.get("operator_signal", {}).get("prompt_count", 0)} prompts → {cycle.get("copilot_signal", {}).get("py_files_changed", 0)} files')
            if cycle.get('backward_runs', 0):
                print(f'  ⬅️  backward pass: {cycle["backward_runs"]} gradient(s) distributed')
            if cycle.get('new_predictions', 0):
                print(f'  🔮 predictions: {cycle["new_predictions"]} phantom(s) fired for next cycle')
            ps = cycle.get('prediction_score', {})
            if ps.get('status') == 'scored':
                print(f'  📊 scored old predictions: avg_f1={ps.get("avg_f1", "?")} | overconf={ps.get("overconfidence_rate", "?")}')
            for tip in coaching.get('operator_coaching', [])[:2]:
                print(f'     👤 operator: {tip}')
            for tip in coaching.get('agent_coaching', [])[:2]:
                print(f'     🤖 agent: {tip}')

            # ── Training cycle summary — intent alignment per push ──
            try:
                tp_mod = _load_glob_module(root, 'src', '对p_tp_s027*')
                if tp_mod and hasattr(tp_mod, 'generate_cycle_summary'):
                    summary = tp_mod.generate_cycle_summary(root, cycle)
                    n = summary.get('pair_count', 0)
                    m = summary.get('metrics', {})
                    avg_rw = m.get('avg_rework_score')
                    phys = m.get('physical_keystroke_rate', 0)
                    print(f'  🎯 training: {n} pairs | rework={avg_rw} | physical_rate={phys}')
            except Exception as te:
                print(f'  ⚠️  training summary: {te}')
    except Exception as e:
        print(f'  ⚠️  push cycle: {e}')

    # Voice style — personality adaptation from operator's actual language
    try:
        vs_mod = _load_glob_module(root, 'src', '训w_trwr_s028*')
        if vs_mod and hasattr(vs_mod, 'inject_voice_style'):
            ok = vs_mod.inject_voice_style(root)
            if ok:
                profile = vs_mod.build_voice_profile(root)
                n_dir = len(profile.get('directives', []))
                print(f'  🗣️  voice style: {profile.get("prompt_count", 0)} prompts → {n_dir} directives injected')
    except Exception as e:
        print(f'  ⚠️  voice style: {e}')

    # Intent→outcome binding — close the intent loop with real diff content
    try:
        import importlib.util as _ilu
        _binder_path = root / 'src' / 'intent_outcome_binder_seq001_v001.py'
        if _binder_path.exists():
            _spec = _ilu.spec_from_file_location('intent_outcome_binder_seq001_v001', _binder_path)
            _binder = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_binder)
            _result = _binder.bind_commit(root, 'HEAD')
            _rename = _result.get('rename_engine') or {}
            _imports = _rename.get('import_validation') or {}
            _outcome = _result.get('outcome_binding') or {}
            if not _result.get('skipped'):
                print(f'  outcome binder: {_outcome.get("outcomes", 0)} outcome(s), '
                      f'rename_fired={_rename.get("fired", False)} imports_valid={_imports.get("valid", False)}')
                print(f'  🔗 intent binding: {_result["bound"]}/{_result["files_changed"]} files matched '
                      f'({_result["unmatched"]} unmatched) → edit_pairs.jsonl')
    except Exception as e:
        print(f'  ⚠️  intent binding: {e}')
