"""compliance_seq008_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import re

SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git',
             '_llm_tests_put_all_test_and_debug_scripts_here',
             '.next', '.pytest_cache', 'compiler_output',
             'rollback_logs', 'audit_backups', 'json_uploads',
             'logs', '.vscode', 'cache'}


MAX_LINES = 200

WARN_LINES = 300

CRIT_LINES = 500
