# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v008 | 635 lines | ~6,981 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: chore_run_push_cycle
# LAST:   2026-04-20 @ afa395a
# SESSIONS: 6
# ──────────────────────────────────────────────
"""git_plugin_main_orchestrator_seq019_v001.py — Pigeon-extracted by compiler."""
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.pigeon_limits import is_excluded
from pigeon_compiler.rename_engine import (
    load_registry,
    save_registry,
    build_pigeon_filename,
    parse_pigeon_stem,
    bump_version,
    build_compressed_filename,
    mutate_compressed_stem,
    bug_marker_from_keys,
    rewrite_all_imports,
    extract_desc_slug,
    build_all_manifests,
)
from pigeon_compiler.session_logger import log_session, count_sessions
import ast
import os
import re

# ── Pigeon-decomposed sibling helpers (cross-linked namespace) ──
# The sibling modules were auto-extracted by the pigeon compiler and they call
# each other's `_underscore` helpers directly (e.g. git_ops uses `_git` from
# helpers) without explicit imports. Python keeps each module's globals
# separate so those calls raise NameError at runtime.
# Fix: collect the union of all sibling symbols and write it back into every
# sibling's __dict__, re-creating the shared namespace the decomposer assumed.
def _pull_sibling_symbols() -> None:
    import importlib
    siblings = [
        "p_git__s001_v001",
        "p_gph_s002_v002_d0419_λGI",
        "p_gpgo_s003_v001",
        "p_gpip_s004_v003_d0420_λFX",
        "p_gpci_s007_v001",
        "p_gpoh_s009_v001",
        "p_gpop_s008_v001",
        "p_gprc_s010_v001",
        "p_gpda_s012_v001",
        "p_gpds_s011_v001",
        "p_gpet_s013_v001",
        "p_gipcp_s014_v001",
        "p_gpcg_s015_v001",
        "p_git__s005_v001",
        "p_gpos_s016_v001",
        "p_gppb_s006_v001",
        "p_gppc_s017_v001",
    ]
    loaded = []
    for mod_name in siblings:
        try:
            mod = importlib.import_module(f"pigeon_compiler.git_plugin.{mod_name}")
            loaded.append(mod)
        except Exception:
            continue
    # Build union dict of all symbols.
    union: dict = {}
    for mod in loaded:
        for sym in dir(mod):
            if sym.startswith("__"):
                continue
            if sym not in union:
                union[sym] = getattr(mod, sym)
    # Pull into orchestrator namespace.
    ns = globals()
    for sym, val in union.items():
        if sym not in ns:
            ns[sym] = val
    # Cross-link: put the union back into every sibling so they can see each
    # other's helpers when the orchestrator calls them.
    for mod in loaded:
        mod_ns = mod.__dict__
        for sym, val in union.items():
            if sym not in mod_ns:
                mod_ns[sym] = val

_pull_sibling_symbols()

def _load_dotenv(root: Path) -> None:
    """Load .env into os.environ (no external deps)."""
    env_path = root / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def run():
    root = _root()
    _load_dotenv(root)  # ensure API keys available for all submodules
    msg = _commit_msg()

    if '[pigeon-auto]' in msg:
        return

    h = _commit_hash()
    intent = _parse_intent(msg)
    changed = _changed_files()
    if not changed:
        return

    registry = load_registry(root)
    edit_whys = _load_edit_whys(root)
    edit_authors = _load_edit_authors(root)
    renames = []        # (old_rel, new_rel, entry, tokens_before, diff_stat)
    box_only = []       # (abs_path, entry, old_rel, tokens_before, diff_stat)
    import_map = {}     # old_module → new_module
    today = datetime.now(timezone.utc).strftime('%m%d')

    for rel in changed:
        p = Path(rel)
        if p.suffix != '.py' or is_excluded(p):
            continue
        # Root-level debug scripts — skip
        if '/' not in rel and '\\' not in rel and _ROOT_DEBUG.match(p.name):
            continue
        abs_p = root / rel
        if not abs_p.exists():
            continue

        parsed = parse_pigeon_stem(p.stem)
        if not parsed:
            continue

        desc = extract_desc_slug(abs_p) or parsed['desc']
        try:
            file_text = abs_p.read_text(encoding='utf-8')
        except Exception:
            file_text = ''
        tokens = _estimate_tokens(file_text)
        tokens_before = tokens  # snapshot before mutation
        diff_stat = _file_diff_stat(rel)

        entry = registry.get(rel)
        if entry and entry.get('ver') is not None:
            entry = bump_version(entry, new_desc=desc, new_intent=intent)
            entry['tokens'] = tokens
            entry['intent_code'] = _intent_code(entry.get('intent', intent))
            entry['history'][-1]['tokens'] = tokens
        elif entry:
            # Corrupt/incomplete registry entry — rebuild from parsed stem
            entry = None
        if not entry:
            entry = {
                'path': rel, 'name': parsed['name'],
                'seq': parsed['seq'], 'ver': parsed['ver'] + 1,
                'date': today, 'desc': desc, 'intent': intent,
                'intent_code': _intent_code(intent),
                'bug_keys': [],
                'bug_counts': {},
                'bug_entities': {},
                'last_bug_mark': '',
                'tokens': tokens,
                'history': [{'ver': parsed['ver'] + 1, 'date': today,
                             'desc': desc, 'intent': intent,
                             'tokens': tokens,
                             'action': 'registered'}],
            }

        # Attach 3-word last_change from pulse EDIT_WHY
        why = edit_whys.get(rel, '')
        if not why:
            # Try matching by filename only (edit_pairs stores relative paths)
            for ew_path, ew_val in edit_whys.items():
                if ew_path.endswith(p.name) or ew_path.endswith(rel):
                    why = ew_val
                    break
        if why:
            entry['last_change'] = why
            # Attribute the change to its actual author
            author = edit_authors.get(rel, '')
            if not author:
                for ea_path, ea_val in edit_authors.items():
                    if ea_path.endswith(p.name) or ea_path.endswith(rel):
                        author = ea_val
                        break
            entry['last_change_author'] = author or 'copilot'

        # Compressed files — mutate filename in-place (bump ver, date, intent)
        if parsed.get('compressed'):
            new_name = mutate_compressed_stem(
                p.stem,
                new_ver=entry['ver'],
                new_date=today,
                new_intent=entry.get('intent_code') or _intent_code(intent),
            )
            if new_name and Path(new_name).stem != p.stem:
                folder = str(p.parent).replace('\\', '/')
                new_rel = f'{folder}/{new_name}' if folder != '.' else new_name
                entry['path'] = new_rel
                if rel in registry:
                    del registry[rel]
                registry[new_rel] = entry
                renames.append((rel, new_rel, entry, tokens_before, diff_stat))
                old_mod = str(Path(rel).with_suffix('')).replace('\\', '.').replace('/', '.')
                new_mod = str(Path(new_rel).with_suffix('')).replace('\\', '.').replace('/', '.')
                import_map[old_mod] = new_mod
            else:
                entry['path'] = rel
                registry[rel] = entry
                box_only.append((abs_p, entry, rel, tokens_before, diff_stat))
            continue

        # Prefer pulse EDIT_WHY as last-change reason in filename over generic commit intent
        last_change_slug = entry.get('last_change', '')
        if last_change_slug:
            lc_words = re.sub(r'[^a-zA-Z0-9]', ' ', last_change_slug).split()[:3]
            filename_intent = '_'.join(w.lower() for w in lc_words) if lc_words else intent
        else:
            filename_intent = intent

        new_name = build_pigeon_filename(
            parsed['name'], parsed['seq'], entry['ver'],
            entry['date'], desc, filename_intent,
        )
        folder = str(p.parent).replace('\\', '/')
        new_rel = f'{folder}/{new_name}' if folder != '.' else new_name
        entry['path'] = new_rel

        if rel in registry and rel != new_rel:
            del registry[rel]
        registry[new_rel] = entry

        if p.stem != Path(new_name).stem:
            renames.append((rel, new_rel, entry, tokens_before, diff_stat))
            old_mod = str(Path(rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            new_mod = str(Path(new_rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            import_map[old_mod] = new_mod
        else:
            box_only.append((abs_p, entry, rel, tokens_before, diff_stat))

    if not renames and not box_only:
        # No pigeon-managed files changed — but still run narrative + coaching
        # for non-pigeon code (client/, vscode-extension/, etc.)
        all_changed_code = [f for f in changed
                            if f.endswith(('.py', '.ts', '.js'))]
        if all_changed_code:
            print(f'\n🐦 Pigeon Git Plugin: 0 rename(s), 0 update(s), '
                  f'{len(all_changed_code)} non-pigeon file(s)')
            _run_post_commit_extras(root, intent, h, all_changed_code,
                                    registry, msg)
        return

    print(f'\n🐦 Pigeon Git Plugin: {len(renames)} rename(s), '
          f'{len(box_only)} update(s)')

    # Rewrite imports BEFORE renaming files (safe order — old files still exist)
    if import_map:
        changes = rewrite_all_imports(root, import_map)
        if changes:
            files_hit = len({c['file'] for c in changes})
            print(f'  ↳ {len(changes)} import(s) rewritten in {files_hit} file(s)')

    # Execute renames (after imports are updated)
    for old_rel, new_rel, entry, _, _ in renames:
        old_abs, new_abs = root / old_rel, root / new_rel
        if old_abs.exists():
            new_abs.parent.mkdir(parents=True, exist_ok=True)
            old_abs.rename(new_abs)
            print(f'  📝 {Path(old_rel).name}')
            print(f'     → {Path(new_rel).name}')

    # Log sessions + inject prompt boxes
    for old_rel, new_rel, entry, tb, ds in renames:
        log_session(root, new_rel, entry, h, msg, ds, old_path=old_rel, tokens_before=tb)
        new_abs = root / new_rel
        if new_abs.exists():
            _inject_box(new_abs, entry, h, root)
    for abs_p, entry, old_rel, tb, ds in box_only:
        log_session(root, old_rel, entry, h, msg, ds, tokens_before=tb)
        _inject_box(abs_p, entry, h, root)

    # Save registry
    save_registry(root, registry)

    # Save registry-backed prompt metadata via the central prompt manager later in the flow
    processed = len(renames) + len(box_only)

    # ── Self-fix: one-shot cross-file problem scan ──
    changed_py = [nr for _, nr, _, _, _ in renames] + [r for _, _, r, _, _ in box_only]
    cross_context = {}
    try:
        fix_mod = _load_glob_module(root, 'src', '修f_sf_s013*')
        if fix_mod:
            fix_report = fix_mod.run_self_fix(
                root, registry, changed_py=changed_py, intent=intent)
            cross_context = fix_report.get('cross_context', {})
            bug_keys = _collect_bug_keys(fix_report.get('problems', []))
            for path, entry in registry.items():
                entry['intent_code'] = _intent_code(entry.get('intent', ''))
                _sync_bug_metadata(entry, bug_keys.get(path, []), today)
            save_registry(root, registry)
            fix_path = fix_mod.write_self_fix_report(root, fix_report, h)
            n_probs = len(fix_report.get('problems', []))
            print(f'  🔧 self-fix → {fix_path.relative_to(root)} ({n_probs} problems)')
            # Auto-compile: split any pigeon files over 200-line hard cap, pruning dead exports
            try:
                if hasattr(fix_mod, 'auto_compile_oversized'):
                    compiled = fix_mod.auto_compile_oversized(root, fix_report, max_files=5)
                    for c in compiled:
                        if c.get('status') == 'ok':
                            pruned = c.get('dead_pruned', [])
                            print(f'  🪦 auto-compiled: {Path(c["file"]).name}')
                            print(f'     → {c["files"]} file(s) in {c["output_dir"]}')
                            if pruned:
                                print(f'     ✂️  pruned dead: {", ".join(pruned)}')
                        else:
                            print(f'  ⚠️  auto-compile {c["file"]}: {c.get("error")}')
            except Exception as e:
                print(f'  ⚠️  auto-compile oversized: {e}')
    except Exception as e:
        print(f'  ⚠️  self-fix: {e}')

    bug_renames = []
    bug_import_map = {}
    bug_path_map = {}
    for rel in list(changed_py):
        entry = registry.get(rel)
        if not entry:
            continue
        p = Path(rel)
        parsed = parse_pigeon_stem(p.stem)
        if not parsed or not parsed.get('compressed'):
            continue
        bug_marker = bug_marker_from_keys(entry.get('bug_keys', []))
        new_name = mutate_compressed_stem(
            p.stem,
            new_ver=entry.get('ver'),
            new_date=entry.get('date') or today,
            new_intent=entry.get('intent_code') or _intent_code(entry.get('intent', '')),
            new_bugs=bug_marker,
        )
        if not new_name or Path(new_name).stem == p.stem:
            continue
        folder = str(p.parent).replace('\\', '/')
        new_rel = f'{folder}/{new_name}' if folder != '.' else new_name
        bug_renames.append((rel, new_rel, entry))
        bug_path_map[rel] = new_rel
        old_mod = str(Path(rel).with_suffix('')).replace('\\', '.').replace('/', '.')
        new_mod = str(Path(new_rel).with_suffix('')).replace('\\', '.').replace('/', '.')
        bug_import_map[old_mod] = new_mod

    if bug_import_map:
        bug_changes = rewrite_all_imports(root, bug_import_map)
        if bug_changes:
            files_hit = len({c['file'] for c in bug_changes})
            print(f'  🐛 {len(bug_changes)} bug-mark import(s) rewritten in {files_hit} file(s)')
        import_map.update(bug_import_map)

    for old_rel, new_rel, entry in bug_renames:
        old_abs, new_abs = root / old_rel, root / new_rel
        if not old_abs.exists():
            continue
        new_abs.parent.mkdir(parents=True, exist_ok=True)
        old_abs.rename(new_abs)
        if old_rel in registry:
            del registry[old_rel]
        entry['path'] = new_rel
        registry[new_rel] = entry
        print(f'  👹 {Path(old_rel).name}')
        print(f'     → {Path(new_rel).name}')

    if bug_path_map:
        changed_py = [bug_path_map.get(path, path) for path in changed_py]
        save_registry(root, registry)

    # ── TC Trajectory Update: track λ mutations in TC_MANIFEST ──
    # Every rename with a new λ suffix updates the file's trajectory
    try:
        tc_manifest_seq001_v001_mod = _load_glob_module(root, 'src', 'tc_manifest_seq001_v001*')
        if tc_manifest_seq001_v001_mod and hasattr(tc_manifest_seq001_v001_mod, 'update_file_trajectory'):
            trajectory_count = 0
            # Process all renames from this commit
            for old_rel, new_rel, entry in (renames + bug_renames):
                parsed = parse_pigeon_stem(Path(new_rel).stem)
                if parsed and parsed.get('intent'):
                    lambda_suffix = 'λ' + parsed['intent']
                    stem = parsed.get('abbrev', '') or parsed.get('name', '')[:10]
                    deduction = entry.get('intent', 'mutation')[:40]
                    tc_manifest_seq001_v001_mod.update_file_trajectory(stem, lambda_suffix, deduction)
                    trajectory_count += 1
            if trajectory_count:
                print(f'  📜 TC trajectory → {trajectory_count} file(s) tracked')
    except Exception as e:
        print(f'  ⚠️  TC trajectory: {e}')

    for entry in registry.values():
        entry['intent_code'] = _intent_code(entry.get('intent', ''))
        entry.setdefault('bug_keys', [])
        entry.setdefault('bug_counts', {})
        entry.setdefault('bug_entities', {})
        entry.setdefault('last_bug_mark', '')
    save_registry(root, registry)

    # ── Pulse harvest: failsafe for any un-cleared pulse blocks ──
    try:
        pulse_mod = _load_glob_module(root, 'src', '脉p_ph_s015*')
        if pulse_mod:
            recs = pulse_mod.harvest_all_pulses(root)
            if recs:
                print(f'  📡 pulse harvest → {len(recs)} edit(s) paired to prompts')
            # Also inject pulse blocks into any new files
            n_injected = pulse_mod.inject_all_pulses(root)
            if n_injected:
                print(f'  📡 pulse inject → {n_injected} new pulse block(s)')
    except Exception as e:
        print(f'  ⚠️  pulse harvest: {e}')

    # ── Interlink check: run self-tests on touched modules ──
    try:
        interlink_mod = _load_glob_module(root, 'src', 'interlinker_seq001_v001*')
        if interlink_mod and changed_py:
            interlinked = 0
            for cp in changed_py[:10]:  # cap at 10 files
                fp = root / cp
                if fp.exists() and fp.suffix == '.py':
                    try:
                        result = interlink_mod.interlink_module(fp, root)
                        if result.get('state') == 'interlinked':
                            interlinked += 1
                    except Exception:
                        pass
            if interlinked:
                print(f'  🔗 interlink → {interlinked} module(s) interlinked')
    except Exception as e:
        print(f'  ⚠️  interlink check: {e}')

    # ── Organism test upgrade: LLM rewrites baseline tests autonomously ──
    try:
        upgrade_mod = _load_glob_module(root, 'src', 'interlinker_seq001_v001_upgrade_seq001_v001*')
        if upgrade_mod and changed_py:
            changed_fps = [root / cp for cp in changed_py if (root / cp).exists()]
            results = upgrade_mod.run_upgrade_cycle(root, changed_fps)
            upgraded = sum(1 for r in results if r.get('upgraded'))
            if upgraded:
                print(f'  🧬 organism → {upgraded} test(s) upgraded')
    except Exception as e:
        print(f'  ⚠️  organism upgrade: {e}')

    # ── Push narrative + coaching + operator state ──
    all_changed_code = changed_py + [f for f in changed
                                      if f.endswith(('.py', '.ts', '.js'))
                                      and f not in changed_py]
    _run_post_commit_extras(root, intent, h, all_changed_code, registry, msg,
                            renames=renames, box_only=box_only,
                            cross_context=cross_context)

    # Unified Copilot prompt management — ensure all managed prompt blocks and audits stay in sync
    try:
        prompt_mod = _load_glob_module(root, 'src', '管w_cpm_s020*')
        if prompt_mod:
            result = prompt_mod.refresh_managed_prompt(root, registry=registry, processed=processed)
            audit = result.get('audit', {}) if isinstance(result, dict) else {}
            missing = audit.get('missing_blocks', []) if isinstance(audit, dict) else []
            unfilled = audit.get('unfilled_fields', []) if isinstance(audit, dict) else []
            print('  🧩 copilot prompt manager refreshed blocks + audit')
            if missing:
                print(f'     missing blocks: {", ".join(missing)}')
            if unfilled:
                print(f'     unfilled fields: {", ".join(unfilled)}')
    except Exception as e:
        print(f'  ⚠️  prompt manager: {e}')

    # Rebuild manifests
    try:
        build_all_manifests(root)
    except Exception as e:
        print(f'  ⚠️  Manifest rebuild: {e}')

    # ── Staleness audit ──
    # Per operator intent (2026-04-17): close the loop between managed-block
    # freshness and operator awareness. Staleness detector previously only
    # ran on UI events in classify_bridge — now it runs on every commit so
    # Copilot sees fresh stale-warnings even when the chat UI is closed.
    try:
        stale_mod = _load_glob_module(root, 'src', '警p_sa_s030*')
        if stale_mod and hasattr(stale_mod, 'inject_staleness_alert'):
            injected = stale_mod.inject_staleness_alert(root)
            if injected:
                print('  ⚠️  staleness alert injected — managed blocks rotted')
    except Exception as e:
        print(f'  ⚠️  staleness audit: {e}')

    # Self-fix accuracy — score recurring threads across reports
    try:
        sft_mod = _load_glob_module(root, 'src', 'self_fix_tracker_seq001_v001*')
        if sft_mod and hasattr(sft_mod, 'compute_accuracy'):
            acc = sft_mod.compute_accuracy(root)
            if 'error' not in acc:
                print(f"  📊 self-fix accuracy: {acc['total_threads']} threads, "
                      f"fix rate {round(acc['avg_fix_rate'] * 100, 1)}% "
                      f"({acc['status_breakdown'].get('resolved', 0)} resolved, "
                      f"{acc['status_breakdown'].get('eternal', 0)} eternal)")
    except Exception as e:
        print(f'  ⚠️  self-fix accuracy: {e}')

    # Context compression — strip comments/docstrings/annotations for LLM context
    try:
        cc_mod = _load_glob_module(root, 'src', 'context_compressor_seq001_v001*')
        if cc_mod and hasattr(cc_mod, 'compress_changed'):
            cc_result = cc_mod.compress_changed(root, changed_files=changed)
            if cc_result['files'] > 0:
                print(f"  🗜️  compression: {cc_result['orig_tokens']}→{cc_result['compressed_tokens']} tokens "
                      f"({cc_result['ratio']}x, {cc_result['files']} files, {cc_result['elapsed_ms']}ms)")
    except Exception as e:
        print(f'  ⚠️  context compression: {e}')

    # Intent compression — 5-layer deep compression analysis
    try:
        ic_mod = _load_glob_module(root, 'src', 'intent_compressor_seq001_v001*')
        if ic_mod and hasattr(ic_mod, 'compress_all'):
            ic_result = ic_mod.compress_all(root)
            cl = ic_result.get('compression_layers', {})
            ist = ic_result.get('intent_stats', {})
            l3 = cl.get('layer3_skeleton', {})
            print(f"  🧠 intent compression: {ic_result.get('total_original_tokens', 0)}→"
                  f"{l3.get('tokens', 0)} tok skeleton "
                  f"({l3.get('ratio', 0)}x, {ist.get('intent_amplification', 0)}x intent amp)")
    except Exception as e:
        print(f'  ⚠️  intent compression: {e}')

    # Codebase transmutation — numerical mirror + narrative mirror + global stats
    try:
        ct_mod = _load_glob_module(root, 'src', 'codebase_transmuter_seq001_v001*')
        if ct_mod and hasattr(ct_mod, 'transmute_all'):
            tr = ct_mod.transmute_all(root)
            s = tr.get('stats', {})
            n = tr.get('numerical', {})
            print(f"  🔢 transmute: {s.get('files', 0)} files, {s.get('tokens', 0)} tok, "
                  f"noise {s.get('noise_pct', 0)}%, "
                  f"numerical {n.get('ratio', 0)}x ({n.get('unique_symbols', 0)} symbols)")
    except Exception as e:
        print(f'  ⚠️  codebase transmutation: {e}')

    # Record codebase vitals snapshot
    try:
        vitals_mod = _load_glob_module(root, 'src', 'codebase_vitals_seq001_v001*')
        if vitals_mod and hasattr(vitals_mod, 'record_vitals'):
            vitals_mod.record_vitals(root, h, msg.splitlines()[0][:80])
            print('  📊 vitals snapshot recorded')
        renderer_mod = _load_glob_module(root, 'src', 'vitals_renderer_seq001_v001*')
        if renderer_mod and hasattr(renderer_mod, 'render_dashboard'):
            renderer_mod.render_dashboard(root)
            print('  📊 vitals dashboard rebuilt')
    except Exception as e:
        print(f'  ⚠️  vitals: {e}')

    # Compute total token footprint for this commit
    total_tokens = sum(
        e.get('tokens', 0) for _, _, e, _, _ in renames
    ) + sum(
        _estimate_tokens(fp.read_text(encoding='utf-8'))
        for fp, _, _, _, _ in box_only if fp.exists()
    )

    # Validate imports before committing — catch broken state early
    rename_count = len(renames) + len(bug_renames)
    if rename_count:
        val = validate_imports(root)
        if not val['valid']:
            broken = val['broken']
            print(f'  ⚠️  {len(broken)} broken import(s) detected after rename:')
            for b in broken[:10]:
                print(f"      {b['file']}:{b['line']}  {b['import']}")
            # Attempt a second rewrite pass with broader matching
            extra = rewrite_all_imports(root, import_map)
            if extra:
                print(f'  🔧 Second pass fixed {len(extra)} import(s)')

    # ── Autonomous Escalation Engine ──
    # The modules have earned the right to fix themselves.
    # 6-level ladder: REPORT → ASK → INSIST → WARN → ACT → VERIFY
    try:
        esc_mod = _load_glob_module(root, 'src', 'escalation_engine_seq001_v001*')
        if esc_mod and hasattr(esc_mod, 'check_and_escalate'):
            esc_result = esc_mod.check_and_escalate(root)
            esc_actions = esc_result.get('actions', [])
            esc_warnings = esc_result.get('warnings', [])
            if esc_actions:
                for a in esc_actions:
                    emoji = '✅' if a['result'] == 'success' else '🔙' if a['result'] == 'rolled_back' else '⚠️'
                    print(f"  {emoji} 自 {a['module']}: {a.get('description', a['action'])}")
                    if a.get('message'):
                        print(f"       \"{a['message']}\"")
            if esc_warnings:
                print(f"  🪜 escalation warnings issued for: {', '.join(esc_warnings)}")
            tracked = esc_result.get('total_modules_tracked', 0)
            total_fixes = esc_result.get('total_autonomous_fixes', 0)
            if tracked:
                print(f"  📊 escalation: {tracked} tracked, {total_fixes} autonomous fixes total")
    except Exception as e:
        print(f'  ⚠️  autonomous escalation: {e}')

    # ── Learning Loop Catch-Up ──
    # Process new journal entries on every push. The loop was never
    # wired as a daemon — this is the only place it runs.
    try:
        ll_mod = _load_glob_module(root, 'pigeon_brain/flow', '学f_ll_s013*')
        if ll_mod and hasattr(ll_mod, 'catch_up'):
            ll_result = ll_mod.catch_up(root, use_deepseek=False)
            processed = ll_result.get('entries_processed', 0)
            trained = ll_result.get('total_nodes_trained', 0)
            if processed:
                print(f'  🧠 learning loop: {processed} entries, {trained} nodes trained')
    except Exception as e:
        print(f'  ⚠️  learning loop catch-up: {e}')

    # Auto-commit
    _git('add', '-A')
    if _git('status', '--porcelain').strip():
        n = rename_count
        _git('commit', '-m',
             f'chore(pigeon): auto-rename {n} file(s) [pigeon-auto]\n\n'
             f'Intent: {intent}\n'
             f'Tokens: ~{total_tokens:,}\n'
             f'Triggered by: {msg.splitlines()[0]}')
        print(f'  ✅ Auto-committed [pigeon-auto] (~{total_tokens:,} tokens)\n')
    else:
        print(f'  ℹ️  No changes to auto-commit\n')
