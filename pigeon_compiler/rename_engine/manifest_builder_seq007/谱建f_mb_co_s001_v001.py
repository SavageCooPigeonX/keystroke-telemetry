"""manifest_builder_seq007_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED, is_excluded
import json
import re

SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git',
             '_llm_tests_put_all_test_and_debug_scripts_here',
             '.next', '.pytest_cache', 'compiler_output', 'rollback_logs',
             'audit_backups', 'json_uploads', 'logs', '.vscode', 'cache'}


SKIP_FILES = {'__init__.py', 'conftest.py'}


MAX_COMPLIANT = PIGEON_MAX


_LEGEND = (
    '## How to read this manifest\n'
    '\n'
    'This file is **auto-generated** by `manifest_builder` and describes every\n'
    'Python module in this folder. It is the single source of truth for:\n'
    '- What each file does (Description)\n'
    '- What each file exports (Exports) and depends on (Deps)\n'
    '- Whether the file meets the Pigeon size budget (Status)\n'
    '- Living operator notes that persist across rebuilds (Notes)\n'
    '\n'
    '**Status icons:** '
    '✅ ≤{max} lines | '
    '⚠️ OVER {max}–300 | '
    '🟠 WARN 300–500 | '
    '🔴 CRIT >500\n'
    '\n'
    '**Columns:** '
    'Seq = load order · Lines = source line count · '
    'Exports = public classes/functions · Deps = intra-project imports\n'
)


_MARKER_RE = re.compile(r'#\s*(TODO|FIXME|HACK|XXX|WARN|NOTE)\b', re.IGNORECASE)


LOG_DIRS = ('test_logs', 'demo_logs', 'stress_logs')

PAUSE_THRESHOLD_MS = 2000

BACKSPACE_BURST_MIN = 3

TRAIL_LIMIT = 50
