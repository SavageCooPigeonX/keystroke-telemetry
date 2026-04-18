"""警p_sa_s030_v003_d0402_缩分话_λV_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import re

COPILOT_PATH = '.github/copilot-instructions.md'

ALERT_START = '<!-- pigeon:staleness-alert -->'

ALERT_END   = '<!-- /pigeon:staleness-alert -->'


PER_PROMPT_BLOCKS = {
    'current-query': {
        'block_start': '<!-- pigeon:current-query -->',
        'block_end':   '<!-- /pigeon:current-query -->',
        'pattern': r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC',
        'fmt': '%Y-%m-%d %H:%M',
        'max_age_min': 10,
        'writer': 'prompt_enricher (Gemini Flash)',
    },
    'prompt-telemetry': {
        'block_start': '<!-- pigeon:prompt-telemetry -->',
        'block_end':   '<!-- /pigeon:prompt-telemetry -->',
        'pattern': r'"updated_at":\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
        'fmt': '%Y-%m-%dT%H:%M:%S',
        'max_age_min': 10,
        'writer': 'prompt_journal._refresh_copilot_instructions',
    },
    'task-context': {
        'block_start': '<!-- pigeon:task-context -->',
        'block_end':   '<!-- /pigeon:task-context -->',
        'pattern': r'Auto-injected (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC',
        'fmt': '%Y-%m-%d %H:%M',
        'max_age_min': 120,  # refreshed by classify_bridge, looser threshold
        'writer': 'dynamic_prompt.inject_task_context (via classify_bridge)',
    },
}
