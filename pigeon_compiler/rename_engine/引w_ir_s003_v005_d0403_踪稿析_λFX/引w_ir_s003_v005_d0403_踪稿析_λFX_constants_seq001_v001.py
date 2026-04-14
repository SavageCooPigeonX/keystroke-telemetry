"""引w_ir_s003_v005_d0403_踪稿析_λFX_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 31 lines | ~388 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git',
             '_llm_tests_put_all_test_and_debug_scripts_here',
             '.next', '.pytest_cache'}


KNOWN_EXTERNAL = {
    # stdlib
    'os', 'sys', 're', 'json', 'pathlib', 'datetime', 'collections',
    'functools', 'itertools', 'logging', 'hashlib', 'uuid', 'time',
    'typing', 'abc', 'ast', 'io', 'math', 'random', 'string',
    'threading', 'traceback', 'urllib', 'base64', 'copy', 'csv',
    'difflib', 'enum', 'glob', 'html', 'http', 'importlib', 'inspect',
    'operator', 'pickle', 'pprint', 'secrets', 'shutil', 'signal',
    'socket', 'sqlite3', 'struct', 'subprocess', 'tempfile', 'textwrap',
    'unittest', 'warnings', 'xml', 'zipfile', 'contextlib', 'dataclasses',
    'decimal', 'email', 'heapq', 'queue', 'types', 'weakref',
    'concurrent', 'multiprocessing', 'asyncio', 'ctypes', 'array',
    # requirements.txt deps + transitive
    'flask', 'flask_login', 'flask_wtf', 'flask_limiter',
    'werkzeug', 'dotenv', 'gunicorn', 'email_validator',
    'supabase', 'httpx', 'stripe', 'tzdata', 'markdown',
    'wtforms', 'jinja2', 'click', 'itsdangerous', 'markupsafe',
    'certifi', 'charset_normalizer', 'idna', 'urllib3',
    'requests', 'pydantic', 'openai', 'anthropic',
    'postgrest', 'gotrue', 'storage3', 'realtime', 'supafunc',
    'h11', 'sniffio', 'anyio', 'httpcore', 'setuptools', 'pip',
    'pkg_resources', 'distutils', 'pytest', 'coverage',
}
