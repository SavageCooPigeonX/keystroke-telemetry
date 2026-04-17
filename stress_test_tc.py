"""Stress test — thought completer pipeline.

Simulates buffers → context agent → section classifier → grader → adaptive params.
No Gemini calls. Tests that the right files get selected for specific intents
and that section/grading/tuning respond correctly.
"""
import json
import importlib.util
from pathlib import Path
import sys
import time
import types

sys.path.insert(0, '.')

# Pre-register src as a package to avoid triggering src/__init__.py
_src_dir = str(Path('src').resolve())
if 'src' not in sys.modules:
    _pkg = types.ModuleType('src')
    _pkg.__path__ = [_src_dir]
    _pkg.__package__ = 'src'
    sys.modules['src'] = _pkg

# Now import tc_ modules — they use relative imports within src
from src.tc_context_agent import select_context_files, build_code_context, _extract_mentions
from src.tc_profile import (classify_section, update_section, update_profile_from_completion,
                            load_profile, save_profile, _deduce_intelligence,
                            format_intelligence_for_prompt)
from src.tc_grader import (grade_completion, log_grade, update_grade_summary,
                           format_grades_for_prompt, compute_adaptive_params)
from src.tc_context import load_context

ROOT = Path('.')
PASS = 0
FAIL = 0
TOTAL = 0

def header(name):
    print(f'\n{"="*60}')
    print(f'  {name}')
    print(f'{"="*60}')

def check(test_name, condition, detail=''):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        print(f'  \u2713 {test_name}')
    else:
        FAIL += 1
        print(f'  \u2717 {test_name} — {detail}')

# ═══════════════════════════════════════════════════════════
# TEST 1: Context agent — buffer mentions → file selection
# ═══════════════════════════════════════════════════════════
header('TEST 1: Context Select — module targeting')

test_cases = [
    # (buffer, expected_module_substring, description)
    ('the thought_completer is not picking up context properly',
     'thought_completer', 'direct underscore name mention'),
    ('maybe the drift_watcher needs a reset since entropy keeps climbing',
     'drift', 'drift_watcher via segment match'),
    ('import rewriter is still breaking on pigeon renames',
     'import_rewriter', 'import_rewriter from split words'),
    ('push narrative needs a timeout fix - its hanging',
     'push_narrative', 'push_narrative from underscore name'),
    ('def self_fix_scan(root):\n    bugs = []',
     'self_fix', 'code buffer matching self_fix'),
    ('the streaming layer aggregator is eating memory',
     'streaming_layer', 'streaming_layer from multi-word'),
    ('context_budget is hitting the token limit again',
     'context_budget', 'context_budget direct match'),
    ('prediction_scorer calibration is off by 30%',
     'prediction_scorer', 'prediction_scorer from underscore'),
]

ctx = load_context()
for buffer, expected, desc in test_cases:
    selected = select_context_files(buffer, ctx)
    names = [f['name'] for f in selected]
    scores = {f['name']: f['score'] for f in selected}
    found = any(expected in n for n in names)
    detail = f'got {names} scores={scores}' if not found else ''
    check(f'{desc}: "{expected}" in results', found, detail)

# also test mention extraction
mentions = _extract_mentions('the thought_completer context_agent pipeline is broken')
check('mention extraction: underscore names first',
      'thought_completer' in mentions and 'context_agent' in mentions,
      f'got {mentions}')


# ═══════════════════════════════════════════════════════════
# TEST 2: Section classifier — intent routing
# ═══════════════════════════════════════════════════════════
header('TEST 2: Section Classifier')

section_tests = [
    ('fix the bug in git_plugin its crashing on commit', 'debugging',
     'bug + crash = debugging'),
    ('push the new manifest and run compliance', 'infrastructure',
     'push + manifest + compliance = infrastructure'),
    ('what does the entropy signal look like for this module', 'telemetry',
     'entropy + signal = telemetry'),
    ('how does the context agent work - show me the architecture', 'exploring',
     'how + show + architecture = exploring'),
    ('create a new module for operator probing', 'creating',
     'create + new + module = creating'),
    ('review the diff from last commit and check test coverage', 'reviewing',
     'review + diff + test = reviewing'),
]

for buffer, expected, desc in section_tests:
    section = classify_section(buffer)
    check(f'{desc} → {expected}', section == expected,
          f'got "{section}"')


# ═══════════════════════════════════════════════════════════
# TEST 3: Grader — scoring axes
# ═══════════════════════════════════════════════════════════
header('TEST 3: Grader — scoring axes')

# High relevance: buffer and completion share vocabulary
g1 = grade_completion(
    'the drift_watcher entropy signal is climbing',
    'faster than expected. the last 3 pushes each added 0.05 to global entropy',
    'accepted', context_files=['drift_watcher'], latency_ms=800)
check(f'accepted completion: composite > 0.5', g1['composite'] > 0.5,
      f'composite={g1["composite"]:.3f}')
check(f'accepted: outcome_score = 0.8', g1['outcome_score'] == 0.8)

# Low relevance: buffer about drift, completion about something else
g2 = grade_completion(
    'the drift_watcher entropy signal is climbing',
    'maybe we should refactor the entire streaming layer to use async',
    'dismissed', context_files=['streaming_layer'], latency_ms=1200)
check(f'dismissed off-topic: composite < 0.4', g2['composite'] < 0.4,
      f'composite={g2["composite"]:.3f}')
check(f'dismissed off-topic: relevance < 0.15', g2['relevance'] < 0.15,
      f'relevance={g2["relevance"]:.3f}')

# Echo test: completion just restates buffer
g3 = grade_completion(
    'the context agent picks the wrong files',
    'the context agent picks the wrong files every single time',
    'dismissed')
check(f'echo completion: echo > 0.5', g3['echo'] > 0.5,
      f'echo={g3["echo"]:.3f}')

# Code completion
g4 = grade_completion(
    'def process_buffer(self, buf):\n    ',
    'words = buf.strip().split()\n    return [w for w in words if len(w) > 3]',
    'accepted', latency_ms=600)
check(f'code completion: is_code=True', g4['is_code'] == True)
check(f'code accepted: composite > 0.5', g4['composite'] > 0.5,
      f'composite={g4["composite"]:.3f}')

# Short garbage
g5 = grade_completion('hi', 'the', 'ignored')
check(f'short buffer: low composite', g5['composite'] < 0.3,
      f'composite={g5["composite"]:.3f}')


# ═══════════════════════════════════════════════════════════
# TEST 4: Adaptive params — tuning from grade history
# ═══════════════════════════════════════════════════════════
header('TEST 4: Adaptive Parameters')

params = compute_adaptive_params()
check(f'temperature is float', isinstance(params['temperature'], float),
      f'got {type(params["temperature"])}')
check(f'maxOutputTokens is int', isinstance(params['maxOutputTokens'], int),
      f'got {type(params["maxOutputTokens"])}')
check(f'topP is float', isinstance(params['topP'], float),
      f'got {type(params["topP"])}')
check(f'temperature in range [0.3, 0.95]',
      0.3 <= params['temperature'] <= 0.95,
      f'got {params["temperature"]}')
check(f'maxOutputTokens in range [80, 600]',
      80 <= params['maxOutputTokens'] <= 600,
      f'got {params["maxOutputTokens"]}')
check(f'topP in range [0.7, 0.95]',
      0.7 <= params['topP'] <= 0.95,
      f'got {params["topP"]}')
print(f'\n  Current adaptive params: {params}')


# ═══════════════════════════════════════════════════════════
# TEST 5: Section profiling → intelligence deduction
# ═══════════════════════════════════════════════════════════
header('TEST 5: Section profiling + intelligence')

profile = load_profile()
# Simulate 25 completions across sections to trigger intelligence deductions
sim_data = [
    # (buffer, completion, outcome, section_hint)
    ('fix the crash in git_plugin', 'by adding a null check on line 47', 'accepted'),
    ('why is the import breaking', 'because pigeon renamed the module last push', 'dismissed'),
    ('the bug in self_fix keeps coming back', 'we need to refactor the scanner loop', 'ignored'),
    ('push the manifest and run compliance', 'then check the organism health', 'accepted'),
    ('build the new context selector', 'using weighted scoring from module registry', 'accepted'),
    ('what does this entropy number mean', 'its the uncertainty from copilot edits', 'dismissed'),
    ('how is the completion grading working', 'it scores on 6 axes weighted by outcome', 'accepted'),
    ('the streaming_layer dashboard is slow', 'because the aggregator recomputes every tick', 'ignored'),
    ('create a new pigeon module for probes', 'with a seq number and lambda suffix', 'accepted'),
    ('review the last diff for regressions', 'the rename engine changed 3 import paths', 'dismissed'),
    ('fix the error in prediction_scorer', 'the calibration constant was wrong', 'accepted'),
    ('fix the timeout in push_narrative', 'by catching the subprocess.TimeoutExpired', 'accepted'),
    ('why does context_budget keep overflowing', 'its counting tokens wrong in the prefix', 'dismissed'),
    ('fix the null reference in flow_engine', 'need to check node_memory before access', 'ignored'),
    ('build a replay debugger for the sim', 'that reads os_keystrokes and replays them', 'accepted'),
    ('whats wrong with the thought completer', 'the relevance scores are near zero for most buffers', 'accepted'),
    ('the import rewriter fails on class decomp', 'because class methods have different import rules', 'dismissed'),
    ('push cycle predictions are stale', 'the moon cycle calculator hasnt run since march', 'ignored'),
    ('fix operator_stats classifier degenerating', 'the wpm bins are too coarse, need finer granularity', 'accepted'),
    ('create an escalation engine for bugs', 'that auto-files issues when bugs persist 3+ pushes', 'accepted'),
    ('fix crash when pigeon renames midway', 'the registry lock wasnt released on exception', 'accepted'),
    ('why does the profile show wrong state', 'the exponential moving average is over-smoothing', 'dismissed'),
    ('review push_narrative output for accuracy', 'it hallucinated 2 module names in the delta', 'accepted'),
    ('show me the module coupling graph', 'there are 3 slumber pairs above 0.8 coupling', 'ignored'),
    ('fix the dead export in rework_detector', 'remove format_rework_for_prompt from __all__', 'accepted'),
]

print(f'  Simulating {len(sim_data)} completions across sections...')
for buf, comp, outcome in sim_data:
    update_profile_from_completion(buf, comp, outcome)

# Check section accumulation
profile = load_profile()
sections = profile.get('shards', {}).get('sections', {})
section_names = list(sections.keys())
section_counts = {n: s.get('total_completions', 0) for n, s in sections.items() if isinstance(s, dict)}
print(f'  Sections populated: {section_names}')
print(f'  Section counts: {section_counts}')

check('multiple sections populated', len(sections) >= 3,
      f'got {len(sections)}: {section_names}')
check('debugging section exists', 'debugging' in sections)
check('infrastructure section exists', 'infrastructure' in sections)
check('exploring section exists', 'exploring' in sections)

# Check intelligence deduction triggered
intel = profile.get('shards', {}).get('intelligence', {})
secrets = intel.get('secrets', [])
secret_types = [s.get('type', '?') for s in secrets]
print(f'  Secrets discovered: {len(secrets)} — types: {secret_types}')
check('secrets discovered > 0', len(secrets) > 0,
      f'got {len(secrets)}')

# Format for prompt
intel_block = format_intelligence_for_prompt(profile)
check('intelligence formats for prompt', len(intel_block) > 50,
      f'got {len(intel_block)} chars')
if intel_block:
    print(f'\n  --- Intelligence Block (first 500 chars) ---')
    print(f'  {intel_block[:500]}')


# ═══════════════════════════════════════════════════════════
# TEST 6: Section-aware context boost
# ═══════════════════════════════════════════════════════════
header('TEST 6: Section-aware context select')

# After sim, the debugging section should have hot_modules.
# When typing a debugging-flavored buffer, modules from that section's
# hot list should get a score boost.
debug_sections = sections.get('debugging', {})
debug_hot = debug_sections.get('hot_modules', {}) if isinstance(debug_sections, dict) else {}
print(f'  Debugging hot_modules: {dict(list(debug_hot.items())[:5])}')

# Type a debugging buffer — modules that got hot in debugging sim should boost
debug_buffer = 'fix the error thats breaking everything'
debug_selected = select_context_files(debug_buffer, ctx)
debug_names = [f['name'] for f in debug_selected]
debug_scores = {f['name']: round(f['score'], 2) for f in debug_selected}
print(f'  Debug buffer selected: {debug_names}')
print(f'  Scores: {debug_scores}')
check('debug buffer selects files', len(debug_selected) > 0,
      f'got {len(debug_selected)}')

# Type an infrastructure buffer
infra_buffer = 'push the manifest and run the compliance checker'
infra_selected = select_context_files(infra_buffer, ctx)
infra_names = [f['name'] for f in infra_selected]
print(f'  Infra buffer selected: {infra_names}')
check('infra buffer selects files', len(infra_selected) > 0,
      f'got {len(infra_selected)}')

# Verify different sections select different files
if debug_selected and infra_selected:
    overlap = set(debug_names) & set(infra_names)
    check('different sections → different files',
          len(overlap) < len(debug_names),
          f'overlap={overlap}')


# ═══════════════════════════════════════════════════════════
# TEST 7: Memory shard routing
# ═══════════════════════════════════════════════════════════
header('TEST 7: Shard routing')

try:
    from src._resolve import src_import
    route_context, format_shard_context = src_import(
        "context_router_seq027", "route_context", "format_shard_context")

    shard_tests = [
        ('fix import breaking after rename', 'module relationships or pain points'),
        ('what typing patterns has the operator shown', 'prompt patterns or architecture'),
        ('the thought completer predictions are off', 'predictions or module pain'),
    ]
    for query, expected_area in shard_tests:
        routed = route_context(ROOT, query, top_n=3)
        shard_names = [r['name'] for r in routed]
        shard_text = format_shard_context(routed, ROOT)
        print(f'  "{query[:40]}..." → shards: {shard_names}')
        check(f'shard routing returns results for "{query[:30]}"',
              len(routed) > 0, f'got {len(routed)} shards')
except Exception as e:
    print(f'  shard routing unavailable: {e}')


# ═══════════════════════════════════════════════════════════
# TEST 8: Full pipeline — build_user_prompt smoke test
# ═══════════════════════════════════════════════════════════
header('TEST 8: Full prompt pipeline (no API call)')

from src.tc_gemini import _build_user_prompt, ThoughtBuffer, _strip_signal_echo

tb = ThoughtBuffer()
# Simulate a few thought buffer entries
tb.record('the import rewriter broke', 'again because of pigeon renames', 'dismissed')
tb.record('maybe fix the registry', 'locking mechanism to prevent race conditions', 'accepted')
tb.record('entropy on self_fix is', 'climbing since the last 3 pushes', 'ignored')

ctx = load_context()
prompt = _build_user_prompt('the drift_watcher needs attention', ctx, tb)
print(f'  Prompt length: {len(prompt)} chars')
check('prompt includes BUFFER', 'drift_watcher' in prompt)
check('prompt includes MODE', 'MODE:' in prompt)
check('prompt includes THOUGHT MEMORY', 'THOUGHT MEMORY' in prompt)
check('prompt includes BANNED PHRASES or signals',
      'BANNED' in prompt or 'SIGNALS' in prompt)

# Check section injection
if 'SECTION:' in prompt:
    check('prompt includes SECTION block', True)
    # Extract section line
    for line in prompt.split('\n'):
        if 'SECTION:' in line:
            print(f'  Section line: {line[:100]}')
            break
else:
    check('prompt includes SECTION block', False, 'no SECTION: found')

# Anti-echo
echoed = 'the entropy map shows high uncertainty in the codebase modules'
cleaned = _strip_signal_echo(echoed, 'what should i work on')
check('anti-echo strips signal terms from completion',
      'entropy map' not in cleaned or len(cleaned) < len(echoed),
      f'cleaned={cleaned[:80]}')

# Non-stripped when buffer mentions term
not_stripped = _strip_signal_echo('the entropy map is concerning', 'check the entropy map values')
check('anti-echo preserves when buffer mentions term',
      'entropy map' in not_stripped)


# ═══════════════════════════════════════════════════════════
# TEST 9: Grade summary self-learning format
# ═══════════════════════════════════════════════════════════
header('TEST 9: Self-learning prompt injection')

grades_block = format_grades_for_prompt()
if grades_block:
    check('grades block non-empty', len(grades_block) > 50)
    check('grades block has COMPLETION GRADES header', 'COMPLETION GRADES' in grades_block)
    check('grades block has PERFORMANCE', 'PERFORMANCE' in grades_block or 'composite' in grades_block)
    check('grades block has IMPROVE directive', 'IMPROVE' in grades_block)
    print(f'\n  --- Grades Block (first 400 chars) ---')
    print(f'  {grades_block[:400]}')
else:
    check('grades block exists', False, 'empty grades block')


# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print(f'\n{"="*60}')
print(f'  RESULTS: {PASS}/{TOTAL} passed, {FAIL} failed')
print(f'{"="*60}')

# Print adaptive params for visibility
params = compute_adaptive_params()
print(f'\n  Adaptive params: temp={params["temperature"]} '
      f'maxTok={params["maxOutputTokens"]} topP={params["topP"]}')

# Print current profile stats
profile = load_profile()
print(f'  Profile samples: {profile.get("samples", 0)}')
sections = profile.get('shards', {}).get('sections', {})
for name, sec in sections.items():
    if isinstance(sec, dict) and sec.get('total_completions', 0) > 0:
        print(f'    {name}: {sec["total_completions"]} completions, '
              f'accept={sec.get("accepted",0)}, '
              f'state={sec.get("dominant_state","?")}')

intel = profile.get('shards', {}).get('intelligence', {})
print(f'  Secrets: {intel.get("secret_count", 0)}')
model = intel.get('operator_model', {})
if model:
    print(f'  Model: {model}')

if FAIL > 0:
    sys.exit(1)
