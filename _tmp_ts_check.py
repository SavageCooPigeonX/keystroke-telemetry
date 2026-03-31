import re
t = open('.github/copilot-instructions.md', 'r', encoding='utf-8').read()
checks = [
    (r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'current-query'),
    (r'Auto-injected (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'task-context'),
    (r'Auto-updated (\d{4}-\d{2}-\d{2}) ', 'operator-state'),
    (r'"updated_at":\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', 'prompt-telemetry'),
    (r'Auto-extracted (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'voice-style'),
    (r'Auto-generated (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'predictions'),
]
for pat, name in checks:
    m = re.search(pat, t)
    if m:
        print(f"{name:25s} -> {m.group(1)}")
    else:
        print(f"{name:25s} -> NOT FOUND")
