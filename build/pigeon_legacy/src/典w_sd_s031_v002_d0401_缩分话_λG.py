"""Symbol dictionary generator for Pigeon Code v4.0 Glyph System.

Reads pigeon_registry.json + git log and generates dictionary.pgd —
a symbol-to-meaning mapping that overlays the existing long filenames.

Filenames stay long. The dictionary is an additional layer for LLM
context compression: ~300-500 tokens to encode the entire codebase
architecture vs thousands of tokens reading raw filenames.
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
import subprocess
from pathlib import Path
from datetime import datetime, timezone

try:
    from src.u_cs_s033_v001 import (
        score_module_confidence, compute_copilot_meta_state, format_confidence_line,
    )
except ImportError:
    score_module_confidence = None
    compute_copilot_meta_state = None
    format_confidence_line = None

# ── Chinese character pool for top-level modules ──
# Each char is 1 token, semantically self-documenting.
_PRIMARY_POOL = list(
    '修算境流热漂正思叙规引录桥查忆推演测层控'
    '织联脉图谱核分拆补审写读压缩编译扫描追踪'
)

# ── Mnemonic hints: Chinese chars matched to module meaning ──
_MNEMONIC_MAP = {
    'self_fix': '修',            # repair/fix
    'prediction_scorer': '算',   # calculate/predict
    'context_budget': '境',      # boundary/context
    'flow_engine': '流',         # flow/stream
    'file_heat_map': '热',       # heat
    'drift_watcher': '漂',       # drift/float
    'compliance': '正',          # correct/standard
    'cognitive_reactor': '思',   # thought/cognition
    'push_narrative': '叙',      # narrate/tell
    'import_rewriter': '引',     # lead/import
    'logger': '录',              # record/log
    'resistance_bridge': '桥',   # bridge
    'query_memory': '忆',        # memory/recall
    'dynamic_prompt': '推',      # push/infer
    'streaming_layer': '层',     # layer
    'operator_stats': '控',      # control/operator
    'research_lab': '研',        # research
    'models': '型',              # model/type
    'graph_extractor': '图',     # graph/diagram
    'file_writer': '写',         # write
    'scanner': '扫',             # scan
    'validator': '审',           # audit/validate
    'file_consciousness': '觉',  # consciousness/awareness
    'rework_detector': '测',     # measure/detect
    'symbol_dictionary': '典',   # dictionary/canon
    'glyph_compiler': '编',      # compile/weave
    'copilot_prompt_manager': '管', # manage
    'mutation_scorer': '变',     # mutate/change
    'unsaid': '隐',              # hidden/unsaid
    'training_writer': '训',     # train
    'voice_style': '声',         # voice/sound
    'session_handoff': '递',     # hand off/pass
    'staleness_alert': '警',     # alert/warn
    'shard_manager': '片',       # shard/piece
    'context_router': '路',      # route/path
    'push_cycle': '环',          # cycle/loop
    'task_queue': '队',          # queue
    'pulse_harvest': '脉',       # pulse
    'unified_signal': '合',      # combine/unify
    'training_pairs': '对',      # pair
    'rework_backfill': '补',     # patch/backfill
    'unsaid_recon': '探',        # explore/recon
    'pigeon_compiler': '鸽',     # pigeon
    'timestamp_utils': '时',     # time
    'context_packet': '包',      # packet
    'backward': '逆',            # backward/reverse
    'node_memory': '存',         # store/memory
    'predictor': '预',           # predict
    'learning_loop': '学',       # learn
    'demo_sim': '仿',            # simulate
    'dual_substrate': '双',      # dual
    'live_server': '服',         # serve
    'traced_runner': '跑',       # run
    'trace_hook': '钩',          # hook
    'cli': '令',                 # command
    'adapter': '适',             # adapt
    'drift': '偏',               # bias/drift
    # ── compiler + runner modules ──
    'node_awakener': '唤',       # awaken
    'path_selector': '择',       # select/choose
    'task_writer': '任',         # task
    'vein_transport': '脉运',    # vein transport
    'node_conversation': '话',   # conversation
    'observer_synthesis': '观',  # observe
    'loop_detector': '环检',     # loop detect
    'manifest_builder': '谱建',  # build manifest
    'manifest_bridge': '谱桥',   # bridge manifest
    'plan_parser': '析',         # parse/analyze
    'plan_validator': '验',      # verify
    'resistance_analyzer': '阻',  # resistance
    'registry': '册',            # registry
    'run_heal': '追跑',          # heal-run
    'run_rename': '改名',        # rename
    'run_pigeon_loop': '鸽环',   # pigeon loop
    'run_clean_split': '净拆',   # clean split
    'run_clean_split_helpers': '净助', # clean split helpers
    'run_clean_split_init': '净初',  # clean split init
    'run_batch_compile': '批编',  # batch compile
    'run_compiler_test': '测编',  # test compiler
    'run_deepseek_plans': '深划',  # deepseek plans
    'reaudit_diff': '复审',      # re-audit
    'pq_manifest_utils': '清单',  # manifest utils
    'press_release_gen_constants': '稿常',  # press constants
    'press_release_gen_template_builders': '稿建',  # press builders
    'press_release_gen_template_helpers': '稿助',  # press helpers
    'nametag': '牌',             # tag/name plate
    'shared_state_detector': '共态',  # shared state
    'source_slicer': '切',       # slice
    'resplit': '重拆',           # re-split
    'resplit_binpack': '重箱',   # re-split bin
    'resplit_helpers': '重助',   # re-split helpers
    'init_writer': '初写',       # init writer
}

# ── Intent lambda codes ──
_INTENT_PREFIXES = {
    'dynamic_import_resolvers': 'λR',
    'pigeon_split_3': 'λS',
    'organism_health_system': 'λH',
    'gemini_flash_enricher': 'λF',
    '8888_word_backpropagation': 'λB',
    'windows_max_path': 'λW',
    'desc_upgrade': 'λD',
    'mutation_patch_pipeline': 'λM',
    'intent_deletion_pipeline': 'λI',
    'staleness_alerts_bg': 'λA',
    'pigeon_brain_system': 'λP',
    'push_narratives_timeout': 'λT',
    'research_lab_autonomous': 'λL',
    'task_queue_system': 'λQ',
    'pulse_telemetry_prompt': 'λΠ',
    'import_rewriter_now': 'λΞ',
    'rework_signal_0': 'λρ',
    'stage_78_hook': 'λ7',
    'wpm_outlier_filter': 'λω',
    'fire_full_post': 'λφ',
    'fix_bare_globals': 'λγ',
    'fix_push_cycle': 'λπ',
    'flow_engine_context': 'λε',
    'gemini_chat_seq001_v001_dead': 'λχ',
    'implement_all_18': 'λ18',
    'multi_line_import': 'λμ',
    'per_prompt_deleted': 'λδ',
    'readme_update_7': 'λ7u',
    'trigger_pigeon_rename': 'λτ',
    'verify_pigeon_plugin': 'λν',
}


def _get_git_log(root: Path, n: int = 20) -> list[dict]:
    """Get recent git commits as change history."""
    try:
        result = subprocess.run(
            ['git', 'log', f'-{n}', '--format=%H|%ai|%s'],
            capture_output=True, text=True, cwd=str(root),
            timeout=10
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0][:8],
                    'date': parts[1][:10],
                    'msg': parts[2][:80]
                })
        return commits
    except Exception:
        return []


def _assign_module_glyphs(
    top_modules: list[str],
) -> dict[str, str]:
    """Assign Greek glyphs to top-level modules.

    Uses mnemonics where possible, sequential assignment otherwise.
    """
    assigned: dict[str, str] = {}
    used_glyphs: set[str] = set()

    # First pass: mnemonic assignments
    for mod in top_modules:
        if mod in _MNEMONIC_MAP:
            glyph = _MNEMONIC_MAP[mod]
            if glyph not in used_glyphs:
                assigned[mod] = glyph
                used_glyphs.add(glyph)

    # Second pass: sequential for unassigned
    pool_idx = 0
    for mod in top_modules:
        if mod in assigned:
            continue
        while pool_idx < len(_PRIMARY_POOL) and _PRIMARY_POOL[pool_idx] in used_glyphs:
            pool_idx += 1
        if pool_idx < len(_PRIMARY_POOL):
            assigned[mod] = _PRIMARY_POOL[pool_idx]
            used_glyphs.add(_PRIMARY_POOL[pool_idx])
            pool_idx += 1
        else:
            # Fallback: use first 2 chars uppercase
            assigned[mod] = mod[:2].upper()

    return assigned


def _assign_intent_glyphs(intents: list[str]) -> dict[str, str]:
    """Assign lambda codes to intents."""
    assigned: dict[str, str] = {}
    used: set[str] = set()
    fallback_idx = 0

    for intent in intents:
        if intent in _INTENT_PREFIXES:
            code = _INTENT_PREFIXES[intent]
            assigned[intent] = code
            used.add(code)
        else:
            # Generate from first letter
            while True:
                code = f'λ{chr(97 + fallback_idx)}'
                if code not in used:
                    break
                fallback_idx += 1
            assigned[intent] = code
            used.add(code)
            fallback_idx += 1

    return assigned


def _extract_top_modules(files: list[dict]) -> list[str]:
    """Extract top-level (root) module names.

    A root module is a name that appears in the registry and is NOT
    a decomposed child (child names contain their parent's name as prefix).
    """
    all_names = sorted(set(f['name'] for f in files))
    # Identify children: names like "self_fix_seq013_scan_hardcoded"
    # whose prefix matches another module "self_fix"
    children = set()
    for name in all_names:
        for other in all_names:
            if other != name and name.startswith(other + '_seq'):
                children.add(name)
                break
    # Also identify streaming_layer_* pattern children
    for name in all_names:
        for other in all_names:
            if other != name and name.startswith(other + '_'):
                if other not in children:
                    children.add(name)
                    break
    roots = [n for n in all_names if n not in children]
    return sorted(roots)


def _build_module_entries(
    files: list[dict],
    module_glyphs: dict[str, str],
    intent_glyphs: dict[str, str],
) -> dict:
    """Build per-module dictionary entries."""
    modules = {}
    # Sort module names longest-first for greedy prefix matching
    sorted_mods = sorted(module_glyphs.keys(), key=len, reverse=True)

    for f in files:
        name = f['name']

        # Find the longest module name that is a prefix of this file's name
        matched_module = None
        matched_glyph = None
        for mod in sorted_mods:
            if name == mod or name.startswith(mod + '_'):
                matched_module = mod
                matched_glyph = module_glyphs[mod]
                break

        # Exact match fallback
        if not matched_module and name in module_glyphs:
            matched_module = name
            matched_glyph = module_glyphs[name]

        # Last resort: assign to '?' group
        if not matched_module:
            matched_module = name
            matched_glyph = module_glyphs.get(name, '?')

        glyph_key = matched_glyph
        if glyph_key not in modules:
            modules[glyph_key] = {
                'name': matched_module,
                'folder': str(Path(f['path']).parent).replace('\\', '/'),
                'files': [],
            }

        intent_code = intent_glyphs.get(f.get('intent', ''), '')
        history = []
        for h in f.get('history', []):
            history.append({
                'v': h.get('ver', '?'),
                'd': h.get('date', '?'),
                'action': h.get('action', '?'),
            })

        modules[glyph_key]['files'].append({
            'name': name,
            'seq': f.get('seq', 0),
            'ver': f.get('ver', 1),
            'date': f.get('date', ''),
            'desc': f.get('desc', '').replace('_', ' '),
            'intent': intent_code,
            'tokens': f.get('tokens', 0),
            'path': f['path'].replace('\\', '/'),
            'history': history,
        })

    return modules


def generate_dictionary(root: Path) -> dict:
    """Generate the full .pgd dictionary from registry + git."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return {'error': 'pigeon_registry.json not found'}

    reg = json.loads(reg_path.read_text('utf-8'))
    files = reg.get('files', [])

    # Extract top-level modules from registry names (not folders)
    top_modules = _extract_top_modules(files)
    intents = sorted(set(
        f.get('intent', '') for f in files if f.get('intent')
    ))

    # Assign glyphs
    module_glyphs = _assign_module_glyphs(top_modules)
    intent_glyphs = _assign_intent_glyphs(intents)

    # Build module entries
    module_entries = _build_module_entries(files, module_glyphs, intent_glyphs)

    # Get git history
    git_log = _get_git_log(root)

    # Score module confidence
    confidence = {}
    copilot_meta = {}
    if score_module_confidence is not None:
        confidence = score_module_confidence(root)
        copilot_meta = compute_copilot_meta_state(confidence)

    # Build the dictionary
    now = datetime.now(timezone.utc).isoformat()
    dictionary = {
        'version': '0.1.0',
        'generated': now,
        'stats': {
            'total_files': len(files),
            'modules': len(module_entries),
            'intents': len(intent_glyphs),
            'total_glyphs': len(module_glyphs) + len(intent_glyphs),
        },
        'module_glyphs': {
            g: m for m, g in sorted(
                module_glyphs.items(), key=lambda x: x[1]
            )
        },
        'intent_glyphs': {
            g: i for i, g in sorted(
                intent_glyphs.items(), key=lambda x: x[1]
            )
        },
        'modules': module_entries,
        'recent_changes': git_log[:10],
        'meta_glyphs': {
            '·': 'field separator',
            'v': 'version prefix',
            'd': 'date prefix (MMDD)',
            '†': 'auto-extracted by pigeon compiler',
            '‡': 'manually created',
            '→': 'return / produces',
            '←': 'imports from / depends on',
            '✓': 'confident (low rework, no issues)',
            '~': 'uncertain (some rework or heat)',
            '!': 'degraded (known issues)',
            '?': 'blind (no data)',
        },
        'confidence': confidence,
        'copilot_meta': copilot_meta,
    }

    return dictionary


def generate_compact_injection(dictionary: dict) -> str:
    """Generate a tight injection block for copilot context.

    Target: ~300-500 tokens. Dense lookup table + change summary.
    """
    lines = []
    stats = dictionary['stats']
    lines.append(
        f'[PIGEON DICT v0.2.0 | {stats["total_files"]} files '
        f'| {stats["modules"]} modules | {stats["total_glyphs"]} glyphs]'
    )

    # Copilot meta-state line
    meta = dictionary.get('copilot_meta', {})
    if meta and format_confidence_line is not None:
        lines.append(format_confidence_line(meta))

    # Module glyph table — one line per glyph, dense
    mg = dictionary.get('module_glyphs', {})
    confidence = dictionary.get('confidence', {})
    # Group into rows of 4 for density, append state symbol
    items = []
    for g, n in mg.items():
        state = confidence.get(n, '')
        items.append(f'{g}={n}{state}' if state else f'{g}={n}')
    for i in range(0, len(items), 4):
        lines.append(' | '.join(items[i:i+4]))

    # Intent glyph table — one dense line
    ig = dictionary.get('intent_glyphs', {})
    int_items = [f'{g}={n}' for g, n in ig.items()]
    lines.append('')
    lines.append('Intents: ' + ', '.join(int_items))

    # Change history — top 10 most-churned modules only
    lines.append('')
    lines.append('Hot:')
    churn_ranked = []
    for glyph, data in dictionary.get('modules', {}).items():
        changed = [
            f for f in data.get('files', [])
            if len(f.get('history', [])) > 1
        ]
        if not changed:
            continue
        total_tok = sum(f.get('tokens', 0) for f in data.get('files', []))
        max_v = max(f.get('ver', 0) for f in data.get('files', []))
        total_hist = sum(len(f.get('history', [])) for f in changed)
        chains = []
        for cf in changed[:2]:
            hist = cf.get('history', [])
            chain = '→'.join(f'v{h["v"]}' for h in hist[-3:])
            chains.append(chain)
        churn_ranked.append((
            total_hist, glyph, data['name'], max_v, total_tok, chains
        ))
    churn_ranked.sort(reverse=True)
    for _, glyph, name, max_v, tok, chains in churn_ranked[:10]:
        state = confidence.get(name, '')
        lines.append(
            f'{glyph}{state} {name} v{max_v} {tok}tok [{" ".join(chains)}]'
        )

    # Recent git commits — just 3
    lines.append('')
    for c in dictionary.get('recent_changes', [])[:3]:
        lines.append(f'{c["hash"]} {c["msg"][:50]}')

    lines.append('[/DICT]')
    return '\n'.join(lines)


DICT_BLOCK_START = '<!-- pigeon:dictionary -->'
DICT_BLOCK_END = '<!-- /pigeon:dictionary -->'
COPILOT_PATH = '.github/copilot-instructions.md'


def inject_dictionary_block(root: Path) -> bool:
    """Regenerate dictionary.pgd and inject minimal stub into copilot-instructions.

    Full glyph mappings are now inline in the auto-index block.
    Dictionary block is kept as a stub for block-marker compatibility.
    """
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False

    dictionary = generate_dictionary(root)

    # Minimal stub — all glyph info is now in auto-index
    block = f'{DICT_BLOCK_START}\n<!-- glyph mappings merged into auto-index -->\n{DICT_BLOCK_END}'

    text = cp_path.read_text(encoding='utf-8')

    import re
    pattern = re.compile(
        rf'(?ms)^\s*{re.escape(DICT_BLOCK_START)}\s*$\n.*?^\s*{re.escape(DICT_BLOCK_END)}\s*$',
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    else:
        anchor = '<!-- pigeon:auto-index -->'
        if anchor in text:
            idx = text.index(anchor)
            new_text = text[:idx] + block + '\n' + text[idx:]
        else:
            new_text = text.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')

    # Still write data files for other consumers
    (root / 'dictionary.pgd').write_text(
        json.dumps(dictionary, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    compact = generate_compact_injection(dictionary)
    (root / 'dictionary_compact.txt').write_text(compact, encoding='utf-8')
    return True


def write_dictionary(root: Path) -> Path:
    """Generate and write dictionary.pgd to the project root."""
    dictionary = generate_dictionary(root)
    out_path = root / 'dictionary.pgd'
    out_path.write_text(
        json.dumps(dictionary, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    # Also write the compact injection version
    compact = generate_compact_injection(dictionary)
    compact_path = root / 'dictionary_compact.txt'
    compact_path.write_text(compact, encoding='utf-8')

    return out_path


if __name__ == '__main__':
    root = Path('.')
    pgd = write_dictionary(root)
    # Print compact version to stdout
    dictionary = json.loads(pgd.read_text('utf-8'))
    print(generate_compact_injection(dictionary))
